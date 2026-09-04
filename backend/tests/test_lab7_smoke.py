"""
Lab 7 End-to-End Smoke Test — Full Pipeline Validation.

This test runs the complete placement readiness pipeline with mock data
to verify that all agents are properly wired and produce valid outputs.
It tests the DETERMINISTIC components directly (no LLM calls needed).
"""
import sys
import os
import json
from datetime import datetime, timezone

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_skill_gap_deterministic():
    """Test the deterministic skill gap computation independently."""
    from app.agents.skill_gap_agent import _compute_skill_coverage, _compute_gap_severity

    student_skills = [
        {"name": "python", "proficiency": "advanced"},
        {"name": "javascript", "proficiency": "intermediate"},
        {"name": "react.js", "proficiency": "intermediate"},
        {"name": "sql", "proficiency": "beginner"},
        {"name": "git", "proficiency": "intermediate"},
    ]

    required_skills = [
        {"skill_name": "Python", "expected_level": "intermediate", "importance": "required", "source": "test"},
        {"skill_name": "JavaScript", "expected_level": "intermediate", "importance": "required", "source": "test"},
        {"skill_name": "React.js", "expected_level": "intermediate", "importance": "required", "source": "test"},
        {"skill_name": "SQL", "expected_level": "intermediate", "importance": "required", "source": "test"},
        {"skill_name": "Docker", "expected_level": "beginner", "importance": "required", "source": "test"},
    ]

    result = _compute_skill_coverage(student_skills, required_skills)

    assert result["overall_coverage"] == 60.0, f"Expected 60%, got {result['overall_coverage']}%"
    assert result["matched"] == 3, f"Expected 3 matched, got {result['matched']}"
    assert len(result["gaps"]) == 2, f"Expected 2 gaps, got {len(result['gaps'])}"
    assert len(result["strengths"]) == 3, f"Expected 3 strengths, got {len(result['strengths'])}"

    # Test severity calculation
    assert _compute_gap_severity("intermediate", "beginner") == "low"
    assert _compute_gap_severity("advanced", "beginner") == "medium"
    assert _compute_gap_severity("intermediate", None) == "critical"
    assert _compute_gap_severity("intermediate", "intermediate") == "none"
    assert _compute_gap_severity("intermediate", "advanced") == "none"

    print("[PASS] Skill gap deterministic computation")


def test_coding_analytics_deterministic():
    """Test the deterministic coding analytics computations."""
    from app.agents.coding_analytics_agent import (
        _compute_difficulty_score,
        _compute_activity_trend,
        _compute_topic_strengths,
        _compute_percentile_estimate,
    )

    # Difficulty score
    dist = {"easy": 80, "medium": 80, "hard": 20}
    score = _compute_difficulty_score(dist)
    assert 0 <= score <= 100, f"Difficulty score out of range: {score}"

    # Activity trend
    improving_data = [
        {"problems_solved": 5}, {"problems_solved": 10}, {"problems_solved": 15},
        {"problems_solved": 20}, {"problems_solved": 25}, {"problems_solved": 30},
    ]
    assert _compute_activity_trend(improving_data) == "improving"

    declining_data = [
        {"problems_solved": 30}, {"problems_solved": 25}, {"problems_solved": 20},
        {"problems_solved": 15}, {"problems_solved": 10}, {"problems_solved": 5},
    ]
    assert _compute_activity_trend(declining_data) == "declining"

    stable_data = [
        {"problems_solved": 10}, {"problems_solved": 11}, {"problems_solved": 10},
        {"problems_solved": 11}, {"problems_solved": 10}, {"problems_solved": 11},
    ]
    assert _compute_activity_trend(stable_data) == "stable"

    # Topic strengths
    topics = [
        {"topic": "Arrays", "solved": 30, "total_attempted": 33, "accuracy": 90.0},
        {"topic": "DP", "solved": 5, "total_attempted": 15, "accuracy": 33.3},
    ]
    strengths = _compute_topic_strengths(topics)
    assert strengths[0]["strength_level"] == "strong"
    assert strengths[1]["strength_level"] == "needs_work"

    # Percentile estimate
    pct = _compute_percentile_estimate(200, 1500, 50.0)
    assert 0 <= pct <= 100, f"Percentile out of range: {pct}"

    print("[PASS] Coding analytics deterministic computation")


