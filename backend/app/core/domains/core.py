"""
Core Engineering domain specialist config.
"""
from .base import RoleFamilyConfig, SkillTaxonomy, QuestionBank, ScoringWeights

CORE_CONFIG = RoleFamilyConfig(
    family_id="core",
    name="Core Engineering",
    description="Mechanical, Electrical, Civil, and Core Engineering",
    taxonomy=SkillTaxonomy(
        required_skills=["Thermodynamics/Circuits", "Engineering Mechanics", "Material Science"],
        recommended_skills=["AutoCAD", "MATLAB", "PLC/SCADA", "FEA/CFD"],
        tooling=["SolidWorks", "ANSYS", "LabVIEW"]
    ),
    question_bank=QuestionBank(
        technical=[
            "Explain the first and second laws of thermodynamics.",
            "How does a 3-phase induction motor work?",
            "What is the difference between stress and strain?"
        ],
        behavioral=[
            "Describe a time you had to solve a difficult engineering problem.",
            "How do you ensure safety protocols are followed in a project?"
        ],
        system_design=[
            "Design a simple HVAC system for a commercial building.",
            "How would you design a power distribution network for a small town?"
        ]
    ),
    weights=ScoringWeights(
        skill_coverage=0.45,
        coding_performance=0.05,
        project_relevance=0.30,
        interview_performance=0.15,
        eligibility=0.05
    )
)
