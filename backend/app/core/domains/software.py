"""
Software Engineering domain specialist config.
"""
from .base import RoleFamilyConfig, SkillTaxonomy, QuestionBank, ScoringWeights

SOFTWARE_CONFIG = RoleFamilyConfig(
    family_id="software",
    name="Software Engineering",
    description="Software Development, Backend, Frontend, Full Stack",
    taxonomy=SkillTaxonomy(
        required_skills=["Data Structures", "Algorithms", "Object-Oriented Programming"],
        recommended_skills=["System Design", "Cloud Computing", "REST APIs", "Databases"],
        tooling=["Git", "Docker", "Linux"]
    ),
    question_bank=QuestionBank(
        technical=[
            "Explain the time complexity of QuickSort.",
            "How does a hash map resolve collisions?",
            "Describe the differences between REST and GraphQL."
        ],
        behavioral=[
            "Tell me about a time you had to debug a difficult issue.",
            "How do you handle disagreements in code reviews?"
        ],
        system_design=[
            "Design a URL shortener service.",
            "How would you scale a web application to handle 1 million concurrent users?"
        ]
    ),
    weights=ScoringWeights(
        skill_coverage=0.30,
        coding_performance=0.40,
        project_relevance=0.15,
        interview_performance=0.10,
        eligibility=0.05
    )
)