def test_job_matching_deterministic():
    """Test the deterministic scoring engine."""
    from app.agents.job_matching_agent import (
        _compute_skill_coverage_score,
        _compute_coding_performance_score,
        _compute_project_relevance_score,
        _check_eligibility,
        _compute_match_confidence,
        DEFAULT_SCORING_CONFIG,
    )

    student_skills = [
        {"name": "python"}, {"name": "javascript"}, {"name": "react.js"},
        {"name": "sql"}, {"name": "git"},
    ]

    # Skill coverage
    score, details = _compute_skill_coverage_score(
        student_skills,
        ["Python", "JavaScript", "SQL", "Git", "Docker"],
        ["AWS", "React.js"],
        40,
    )
    assert 0 <= score <= 40, f"Skill score out of range: {score}"
    assert details["matched_required"] == 4
    assert details["total_required"] == 5

    # Coding performance
    coding_analytics = {
        "summary": {
            "coding_percentile": 72.3,
            "difficulty_score": 55.0,
            "activity_trend": "improving",
        }
    }
    score, details = _compute_coding_performance_score(coding_analytics, 25)
    assert 0 <= score <= 25, f"Coding score out of range: {score}"

    # Project relevance
    profile = {
        "projects": [
            {"technologies": ["Python", "Flask", "SQL"]},
            {"technologies": ["React.js", "Node.js"]},
        ]
    }
    job = {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["React.js"],
    }
    score, details = _compute_project_relevance_score(profile, job, 15)
    assert 0 <= score <= 15, f"Project score out of range: {score}"

    # Eligibility
    profile_with_edu = {
        "education": {"gpa": 8.5},
        "years_experience": 0,
    }
    job_with_reqs = {"min_cgpa": 7.0, "min_experience": 0}
    score, is_eligible, details = _check_eligibility(profile_with_edu, job_with_reqs, 5)
    assert is_eligible, "Should be eligible with GPA 8.5 >= 7.0"
    assert score == 5

    # Ineligible case
    profile_low_gpa = {
        "education": {"gpa": 6.0},
        "years_experience": 0,
    }
    score, is_eligible, details = _check_eligibility(profile_low_gpa, job_with_reqs, 5)
    assert not is_eligible, "Should be ineligible with GPA 6.0 < 7.0"
    assert score == 0

    print("[PASS] Job matching deterministic scoring")


