"""Governed connector for Role and Company requirements."""
import uuid
from typing import Optional, List
from sqlalchemy import select

from app.connectors.base import BaseConnector
from app.models.company import Job, RoleSkill

class RoleConnector(BaseConnector):
    """Governs read access to job requirements and system benchmarks."""

    async def get_job_requirements(self, job_id: uuid.UUID) -> Optional[dict]:
        """Fetch strict job requirements without returning raw DB models."""
        result = await self.safe_execute(
            select(Job).where(Job.id == job_id, Job.is_active == True)
        )
        job = result.scalar_one_or_none()
        if not job:
            return None
            
        # We would typically fetch linked skills here through joined loading
        return {
            "job_id": str(job.id),
            "title": job.title,
            "role_family": job.role_family,
            "min_experience": job.min_experience,
            "description": job.description
        }
