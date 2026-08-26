"""Govened connector for Student and Profile data."""
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.connectors.base import BaseConnector, DataAccessDeniedError
from app.models.user import Student, Consent
from app.models.profile import StudentProfile

class StudentConnector(BaseConnector):
    """Governs read/write access to student profiles and ensures consent boundaries."""

    async def verify_consent(self, student_id: uuid.UUID, consent_type: str) -> bool:
        """Strict governance check: Does this student consent to this operation?"""
        result = await self.safe_execute(
            select(Consent).where(
                Consent.student_id == student_id,
                Consent.consent_type == consent_type,
                Consent.granted == True
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_student_profile(self, student_id: uuid.UUID) -> Optional[dict]:
        """Fetch a student's parsed profile securely."""
        # Governance Gate: Profile processing requires data_sharing consent
        if not await self.verify_consent(student_id, "data_sharing"):
             raise DataAccessDeniedError("Student has not consented to data sharing.")
             
        result = await self.safe_execute(
            select(StudentProfile)
            .where(StudentProfile.student_id == student_id)
            .order_by(StudentProfile.created_at.desc())
            .options(
                selectinload(StudentProfile.skills),
                selectinload(StudentProfile.projects),
                selectinload(StudentProfile.experiences)
            )
        )
        profile = result.scalars().first()
        if not profile:
            return None
            
        # Serialize to untrusted agent format
        return {
            "id": str(profile.id),
            "summary": profile.summary,
            "skills": [{"name": s.skill.name if s.skill else "unknown", "proficiency": s.proficiency} for s in profile.skills],
            "projects": [{"title": p.title, "technologies": p.technologies} for p in profile.projects],
        }
