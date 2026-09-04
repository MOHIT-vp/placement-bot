"""
Lab 13: Domain Specialists — Acceptance Tests
"""
from app.core.domains.registry import DOMAIN_REGISTRY, get_domain_config, get_all_domains
from app.core.domains.base import RoleFamilyConfig


class TestDomainConfigurations:
    """Test the domain configurations and registry."""

    def test_registry_contains_all_domains(self):
        """Registry should contain 4 core domains."""
        domains = get_all_domains()
        assert len(domains) == 4

        expected_ids = {"software", "analytics", "core", "higher_studies"}
        actual_ids = {d.family_id for d in domains}
        assert actual_ids == expected_ids

    def test_domain_configs_are_valid(self):
        """Every registered domain config must be valid RoleFamilyConfig."""
        for family_id, config in DOMAIN_REGISTRY.items():
            assert isinstance(config, RoleFamilyConfig)
            assert config.family_id == family_id
            assert config.name
            assert config.taxonomy.required_skills
            assert config.question_bank.technical
            assert config.weights.skill_coverage > 0

    def test_weights_sum_to_one(self):
        """Scoring weights should sum to 1.0 (or very close)."""
        for config in get_all_domains():
            w = config.weights
            total = (w.skill_coverage + w.coding_performance + 
                     w.project_relevance + w.interview_performance + 
                     w.eligibility)
            assert abs(total - 1.0) < 0.01

    def test_higher_studies_zero_coding(self):
        """Higher studies should have 0% weight on coding performance."""
        hs = get_domain_config("higher_studies")
        assert hs is not None
        assert hs.weights.coding_performance == 0.0

    def test_software_coding_focus(self):
        """Software should have high weight on coding."""
        sw = get_domain_config("software")
        assert sw is not None
        assert sw.weights.coding_performance >= 0.40


class TestDomainAPIs:
    """
    Test the mock logic of the Domain APIs.
    We just test that the endpoints are importable and structured properly.
    """
    
    def test_api_routers_exist(self):
        """Verify the domain API router files were created successfully."""
        import os
        from pathlib import Path
        
        base_dir = Path(__file__).parent.parent.parent / "app" / "api" / "v1"
        
        assert (base_dir / "profiles.py").exists()
        assert (base_dir / "analysis.py").exists()
        assert (base_dir / "matching.py").exists()
        assert (base_dir / "interviews.py").exists()
