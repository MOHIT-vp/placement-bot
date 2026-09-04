"""
Lab 14 (Capstone): Admin API.

System management endpoints — admin role only.
Provides domain config introspection and system-wide statistics.
"""
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User
from app.models.workflow import WorkflowRun, ApprovalDecision, Version
from app.core.domains.registry import get_all_domains, get_domain_config

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DomainSummary(BaseModel):
    family_id: str
    name: str
    description: str
    required_skills: List[str]
    weights: Dict[str, float]


class SystemStats(BaseModel):
    total_workflow_runs: int
    pending_review: int
    approved: int
    rejected: int
    published_versions: int


# ---------------------------------------------------------------------------
# Domain Config Endpoints
# ---------------------------------------------------------------------------

@router.get("/domains", response_model=List[DomainSummary])
async def list_all_domains(
    current_user: User = Depends(require_role("admin", "placement_officer")),
):
    """
    List all registered domain specialist configurations.
    Accessible to admins and placement officers for reference.
    """
    configs = get_all_domains()
    return [
        DomainSummary(
            family_id=c.family_id,
            name=c.name,
            description=c.description,
            required_skills=c.taxonomy.required_skills,
            weights={
                "skill_coverage": c.weights.skill_coverage,
                "coding_performance": c.weights.coding_performance,
                "project_relevance": c.weights.project_relevance,
                "interview_performance": c.weights.interview_performance,
                "eligibility": c.weights.eligibility,
            },
        )
        for c in configs
    ]


@router.get("/domains/{family_id}", response_model=Dict[str, Any])
async def get_domain_detail(
    family_id: str,
    current_user: User = Depends(require_role("admin", "placement_officer")),
):
    """
    Get the full domain configuration for a specific role family.
    Includes taxonomy, question bank, and scoring weights.
    """
    config = get_domain_config(family_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{family_id}' not found. Available: software, analytics, core, higher_studies",
        )
    return config.model_dump()


# ---------------------------------------------------------------------------
# System Stats
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    System-wide statistics for the admin panel.
    Provides counts of pipeline runs, approval rates, and published plans.
    """
    # Total workflow runs
    total_result = await db.execute(select(func.count(WorkflowRun.id)))
    total_runs = total_result.scalar() or 0

    # By status
    pending_result = await db.execute(
        select(func.count(WorkflowRun.id)).where(WorkflowRun.status == "completed")
    )
    pending = pending_result.scalar() or 0

    approved_result = await db.execute(
        select(func.count(ApprovalDecision.id)).where(ApprovalDecision.decision == "approved")
    )
    approved = approved_result.scalar() or 0

    rejected_result = await db.execute(
        select(func.count(ApprovalDecision.id)).where(ApprovalDecision.decision == "rejected")
    )
    rejected = rejected_result.scalar() or 0

    published_result = await db.execute(
        select(func.count(Version.id)).where(Version.status == "published")
    )
    published = published_result.scalar() or 0

    return SystemStats(
        total_workflow_runs=total_runs,
        pending_review=pending,
        approved=approved,
        rejected=rejected,
        published_versions=published,
    )