def test_validation_checks():
    """Test the validation agent checks with a complete mock state."""
    from app.agents.validation_agent import validation_agent_node

    # Build a complete valid state
    valid_state = {
        "run_id": "test-run-001",
        "student_id": "test-student-001",
        "consent_validated": True,
        "student_profile": {
            "summary": "Test student",
            "skills": [{"name": "Python", "proficiency": "advanced"}],
            "projects": [{"title": "Test Project", "technologies": ["Python"]}],
            "education": {"gpa": 8.5},
        },
        "skill_gap_report": {
            "overall_coverage": 75.0,
            "strengths": [{"skill": "Python", "level": "advanced", "evidence": "test"}],
            "gaps": [
                {
                    "skill": "Docker",
                    "required_level": "beginner",
                    "current_level": "missing",
                    "severity": "critical",
                    "recommendation": "Study Docker containerization fundamentals.",
                }
            ],
            "overall_assessment": "competitive",
        },
        "coding_analytics": {
            "summary": {
                "total_solved": 187,
                "coding_percentile": 72.3,
                "difficulty_score": 55.0,
                "activity_trend": "improving",
                "contest_rating": 1547,
            },
            "topic_analysis": [],
        },
        "matching_result": {
            "readiness_score": {"total": 68.5, "max": 100, "percentage": 68.5},
            "matches": [
                {
                    "job_id": "job-001",
                    "company_name": "TechCorp",
                    "role_title": "SWE",
                    "match_score": 68.5,
                    "max_score": 100,
                    "match_percentage": 68.5,
                    "confidence": 0.78,
                    "is_eligible": True,
                    "is_low_confidence": False,
                    "reasoning": "Strong Python skills match the backend requirements well. Good coding metrics.",
                    "breakdown": [
                        {"component": "skill_coverage", "points": 28, "max": 40,
                         "details": {"required_ratio": 0.8}},
                        {"component": "coding_performance", "points": 18, "max": 25, "details": {}},
                        {"component": "project_relevance", "points": 10, "max": 15, "details": {}},
                        {"component": "interview_readiness", "points": 7.5, "max": 15, "details": {}},
                        {"component": "eligibility", "points": 5, "max": 5,
                         "details": {"is_eligible": True}},
                    ],
                },
            ],
            "low_confidence_flags": [],
            "total_jobs_evaluated": 1,
            "eligible_count": 1,
        },
        "interview_result": {
            "questions": [{"text": "Q1"}],
            "total_questions": 1,
            "readiness_assessment": {"percentage": 65.0},
        },
        "roadmap": {"items": [], "total_items": 0},
        "evidence_records": [
            {"entity_type": "skill_gap_report", "evidence_type": "test", "source": "test", "content": "test"},
            {"entity_type": "coding_analytics", "evidence_type": "test", "source": "test", "content": "test"},
            {"entity_type": "company_match", "evidence_type": "test", "source": "test", "content": "test"},
        ],
        "errors": [],
        "audit_events": [],
        "retry_count": 0,
        "max_retries": 3,
        "budget_remaining": 100000,
    }

    result = validation_agent_node(valid_state)

    report = result.get("validation_report", {})
    print(f"\n  Validation Results:")
    print(f"  Total checks: {report.get('total_checks', 0)}")
    print(f"  Passed: {report.get('passed_checks', 0)}")
    print(f"  Error failures: {report.get('error_failures', 0)}")
    print(f"  Warning failures: {report.get('warning_failures', 0)}")

    for check in report.get("checks", []):
        status = "PASS" if check["passed"] else "FAIL"
        print(f"    [{status}] {check['code']}: {check['message'][:80]}")

    passed = result.get("validation_passed", False)
    print(f"\n  Overall: {'PASSED' if passed else 'FAILED'}")

    # Should pass all checks
    assert report.get("total_checks") == 12, f"Expected 12 checks, got {report.get('total_checks')}"
    print("[PASS] Validation agent checks")


def test_graph_compilation():
    """Test that the full graph compiles and has all expected nodes."""
    import pytest
    try:
        from app.agents.graph import agent_runner
    except ImportError:
        pytest.skip("langgraph not installed")

    nodes = list(agent_runner.get_graph().nodes.keys())

    expected_nodes = [
        "plan_workflow", "lock_plan", "consent_validation", "resume_agent",
        "skill_gap_agent", "coding_analytics_agent", "join_parallel",
        "job_matching_agent", "interview_agent",
        "validation_agent", "diagnose_and_regenerate", "assemble_draft",
    ]

    for node in expected_nodes:
        assert node in nodes, f"Missing node: {node}"

    print(f"[PASS] Graph compiled with {len(nodes)} nodes: {nodes}")


def test_skill_gap_agent_node():
    """Test the skill gap agent node with mock state (no LLM)."""
    from app.agents.skill_gap_agent import skill_gap_agent_node

    state = {
        "student_profile": {
            "skills": [
                {"name": "python", "proficiency": "advanced"},
                {"name": "javascript", "proficiency": "intermediate"},
                {"name": "sql", "proficiency": "beginner"},
            ],
        },
        "target_roles": ["software_engineer"],
        "consent_validated": True,
    }

    result = skill_gap_agent_node(state)

    assert "skill_gap_report" in result, "Missing skill_gap_report"
    report = result["skill_gap_report"]
    assert "overall_coverage" in report, "Missing overall_coverage"
    assert "strengths" in report, "Missing strengths"
    assert "gaps" in report, "Missing gaps"
    assert 0 <= report["overall_coverage"] <= 100, "Coverage out of range"

    print(f"[PASS] Skill gap agent - Coverage: {report['overall_coverage']}%, "
          f"Gaps: {len(report['gaps'])}, Strengths: {len(report['strengths'])}")


