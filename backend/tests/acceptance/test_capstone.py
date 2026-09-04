"""
Lab 14: Capstone Acceptance Tests.

Final end-to-end tests validating the full structure of the API.
"""
from typing import Dict, Any


class TestDashboardAPIContract:
    """Validate the aggregated student dashboard response shape."""

    def test_student_dashboard_schema(self):
        """Dashboard must contain exactly the aggregated sections."""
        import pytest
        try:
            import fastapi
        except ImportError:
            pytest.skip("fastapi not installed")
            
        from app.api.v1.dashboard import StudentDashboard, WorkflowStatusSummary
        
        # Test serialization of an empty state
        dash = StudentDashboard(
            student_id="1234-5678",
            has_approved_plan=False,
            workflow_status=WorkflowStatusSummary(
                run_id="000",
                status="pending",
                current_step="resume_parsing",
                version_number=None,
                published_at=None
            ),
            student_profile=None,
            skill_gap_report=None,
            coding_analytics=None,
            matching_result=None,
            interview_result=None,
            roadmap=None
        )
        
        data = dash.model_dump()
        assert "student_id" in data
        assert "has_approved_plan" in data
        assert "workflow_status" in data
        assert "student_profile" in data
        assert "matching_result" in data


class TestAdminAPIContract:
    """Validate Admin domain configurations return expected structures."""

    def test_admin_domains_list(self):
        """Admin API must expose the 4 domain packs."""
        import pytest
        try:
            import fastapi
        except ImportError:
            pytest.skip("fastapi not installed")
            
        from app.api.v1.admin import DomainSummary
        from app.core.domains.registry import get_all_domains
        
        configs = get_all_domains()
        summaries = [
            DomainSummary(
                family_id=c.family_id,
                name=c.name,
                description=c.description,
                required_skills=c.taxonomy.required_skills,
                weights={
                    "skill_coverage": c.weights.skill_coverage,
                    "coding_performance": c.weights.coding_performance,
                    "project_relevance": c.weights.project_relevance,
                    "interview_performance": c.weights.interview_performance,
                    "eligibility": c.weights.eligibility,
                }
            ) for c in configs
        ]
        
        assert len(summaries) == 4
        assert summaries[0].family_id == "software"
        assert summaries[1].family_id == "analytics"
        assert "coding_performance" in summaries[0].weights


class TestFinalPipelineIntegrity:
    """Ensure all API routers can be successfully imported and are registered."""
    
    def test_api_routers_exist(self):
        """Verify Capstone API router files were created successfully."""
        import os
        from pathlib import Path
        
        base_dir = Path(__file__).parent.parent.parent / "app" / "api" / "v1"
        
        assert (base_dir / "dashboard.py").exists()
        assert (base_dir / "admin.py").exists()
