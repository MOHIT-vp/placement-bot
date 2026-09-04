"""
Lab 14 (Capstone): Dashboard API.

A single aggregated endpoint for the student frontend and an officer queue overview.
Reads only from approved, published Version snapshots — never raw agent state.
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_student, get_current_user, get_db, require_role
from app.models.user import Student, User
from app.models.workflow import Version, WorkflowRun, ApprovalDecision

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class WorkflowStatusSummary(BaseModel):
    run_id: Optional[str]
    status: Optional[str]
    current_step: Optional[str]
    version_number: Optional[int]
    published_at: Optional[str]


class StudentDashboard(BaseModel):
    student_id: str
    has_approved_plan: bool
    workflow_status: WorkflowStatusSummary
    student_profile: Optional[Dict[str, Any]]
    skill_gap_report: Optional[Dict[str, Any]]
    coding_analytics: Optional[Dict[str, Any]]
    matching_result: Optional[Dict[str, Any]]
    interview_result: Optional[Dict[str, Any]]
    roadmap: Optional[Dict[str, Any]]


class OfficerQueueSummary(BaseModel):
    pending_review_count: int
    recently_approved_count: int
    recently_rejected_count: int
    pending_runs: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Student Dashboard
# ---------------------------------------------------------------------------

@router.get("/me", response_model=StudentDashboard)
async def get_student_dashboard(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregated student dashboard: single call returns the full current state.

    - If an approved plan exists: returns data from the latest published Version snapshot.
    - If no plan yet: returns has_approved_plan=False with null data sections.
    - workflow_status always reflects the most recent WorkflowRun for context.
    """
    # --- Latest published version ---
    version_result = await db.execute(
        select(Version)
        .where(
            Version.student_id == current_student.id,
            Version.entity_type == "readiness_plan",
            Version.status == "published",
        )
        .order_by(Version.version_number.desc())
        .limit(1)
    )
    version = version_result.scalar_one_or_none()

    # --- Most recent workflow run (for status) ---
    run_result = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.student_id == current_student.id)
        .order_by(WorkflowRun.created_at.desc())
        .limit(1)
    )
    latest_run = run_result.scalar_one_or_none()

    workflow_status = WorkflowStatusSummary(
        run_id=str(latest_run.id) if latest_run else None,
        status=latest_run.status if latest_run else None,
        current_step=latest_run.current_step if latest_run else None,
        version_number=version.version_number if version else None,
        published_at=version.published_at.isoformat() if version and version.published_at else None,
    )

    if not version:
        return StudentDashboard(
            student_id=str(current_student.id),
            has_approved_plan=False,
            workflow_status=workflow_status,
            student_profile=None,
            skill_gap_report=None,
            coding_analytics=None,
            matching_result=None,
            interview_result=None,
            roadmap=None,
        )

    snap = version.snapshot
    return StudentDashboard(
        student_id=str(current_student.id),
        has_approved_plan=True,
        workflow_status=workflow_status,
        student_profile=snap.get("student_profile"),
        skill_gap_report=snap.get("skill_gap_report"),
        coding_analytics=snap.get("coding_analytics"),
        matching_result=snap.get("matching_result"),
        interview_result=snap.get("interview_result"),
        roadmap=snap.get("roadmap"),
    )


# ---------------------------------------------------------------------------
# Officer Queue Overview
# ---------------------------------------------------------------------------

@router.get("/officer/queue", response_model=OfficerQueueSummary)
async def get_officer_queue(
    current_user: User = Depends(require_role("placement_officer", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Officer dashboard: pending review queue and recent approval summary.
    """
    # Pending: completed but not yet decided
    pending_result = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.status == "completed")
        .order_by(WorkflowRun.created_at.desc())
        .limit(20)
    )
    pending_runs = pending_result.scalars().all()

    # Approved count (recent decisions)
    approved_result = await db.execute(
        select(func.count(ApprovalDecision.id)).where(ApprovalDecision.decision == "approved")
    )
    approved_count = approved_result.scalar() or 0

    # Rejected count
    rejected_result = await db.execute(
        select(func.count(ApprovalDecision.id)).where(ApprovalDecision.decision == "rejected")
    )
    rejected_count = rejected_result.scalar() or 0

    return OfficerQueueSummary(
        pending_review_count=len(pending_runs),
        recently_approved_count=approved_count,
        recently_rejected_count=rejected_count,
        pending_runs=[
            {
                "run_id": str(r.id),
                "student_id": str(r.student_id),
                "status": r.status,
                "current_step": r.current_step,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in pending_runs
        ],
    )