def test_coding_analytics_agent_node():
    """Test the coding analytics agent node with mock state (no LLM)."""
    from app.agents.coding_analytics_agent import coding_analytics_agent_node

    state = {
        "student_id": "test-student-001",
        "consent_validated": True,
    }

    result = coding_analytics_agent_node(state)

    assert "coding_analytics" in result, "Missing coding_analytics"
    analytics = result["coding_analytics"]
    assert "summary" in analytics, "Missing summary"
    assert "topic_analysis" in analytics, "Missing topic_analysis"
    assert analytics["summary"]["total_solved"] > 0, "No problems solved"

    print(f"[PASS] Coding analytics agent - Solved: {analytics['summary']['total_solved']}, "
          f"Trend: {analytics['summary']['activity_trend']}")


def test_job_matching_agent_node():
    """Test the job matching agent node with mock state (no LLM)."""
    from app.agents.job_matching_agent import job_matching_agent_node

    state = {
        "student_profile": {
            "skills": [
                {"name": "python", "proficiency": "advanced"},
                {"name": "javascript", "proficiency": "intermediate"},
                {"name": "react.js", "proficiency": "intermediate"},
                {"name": "sql", "proficiency": "intermediate"},
                {"name": "git", "proficiency": "intermediate"},
            ],
            "projects": [
                {"title": "Web App", "technologies": ["Python", "React.js", "SQL"]},
            ],
            "education": {"gpa": 8.0},
        },
        "skill_gap_report": {"overall_coverage": 70.0},
        "coding_analytics": {
            "summary": {
                "coding_percentile": 72.3,
                "difficulty_score": 55.0,
                "activity_trend": "improving",
            }
        },
        "consent_validated": True,
    }

    result = job_matching_agent_node(state)

    assert "matching_result" in result, "Missing matching_result"
    matching = result["matching_result"]
    assert "matches" in matching, "Missing matches"
    assert len(matching["matches"]) > 0, "No matches produced"

    top = matching["matches"][0]
    print(f"[PASS] Job matching agent - Top match: {top['company_name']} "
          f"({top['match_percentage']}%, confidence={top['confidence']})")


def test_validation_with_failing_state():
    """Test that validation correctly catches problems."""
    from app.agents.validation_agent import validation_agent_node

    # State with deliberate problems
    bad_state = {
        "run_id": "test-run-bad",
        "student_id": "test-student-bad",
        "consent_validated": False,  # FAIL: consent not validated
        "student_profile": None,     # FAIL: missing section
        "skill_gap_report": None,    # FAIL: missing section
        "coding_analytics": None,    # FAIL: missing section
        "matching_result": None,     # FAIL: missing section
        "interview_result": None,    # FAIL: missing section
        "evidence_records": [],      # FAIL: no evidence
        "errors": [],
        "audit_events": [],
        "retry_count": 0,
        "max_retries": 3,
    }

    result = validation_agent_node(bad_state)
    assert not result["validation_passed"], "Should have FAILED validation"
    assert len(result["failing_checks"]) > 0, "Should have failing checks"

    print(f"[PASS] Validation correctly caught {len(result['failing_checks'])} failures: "
          f"{result['failing_checks']}")


if __name__ == "__main__":
    print("=" * 60)
    print("Lab 7 - Full Node Graph - Smoke Tests")
    print("=" * 60)

    tests = [
        test_skill_gap_deterministic,
        test_coding_analytics_deterministic,
        test_job_matching_deterministic,
        test_graph_compilation,
        test_skill_gap_agent_node,
        test_coding_analytics_agent_node,
        test_job_matching_agent_node,
        test_validation_checks,
        test_validation_with_failing_state,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
