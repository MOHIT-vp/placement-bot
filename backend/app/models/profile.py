"""SQLAlchemy models — Resume, Profile, Skills, Projects, Experiences."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric,
    String, Text, Date,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Resume(Base):
    """Uploaded resume files."""
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=True)
    raw_text = Column(Text, nullable=True)
    status = Column(String(50), default="uploaded")
    uploaded_at = Column(DateTime(timezone=True), default=utcnow)
    parsed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student = relationship("Student", back_populates="resumes")
    profile = relationship("StudentProfile", back_populates="resume", uselist=False)


class StudentProfile(Base):
    """Structured profile extracted from resume + manual data."""
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True)
    summary = Column(Text, nullable=True)
    education_level = Column(String(50), nullable=True)
    specialization = Column(String(100), nullable=True)
    years_experience = Column(Integer, default=0)
    status = Column(String(50), default="draft")
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student = relationship("Student", back_populates="profiles")
    resume = relationship("Resume", back_populates="profile")
    skills = relationship("StudentSkill", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("StudentProject", back_populates="profile", cascade="all, delete-orphan")
    experiences = relationship("StudentExperience", back_populates="profile", cascade="all, delete-orphan")


class Skill(Base):
    """Master skill taxonomy."""
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    normalized_name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class StudentSkill(Base):
    """Skills extracted from a student's profile."""
    __tablename__ = "student_skills"
    __table_args__ = ({"schema": None},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    proficiency = Column(String(20), nullable=True)
    source = Column(String(50), nullable=True)
    verified = Column(Boolean, default=False)
    evidence_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    profile = relationship("StudentProfile", back_populates="skills")
    skill = relationship("Skill")


class StudentProject(Base):
    """Projects from student profile."""
    __tablename__ = "student_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(ARRAY(Text), nullable=True)
    url = Column(String(500), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_academic = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    profile = relationship("StudentProfile", back_populates="projects")


class StudentExperience(Base):
    """Work experience from student profile."""
    __tablename__ = "student_experiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=True)
    role_title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False)
    experience_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    profile = relationship("StudentProfile", back_populates="experiences")
