"""SQLAlchemy models — Companies, Jobs, Role Skills, Benchmarks."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Company(Base):
    """Companies that recruit students."""
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class Job(Base):
    """Job roles offered by companies."""
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    role_family = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    min_cgpa = Column(Numeric(4, 2), nullable=True)
    min_experience = Column(Integer, default=0)
    package_lpa = Column(Numeric(6, 2), nullable=True)
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    embedding = Column(Vector(768), nullable=True, index=True) # Assuming 768 or mapped Gemini size
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company = relationship("Company", back_populates="jobs")
    role_skills = relationship("RoleSkill", back_populates="job", cascade="all, delete-orphan")


class RoleSkill(Base):
    """Skills required for a specific job/role."""
    __tablename__ = "role_skills"
    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_role_skill"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    importance = Column(String(20), nullable=False)  # required, preferred, nice_to_have
    min_proficiency = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    job = relationship("Job", back_populates="role_skills")
    skill = relationship("Skill")


class SkillBenchmark(Base):
    """Configurable skill benchmarks for target roles."""
    __tablename__ = "skill_benchmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_family = Column(String(50), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    expected_level = Column(String(20), nullable=False)
    weight = Column(Numeric(5, 2), default=1.0)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    skill = relationship("Skill")


class ScoringConfig(Base):
    """Configurable scoring weights."""
    __tablename__ = "scoring_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    role_family = Column(String(50), nullable=True)
    config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
