"""
Lab 13: Domain Specialists — Matching API.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_student, get_db
from app.models.user import Student
from app.models.workflow import Version

router = APIRouter(prefix="/matching", tags=["Matching"])


@router.get("/me", response_model=Dict[str, Any])
async def get_my_matches(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the job matches and readiness score from the latest approved readiness plan.
    """
    result = await db.execute(
        select(Version)
        .where(
            Version.student_id == current_student.id,
            Version.entity_type == "readiness_plan",
            Version.status == "published"
        )
        .order_by(Version.version_number.desc())
        .limit(1)
    )
    version = result.scalar_one_or_none()

    if not version or "matching_result" not in version.snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No approved job matches found."
        )

    return version.snapshot["matching_result"]
