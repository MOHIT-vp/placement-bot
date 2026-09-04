"""
Lab 11 Acceptance Suite — Schema Contract Tests

Every agent output must conform to its required schema.
These tests run deterministically — no LLM, no I/O.

Gate: NO output advances to an officer without all schema checks passing.
"""


# ---------------------------------------------------------------------------
# Student Profile Schema
# ---------------------------------------------------------------------------

class TestStudentProfileSchema:
    """student_profile must have the required structure."""

    def test_has_required_keys(self, canonical_student_profile):
        required = {"summary", "skills", "projects", "education"}
        missing = required - set(canonical_student_profile.keys())
        assert not missing, f"student_profile missing keys: {missing}"

    def test_skills_are_typed(self, canonical_student_profile):
        for skill in canonical_student_profile["skills"]:
            assert "name" in skill, "Skill missing 'name'"
            assert "proficiency" in skill, "Skill missing 'proficiency'"
            assert skill["proficiency"] in ("beginner", "intermediate", "advanced"), \
                f"Invalid proficiency: {skill['proficiency']}"

    def test_projects_are_typed(self, canonical_student_profile):
        for project in canonical_student_profile["projects"]:
            assert "title" in project
            assert "technologies" in project
            assert isinstance(project["technologies"], list)

    def test_education_has_gpa(self, canonical_student_profile):
        edu = canonical_student_profile.get("education")
        if edu:
            assert "gpa" in edu
            gpa = edu["gpa"]
            assert gpa is None or (0.0 <= gpa <= 10.0), f"GPA out of range: {gpa}"


# ---------------------------------------------------------------------------
# Skill Gap Report Schema
# ---------------------------------------------------------------------------

class TestSkillGapReportSchema:
    def test_has_required_keys(self, canonical_skill_gap_report):
        required = {"overall_coverage", "overall_assessment", "strengths", "gaps"}
        missing = required - set(canonical_skill_gap_report.keys())
        assert not missing, f"skill_gap_report missing keys: {missing}"

    def test_coverage_in_range(self, canonical_skill_gap_report):
        cov = canonical_skill_gap_report["overall_coverage"]
        assert 0.0 <= cov <= 100.0, f"Coverage out of range: {cov}"

    def test_gaps_have_severity(self, canonical_skill_gap_report):
        valid_severities = {"none", "low", "medium", "high", "critical"}
        for gap in canonical_skill_gap_report["gaps"]:
            assert "severity" in gap
            assert gap["severity"] in valid_severities, \
                f"Invalid severity: {gap['severity']}"

    def test_gaps_have_recommendation(self, canonical_skill_gap_report):
        for gap in canonical_skill_gap_report["gaps"]:
            assert "recommendation" in gap, f"Gap {gap.get('skill')} missing recommendation"
            assert len(gap["recommendation"]) > 10, "Recommendation too short"

    def test_assessment_value(self, canonical_skill_gap_report):
        valid = {"exceptional", "competitive", "developing", "early_stage"}
        assert canonical_skill_gap_report["overall_assessment"] in valid, \
            f"Invalid assessment: {canonical_skill_gap_report['overall_assessment']}"


# ---------------------------------------------------------------------------
# Coding Analytics Schema
# ---------------------------------------------------------------------------

class TestCodingAnalyticsSchema:
    def test_has_required_keys(self, canonical_coding_analytics):
        required = {"summary", "topic_analysis"}
        missing = required - set(canonical_coding_analytics.keys())
        assert not missing, f"coding_analytics missing keys: {missing}"

    def test_summary_has_metrics(self, canonical_coding_analytics):
        summary = canonical_coding_analytics["summary"]
        required = {"total_solved", "coding_percentile", "difficulty_score", "activity_trend"}
        missing = required - set(summary.keys())
        assert not missing, f"summary missing keys: {missing}"

    def test_percentile_in_range(self, canonical_coding_analytics):
        pct = canonical_coding_analytics["summary"]["coding_percentile"]
        assert 0.0 <= pct <= 100.0, f"Percentile out of range: {pct}"

    def test_activity_trend_valid(self, canonical_coding_analytics):
        trend = canonical_coding_analytics["summary"]["activity_trend"]
        assert trend in ("improving", "stable", "declining", "new"), \
            f"Invalid trend: {trend}"

    def test_topic_analysis_typed(self, canonical_coding_analytics):
        for topic in canonical_coding_analytics["topic_analysis"]:
            assert "topic" in topic
            assert "strength_level" in topic
            assert topic["strength_level"] in ("strong", "competent", "needs_work", "weak")


# ---------------------------------------------------------------------------
# Job Matching Result Schema
# ---------------------------------------------------------------------------

class TestJobMatchingSchema:
    def test_has_required_keys(self, canonical_matching_result):
        required = {"readiness_score", "matches", "total_jobs_evaluated", "eligible_count"}
        missing = required - set(canonical_matching_result.keys())
        assert not missing, f"matching_result missing keys: {missing}"

    def test_readiness_score_structure(self, canonical_matching_result):
        rs = canonical_matching_result["readiness_score"]
        assert "total" in rs and "max" in rs and "percentage" in rs
        assert 0.0 <= rs["percentage"] <= 100.0

    def test_matches_have_required_fields(self, canonical_matching_result):
        required = {"company_name", "role_title", "match_percentage",
                    "confidence", "is_eligible", "reasoning", "breakdown"}
        for match in canonical_matching_result["matches"]:
            missing = required - set(match.keys())
            assert not missing, f"Match missing fields: {missing}"

    def test_confidence_in_range(self, canonical_matching_result):
        for match in canonical_matching_result["matches"]:
            conf = match["confidence"]
            assert 0.0 <= conf <= 1.0, f"Confidence out of range: {conf}"

    def test_low_confidence_flagged(self, canonical_matching_result):
        for match in canonical_matching_result["matches"]:
            if match["confidence"] < 0.6:
                assert match["is_low_confidence"], \
                    f"Low confidence match not flagged: {match['company_name']}"

    def test_breakdown_components(self, canonical_matching_result):
        expected_components = {
            "skill_coverage", "coding_performance",
            "project_relevance", "interview_readiness", "eligibility"
        }
        for match in canonical_matching_result["matches"]:
            actual = {b["component"] for b in match["breakdown"]}
            missing = expected_components - actual
            assert not missing, f"Missing breakdown components: {missing}"


# ---------------------------------------------------------------------------
# Interview Result Schema
# ---------------------------------------------------------------------------

class TestInterviewResultSchema:
    def test_has_required_keys(self, canonical_interview_result):
        required = {"target_role", "readiness_assessment", "questions",
                    "total_questions", "ai_generated_disclaimer"}
        missing = required - set(canonical_interview_result.keys())
        assert not missing, f"interview_result missing keys: {missing}"

    def test_ai_disclaimer_present(self, canonical_interview_result):
        disclaimer = canonical_interview_result.get("ai_generated_disclaimer", "")
        assert "[AI-Generated]" in disclaimer, "AI disclaimer must contain '[AI-Generated]'"

    def test_questions_are_marked_ai_generated(self, canonical_interview_result):
        for q in canonical_interview_result["questions"]:
            assert q.get("ai_generated") is True, \
                f"Question not marked ai_generated: {q.get('text', '')[:40]}"
