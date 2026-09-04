"""
Lab 12: Approval Workflow API

Officer-only endpoints for the review → approve/reject/edit → publish flow.
RBAC: only users with role 'placement_officer' or 'admin' can act on approvals.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.models.workflow import ApprovalDecision, WorkflowRun, AuditLog

router = APIRouter(prefix="/approvals", tags=["Approvals"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ApprovalRequest(BaseModel):
    decision: str               # "approved" | "rejected" | "changes_requested"
    comments: Optional[str] = None
    edits: Optional[Dict[str, Any]] = None  # Officer-applied edits to the draft


class ApprovalResponse(BaseModel):
    approval_id: uuid.UUID
    workflow_run_id: uuid.UUID
    decision: str
    comments: Optional[str]
    reviewed_by: str
    reviewed_at: str


class ApprovalQueueItem(BaseModel):
    workflow_run_id: uuid.UUID
    student_id: uuid.UUID
    status: str
    current_step: str
    created_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/queue", response_model=List[ApprovalQueueItem])
async def get_approval_queue(
    current_user: User = Depends(require_role("placement_officer", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all workflow runs awaiting officer approval.
    Accessible only to placement_officer and admin roles.
    """
    result = await db.execute(
        select(WorkflowRun).where(WorkflowRun.status == "completed").order_by(WorkflowRun.created_at.desc())
    )
    runs = result.scalars().all()

    return [
        ApprovalQueueItem(
            workflow_run_id=run.id,
            student_id=run.student_id,
            status=run.status,
            current_step=run.current_step or "unknown",
            created_at=run.created_at.isoformat() if run.created_at else "",
        )
        for run in runs
    ]


@router.post("/{workflow_run_id}", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
async def submit_approval(
    workflow_run_id: uuid.UUID,
    request: ApprovalRequest,
    current_user: User = Depends(require_role("placement_officer", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an approval decision (approve / reject / request changes).
    Only placement officers and admins may call this.

    - approved         → workflow publishes; triggers Version creation
    - rejected         → workflow marked rejected; student notified
    - changes_requested → workflow returned for amendments
    """
    # Validate decision value
    valid_decisions = {"approved", "rejected", "changes_requested"}
    if request.decision not in valid_decisions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid decision '{request.decision}'. Must be one of: {valid_decisions}",
        )

    # Verify the workflow run exists
    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == workflow_run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    # Prevent duplicate approvals on a run that is already decided
    existing = await db.execute(
        select(ApprovalDecision).where(
            ApprovalDecision.workflow_run_id == workflow_run_id,
            ApprovalDecision.decision.in_(["approved", "rejected"])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This workflow run already has a final approval decision.",
        )

    # Record the decision
    approval = ApprovalDecision(
        workflow_run_id=workflow_run_id,
        reviewer_id=current_user.id,
        decision=request.decision,
        comments=request.comments,
        edits=request.edits,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(approval)

    # Update workflow run status
    run.status = request.decision  # "approved" / "rejected" / "changes_requested"

    # Write audit log entry
    audit = AuditLog(
        actor_id=current_user.id,
        actor_type="placement_officer",
        workflow_run_id=workflow_run_id,
        action="approval_decision",
        entity_type="workflow_run",
        entity_id=workflow_run_id,
        decision=request.decision,
        approval_decision=request.decision,
        correlation_id=uuid.uuid4(),
        details={"comments": request.comments, "edits_applied": bool(request.edits)},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(approval)

    return ApprovalResponse(
        approval_id=approval.id,
        workflow_run_id=workflow_run_id,
        decision=approval.decision,
        comments=approval.comments,
        reviewed_by=current_user.full_name,
        reviewed_at=approval.reviewed_at.isoformat(),
    )


@router.get("/{workflow_run_id}", response_model=List[ApprovalResponse])
async def get_approval_history(
    workflow_run_id: uuid.UUID,
    current_user: User = Depends(require_role("placement_officer", "admin", "student")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all approval decisions for a specific workflow run.
    Students can read their own approval history; officers can read all.
    """
    result = await db.execute(
        select(ApprovalDecision, User)
        .join(User, ApprovalDecision.reviewer_id == User.id)
        .where(ApprovalDecision.workflow_run_id == workflow_run_id)
        .order_by(ApprovalDecision.reviewed_at.asc())
    )
    rows = result.all()

    return [
        ApprovalResponse(
            approval_id=decision.id,
            workflow_run_id=workflow_run_id,
            decision=decision.decision,
            comments=decision.comments,
            reviewed_by=reviewer.full_name,
            reviewed_at=decision.reviewed_at.isoformat(),
        )
        for decision, reviewer in rows
    ]
