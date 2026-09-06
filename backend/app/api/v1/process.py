"""
Process API endpoint — Real LangGraph pipeline with full persistence.

Accepts a resume file upload, creates/fetches a demo student,
starts the workflow run, invokes the full LangGraph pipeline,
persists the result snapshot to PostgreSQL, writes audit logs,
and returns a run_id for the frontend to poll.

The result enters PENDING_REVIEW status and requires officer approval
before becoming visible on the student dashboard.
"""
import os
import uuid
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, Student
from app.models.workflow import WorkflowRun, AuditLog
from app.agents.graph import agent_runner
from app.services.audit import log_workflow_events

router = APIRouter(prefix="/process", tags=["Process"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    run_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    run_id: str
    status: str
    current_step: Optional[str] = None
    student_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers (MVP Auth Bypass)
# 
# SECURITY WARNING: These helpers generate mock users to bypass authentication
# for the MVP demo. 
# FUTURE REQUIREMENT: Remove these in Phase 3 and use `get_current_student`
# and `get_current_user` dependencies from `deps.py`.
# ---------------------------------------------------------------------------

async def get_or_create_demo_student(db: AsyncSession) -> Student:
    """Fetch or create a demo student for the MVP upload flow."""
    demo_email = "student@demo.com"
    result = await db.execute(select(User).where(User.email == demo_email))
    user = result.scalar_one_or_none()

    if not user:
        from app.services.auth import create_user
        user = await create_user(
            db=db,
            email=demo_email,
            password="password123",
            full_name="Demo Student",
            role="student",
        )

    result = await db.execute(select(Student).where(Student.user_id == user.id))
    student = result.scalar_one_or_none()

    if not student:
        student = Student(user_id=user.id)
        db.add(student)
        await db.flush()

    return student


async def get_or_create_demo_officer(db: AsyncSession) -> User:
    """Fetch or create a demo placement officer for the MVP flow."""
    officer_email = "officer@demo.com"
    result = await db.execute(select(User).where(User.email == officer_email))
    user = result.scalar_one_or_none()

    if not user:
        from app.services.auth import create_user
        user = await create_user(
            db=db,
            email=officer_email,
            password="password123",
            full_name="Demo Officer",
            role="placement_officer",
        )

    return user


# ---------------------------------------------------------------------------
# Upload + Pipeline Execution
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse, summary="Upload resume and start real LangGraph pipeline")
async def process_resume(
    file: UploadFile = File(...),
    github_username: Optional[str] = Form(None),
    leetcode_handle: Optional[str] = Form(None),
    coding_solved: int = Form(0),
    cgpa: Optional[float] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts a resume file, invokes the full LangGraph pipeline,
    persists the result to PostgreSQL, and returns a run_id.

    The result enters PENDING_REVIEW status. The officer must approve
    before the student can see the final dashboard.
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files accepted.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 5 MB limit.")

    # Save to temp file for Resume Agent to read
    suffix = ".pdf" if "pdf" in file.content_type else ".docx"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    try:
        tmp.write(contents)
        tmp.flush()
        tmp.close()

        # 1. Get or Create Demo Student
        student = await get_or_create_demo_student(db)

        # 2. Create WorkflowRun in DB
        db_run = WorkflowRun(
            student_id=student.id,
            initiated_by=student.user_id,
            status="running",
            current_step="init",
            started_at=datetime.now(timezone.utc),
        )
        db.add(db_run)
        await db.commit()
        await db.refresh(db_run)

        # 3. Write initial audit log
        init_audit = AuditLog(
            actor_id=student.user_id,
            actor_type="student",
            workflow_run_id=db_run.id,
            action="RUN_CREATED",
            entity_type="workflow_run",
            entity_id=db_run.id,
            correlation_id=uuid.uuid4(),
            details={
                "github_username": github_username,
                "leetcode_handle": leetcode_handle,
                "coding_solved": coding_solved,
                "cgpa": cgpa,
                "file_name": file.filename,
            },
        )
        db.add(init_audit)
        await db.commit()

        # 4. Build state and invoke the full LangGraph pipeline
        initial_state: Dict[str, Any] = {
            "student_id": str(student.id),
            "run_id": str(db_run.id),
            "consent_validated": True,
            "resume_data": {
                "file_path": tmp.name,
                "mime_type": file.content_type,
            },
            "target_roles": ["software_engineer", "data_engineer"],
            "current_step": "init",
            "errors": [],
            "audit_events": [],
            "evidence_records": [],
            "retry_count": 0,
            "max_retries": 3,
            "budget_remaining": 100000,
            "validation_passed": False,
            "approval_status": "pending",
        }

        config = {"configurable": {"thread_id": str(db_run.id)}}

        try:
            final_state = agent_runner.invoke(initial_state, config=config)
        except Exception as e:
            db_run.status = "failed"
            db_run.error_message = str(e)
            db_run.completed_at = datetime.now(timezone.utc)
            await db.commit()

            # Audit the failure
            fail_audit = AuditLog(
                actor_type="system",
                workflow_run_id=db_run.id,
                action="PIPELINE_FAILED",
                entity_type="workflow_run",
                entity_id=db_run.id,
                correlation_id=uuid.uuid4(),
                details={"error": str(e)},
            )
            db.add(fail_audit)
            await db.commit()

            raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

        # 5. Build the result snapshot from final state
        result_snapshot = {
            "student_profile": final_state.get("student_profile", {}),
            "skill_gap_report": final_state.get("skill_gap_report", {}),
            "coding_analytics": final_state.get("coding_analytics", {}),
            "matching_result": final_state.get("matching_result", {}),
            "interview_result": final_state.get("interview_result", {}),
            "roadmap": final_state.get("roadmap", {}),
            "validation_report": final_state.get("validation_report", {}),
            "evidence_count": len(final_state.get("evidence_records", [])),
            "metadata": {
                "github_username": github_username,
                "leetcode_handle": leetcode_handle,
                "coding_solved": coding_solved,
                "cgpa": cgpa,
                "validation_passed": final_state.get("validation_passed", False),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        # 6. Persist to DB — status is PENDING_REVIEW (requires officer approval)
        db_run.status = "pending_review"
        db_run.current_step = final_state.get("current_step", "completed")
        db_run.result_snapshot = result_snapshot
        db_run.completed_at = datetime.now(timezone.utc)
        await db.commit()

        # 7. Write LangGraph audit events to the audit_logs table
        audit_events = final_state.get("audit_events", [])
        if audit_events:
            await log_workflow_events(
                db=db,
                workflow_run_id=str(db_run.id),
                events=audit_events,
                actor_id=str(student.user_id),
                actor_type="agent",
            )

        # 8. Write completion audit log
        completion_audit = AuditLog(
            actor_id=student.user_id,
            actor_type="system",
            workflow_run_id=db_run.id,
            action="SENT_FOR_REVIEW",
            entity_type="workflow_run",
            entity_id=db_run.id,
            correlation_id=uuid.uuid4(),
            details={
                "validation_passed": final_state.get("validation_passed", False),
                "errors_count": len(final_state.get("errors", [])),
            },
        )
        db.add(completion_audit)
        await db.commit()

        return UploadResponse(
            run_id=str(db_run.id),
            status="pending_review",
            message="Your profile has been analyzed and is awaiting Placement Officer review.",
        )

    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


# ---------------------------------------------------------------------------
# Status Polling
# ---------------------------------------------------------------------------

@router.get("/status/{run_id}", response_model=StatusResponse, summary="Poll workflow status")
async def get_workflow_status(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns the current status of a workflow run for frontend polling."""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id format.")

    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_uuid))
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found.")

    return StatusResponse(
        run_id=str(run.id),
        status=run.status,
        current_step=run.current_step,
        student_id=str(run.student_id) if run.student_id else None,
    )
