"""
Lab 11 Acceptance Suite — Evidence Grounding Contracts

Every significant agent output must have a corresponding grounded evidence record.
No output advances to an officer without this gate passing.
"""


REQUIRED_EVIDENCE_ENTITY_TYPES = {
    "student_profile",
    "skill_gap_report",
    "coding_analytics",
    "company_match",
    "interview_preparation",
}

REQUIRED_EVIDENCE_FIELDS = {"entity_type", "evidence_type", "source", "content"}


class TestEvidencePresence:
    """Evidence records must exist for every major output."""

    def test_evidence_records_not_empty(self, complete_valid_state):
        records = complete_valid_state.get("evidence_records", [])
        assert len(records) > 0, "No evidence records found"

    def test_all_required_entity_types_covered(self, complete_valid_state):
        records = complete_valid_state.get("evidence_records", [])
        covered = {r.get("entity_type") for r in records}
        missing = REQUIRED_EVIDENCE_ENTITY_TYPES - covered
        assert not missing, f"Missing evidence for outputs: {missing}"

    def test_each_record_has_required_fields(self, canonical_evidence_records):
        for record in canonical_evidence_records:
            missing = REQUIRED_EVIDENCE_FIELDS - set(record.keys())
            assert not missing, f"Evidence record missing fields: {missing} in {record}"

    def test_content_is_non_empty(self, canonical_evidence_records):
        for record in canonical_evidence_records:
            assert record.get("content", "").strip(), \
                f"Evidence record has empty content: entity={record.get('entity_type')}"

    def test_source_is_agent_name(self, canonical_evidence_records):
        valid_sources = {
            "resume_agent", "skill_gap_agent", "coding_analytics_agent",
            "job_matching_agent", "interview_agent",
        }
        for record in canonical_evidence_records:
            assert record.get("source") in valid_sources, \
                f"Unknown evidence source: {record.get('source')}"


class TestEvidenceSchemaModel:
    """EvidenceRecord Pydantic model must accept canonical evidence."""

    def test_evidence_record_model_validates(self, canonical_evidence_records):
        from app.schemas.evidence import EvidenceRecord
        for raw in canonical_evidence_records:
            # Must not raise
            model = EvidenceRecord(**raw)
            assert model.entity_type == raw["entity_type"]
            assert model.source == raw["source"]

    def test_evidence_record_model_dumps_to_dict(self, canonical_evidence_records):
        from app.schemas.evidence import EvidenceRecord
        for raw in canonical_evidence_records:
            dumped = EvidenceRecord(**raw).model_dump()
            assert isinstance(dumped, dict)
            for field in REQUIRED_EVIDENCE_FIELDS:
                assert field in dumped


class TestValidationAgentEvidenceGate:
    """The ValidationAgent EVIDENCE_PRESENT check must enforce coverage."""

    def test_passes_with_full_evidence(self, complete_valid_state):
        from app.agents.validation_agent import validation_agent_node
        result = validation_agent_node(complete_valid_state)
        report = result.get("validation_report", {})
        ev_check = next(
            (c for c in report.get("checks", []) if c["code"] == "EVIDENCE_PRESENT"), None
        )
        assert ev_check is not None, "EVIDENCE_PRESENT check not run"
        assert ev_check["passed"], f"Evidence check failed: {ev_check['message']}"

    def test_fails_with_no_evidence(self, complete_valid_state):
        from app.agents.validation_agent import validation_agent_node
        bad_state = {**complete_valid_state, "evidence_records": []}
        result = validation_agent_node(bad_state)
        report = result.get("validation_report", {})
        ev_check = next(
            (c for c in report.get("checks", []) if c["code"] == "EVIDENCE_PRESENT"), None
        )
        assert ev_check is not None
        assert not ev_check["passed"], "Should have failed with no evidence"
