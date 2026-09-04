"""
Lab 13: Domain Specialists — Interviews API.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_student, get_db
from app.models.user import Student
from app.models.workflow import Version

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.get("/me", response_model=Dict[str, Any])
async def get_my_interviews(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the mock interview results and learning roadmap from the latest approved readiness plan.
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

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No approved interview data found."
        )

    return {
        "interview_result": version.snapshot.get("interview_result"),
        "roadmap": version.snapshot.get("roadmap")
    }
