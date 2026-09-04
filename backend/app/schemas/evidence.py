from typing import List, Optional
from pydantic import BaseModel, Field

class EvidenceRecord(BaseModel):
    """
    Structured record of evidence grounding an agent's output.
    """
    entity_type: str = Field(description="The type of entity this evidence supports (e.g., 'student_profile', 'skill_gap_report', 'company_match').")
    evidence_type: str = Field(description="The nature of the evidence (e.g., 'resume_parsing', 'deterministic_computation', 'platform_aggregation', 'ai_generation').")
    source: str = Field(description="The agent or component that generated this evidence.")
    content: str = Field(description="A detailed description or excerpt of the evidence.")
    scope_tags: List[str] = Field(default_factory=list, description="Tags for categorizing and retrieving this evidence.")
