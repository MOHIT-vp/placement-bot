"""
Base schema for Role-Family domain packs.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel


class SkillTaxonomy(BaseModel):
    required_skills: List[str]
    recommended_skills: List[str]
    tooling: List[str]


class QuestionBank(BaseModel):
    technical: List[str]
    behavioral: List[str]
    system_design: Optional[List[str]] = None


class ScoringWeights(BaseModel):
    skill_coverage: float
    coding_performance: float
    project_relevance: float
    interview_performance: float
    eligibility: float


class RoleFamilyConfig(BaseModel):
    """Configuration for a specific domain specialist."""
    family_id: str
    name: str
    description: str
    taxonomy: SkillTaxonomy
    question_bank: QuestionBank
    weights: ScoringWeights
