"""
Data & Analytics domain specialist config.
"""
from .base import RoleFamilyConfig, SkillTaxonomy, QuestionBank, ScoringWeights

ANALYTICS_CONFIG = RoleFamilyConfig(
    family_id="analytics",
    name="Data & Analytics",
    description="Data Science, Machine Learning, Data Engineering, Business Analytics",
    taxonomy=SkillTaxonomy(
        required_skills=["SQL", "Python", "Statistics", "Data Visualization"],
        recommended_skills=["Machine Learning", "Data Warehousing", "Big Data", "ETL"],
        tooling=["Jupyter", "Tableau/PowerBI", "Pandas", "Scikit-Learn"]
    ),
    question_bank=QuestionBank(
        technical=[
            "Explain the difference between supervised and unsupervised learning.",
            "How would you optimize a slow-running SQL query?",
            "What is the curse of dimensionality?"
        ],
        behavioral=[
            "Describe a time you had to present complex data to a non-technical audience.",
            "How do you ensure data quality in your analysis?"
        ],
        system_design=[
            "Design a real-time fraud detection pipeline.",
            "How would you design a recommendation engine for an e-commerce site?"
        ]
    ),
    weights=ScoringWeights(
        skill_coverage=0.40,
        coding_performance=0.20,
        project_relevance=0.25,
        interview_performance=0.10,
        eligibility=0.05
    )
)
