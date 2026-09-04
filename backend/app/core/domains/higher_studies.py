"""
Higher Studies domain specialist config.
"""
from .base import RoleFamilyConfig, SkillTaxonomy, QuestionBank, ScoringWeights

HIGHER_STUDIES_CONFIG = RoleFamilyConfig(
    family_id="higher_studies",
    name="Higher Studies",
    description="Research, Master's, PhD, GRE/GATE Preparation",
    taxonomy=SkillTaxonomy(
        required_skills=["Research Methodology", "Academic Writing", "Quantitative Aptitude"],
        recommended_skills=["Data Analysis", "Publication Formatting", "Literature Review"],
        tooling=["LaTeX", "EndNote/Mendeley", "SPSS/R"]
    ),
    question_bank=QuestionBank(
        technical=[
            "Describe your undergraduate research project and its implications.",
            "What statistical tests did you use for your analysis and why?",
            "How do you stay updated with the latest research in your field?"
        ],
        behavioral=[
            "Why do you want to pursue higher studies in this specific domain?",
            "Tell me about a time you faced a setback in your research and how you handled it."
        ],
        system_design=None
    ),
    weights=ScoringWeights(
        skill_coverage=0.30,
        coding_performance=0.0,
        project_relevance=0.40,
        interview_performance=0.20,
        eligibility=0.10
    )
)
