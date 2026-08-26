"""
Governed Connector for Coding Platform Data.

Provides typed, consent-governed access to coding analytics data.
In production, this would integrate with external APIs (LeetCode, Codeforces, HackerRank).
For Lab 7, it uses mock data but enforces the same governance rules.
"""
import uuid
from typing import Optional, Dict, Any
from sqlalchemy import select

from app.connectors.base import BaseConnector, DataAccessDeniedError
from app.models.user import Student, Consent
from app.models.analysis import CodingAnalytics


class CodingConnector(BaseConnector):
    """Governs read access to coding platform analytics with consent enforcement."""

    async def verify_coding_consent(self, student_id: uuid.UUID) -> bool:
        """Strict governance check: Does this student consent to coding data access?"""
        result = await self.safe_execute(
            select(Consent).where(
                Consent.student_id == student_id,
                Consent.consent_type == "coding_platform",
                Consent.granted == True,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_coding_analytics(self, student_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Fetch a student's coding analytics securely.
        Consent is REQUIRED before any data access.
        """
        # Governance Gate
        if not await self.verify_coding_consent(student_id):
            raise DataAccessDeniedError(
                "Student has not consented to coding platform data access."
            )

        result = await self.safe_execute(
            select(CodingAnalytics)
            .where(CodingAnalytics.student_id == student_id)
            .order_by(CodingAnalytics.created_at.desc())
        )
        analytics = result.scalars().first()
        if not analytics:
            return None

        # Serialize to safe agent format (no ORM models leaked)
        return {
            "id": str(analytics.id),
            "platform": analytics.platform,
            "username": analytics.platform_username,
            "total_solved": analytics.total_problems_solved,
            "difficulty_distribution": {
                "easy": analytics.easy_count or 0,
                "medium": analytics.medium_count or 0,
                "hard": analytics.hard_count or 0,
            },
            "contest_rating": analytics.contest_rating,
            "contest_count": analytics.contest_count or 0,
            "streak_days": analytics.streak_days or 0,
            "topic_breakdown": analytics.topic_breakdown or [],
            "monthly_activity": analytics.monthly_activity or [],
            "last_synced": analytics.updated_at.isoformat() if analytics.updated_at else None,
        }
