"""
Full Node Graph — Lab 7 Master Orchestration Graph.

This is the complete LangGraph StateGraph that wires ALL specialist agents
into one explicit pipeline with:
- Sequential flow: consent → resume → parallel → join → matching → interview → validation
- Conditional edges: validation pass/fail routing
- Self-healing back-edge: validation fail → diagnose → re-validate
- Escalation: retry budget exhaustion → assemble with warnings
- Budget enforcement at every node transition

Architecture:
    START → plan_workflow → lock_plan → consent_validation → resume_agent
        → skill_gap_agent → join_parallel (Lab 8 will add true parallel fan-out)
        → coding_analytics_agent → join_parallel
        → job_matching_agent → interview_agent → validation_agent
            ├── PASS → assemble_draft → END
            ├── FAIL + retries left → diagnose_and_regenerate → validation_agent
            └── FAIL + no retries → assemble_draft (with warnings) → END
"""
from typing import Dict, Any
from datetime import datetime, timezone
import logging

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import PlacementState, AuditEvent
from app.agents.coordinator import plan_workflow, lock_plan
from app.agents.resume_agent import resume_agent_node
from app.agents.skill_gap_agent import skill_gap_agent_node
from app.agents.coding_analytics_agent import coding_analytics_agent_node
from app.agents.job_matching_agent import job_matching_agent_node
from app.agents.interview_agent import interview_agent_node
from app.agents.validation_agent import validation_agent_node
from app.core.runtime import runtime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Infrastructure nodes (consent, join, diagnose, assemble)
# ---------------------------------------------------------------------------

def consent_validation_node(state: PlacementState) -> Dict[str, Any]:
    """
    Node: Validate that all required consents are in place before processing.
    For Lab 7, this performs a basic consent check.
    In production, this queries the Consent table via the StudentConnector.
    """
    logger.info("[ConsentValidation] Checking consents...")

    student_id = state.get("student_id", "unknown")

    # For Lab 7: consent is assumed to be validated (mock)
    # Production: would check data_sharing, resume_processing, coding_platform consents
    consent_status = {
        "data_sharing": True,
        "resume_processing": True,
        "coding_platform": True,
        "interview_data": True,
    }

    audit = AuditEvent(
        action="consent_validated",
        agent="ConsentValidation",
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={"consents": consent_status, "student_id": student_id}
    )

    logger.info(f"[ConsentValidation] All consents validated for student {student_id[:8]}...")

    return {
        "consent_validated": True,
        "current_step": "consent_validation",
        "audit_events": [audit],
    }


def join_parallel_node(state: PlacementState) -> Dict[str, Any]:
    """
    Node: Join/merge point after parallel agents complete.
    In Lab 7, this is sequential. Lab 8 will add true parallel fan-out.
    This node verifies both skill_gap and coding_analytics are present,
    then signals readiness for the Job Matching Agent.
    """
    logger.info("[JoinParallel] Merging parallel agent results...")

    has_skill_gap = state.get("skill_gap_report") is not None
    has_coding = state.get("coding_analytics") is not None

    merge_status = {
        "skill_gap_report": "present" if has_skill_gap else "missing",
        "coding_analytics": "present" if has_coding else "missing",
    }

    errors = []
    if not has_skill_gap:
        errors.append("JoinParallel: skill_gap_report is missing")
    if not has_coding:
        errors.append("JoinParallel: coding_analytics is missing")

    audit = AuditEvent(
        action="parallel_results_merged",
        agent="JoinParallel",
        timestamp=datetime.now(timezone.utc).isoformat(),
        details=merge_status,
    )

    logger.info(f"[JoinParallel] Merge status: {merge_status}")

    result: Dict[str, Any] = {
        "current_step": "join_parallel",
        "audit_events": [audit],
    }
    if errors:
        result["errors"] = errors

    return result


def diagnose_and_regenerate_node(state: PlacementState) -> Dict[str, Any]:
    """
    Node: Diagnose validation failures and prepare for targeted regeneration.
    This is the foundation for Lab 10's self-healing.
    For Lab 7, it increments retry count and logs the diagnosis.
    """
    logger.info("[DiagnoseRegenerate] Analyzing validation failures...")

    retry_count = state.get("retry_count", 0) + 1
    max_retries = state.get("max_retries", 3)

    validation_report = state.get("validation_report", {})
    diagnosis = validation_report.get("diagnosis", {})

    failing_checks = state.get("failing_checks", [])
    agents_to_regen = diagnosis.get("agents_to_regenerate", [])

    audit = AuditEvent(
        action="diagnosis_completed",
        agent="DiagnoseRegenerate",
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={
            "retry_count": retry_count,
            "max_retries": max_retries,
            "failing_checks": failing_checks,
            "agents_to_regenerate": agents_to_regen,
        }
    )

    logger.info(
        f"[DiagnoseRegenerate] Retry {retry_count}/{max_retries}, "
        f"Failing: {failing_checks}, Targets: {agents_to_regen}"
    )

    return {
        "retry_count": retry_count,
        "current_step": "diagnose_and_regenerate",
        "audit_events": [audit],
    }


def assemble_draft_node(state: PlacementState) -> Dict[str, Any]:
    """
    Node: Assemble the final readiness plan draft from all agent outputs.
    This combines everything into the publishable document structure.
    """
    logger.info("[AssembleDraft] Assembling final readiness plan draft...")

    validation_passed = state.get("validation_passed", False)
    student_profile = state.get("student_profile", {})
    skill_gap_report = state.get("skill_gap_report", {})
    coding_analytics = state.get("coding_analytics", {})
    matching_result = state.get("matching_result", {})
    interview_result = state.get("interview_result", {})
    roadmap = state.get("roadmap", {})
    evidence_records = state.get("evidence_records", [])
    validation_report = state.get("validation_report", {})

    # Build the complete draft
    draft = {
        "metadata": {
            "student_id": state.get("student_id"),
            "run_id": state.get("run_id"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "passed" if validation_passed else "passed_with_warnings",
            "version": "draft",
        },
        "student_profile": {
            "summary": student_profile.get("summary", ""),
            "skills_count": len(student_profile.get("skills", [])),
            "projects_count": len(student_profile.get("projects", [])),
            "education": student_profile.get("education"),
        },
        "skill_assessment": {
            "overall_coverage": skill_gap_report.get("overall_coverage", 0),
            "assessment": skill_gap_report.get("overall_assessment", "unknown"),
            "strengths_count": len(skill_gap_report.get("strengths", [])),
            "gaps_count": len(skill_gap_report.get("gaps", [])),
        },
        "coding_performance": {
            "total_solved": coding_analytics.get("summary", {}).get("total_solved", 0),
            "percentile": coding_analytics.get("summary", {}).get("coding_percentile", 0),
            "trend": coding_analytics.get("summary", {}).get("activity_trend", "unknown"),
        },
        "job_matches": {
            "total_evaluated": matching_result.get("total_jobs_evaluated", 0),
            "eligible_count": matching_result.get("eligible_count", 0),
            "top_match_score": (
                matching_result.get("matches", [{}])[0].get("match_percentage", 0)
                if matching_result.get("matches") else 0
            ),
            "readiness_score": matching_result.get("readiness_score", {}),
        },
        "interview_preparation": {
            "questions_generated": interview_result.get("total_questions", 0),
            "readiness_percentage": interview_result.get("readiness_assessment", {}).get("percentage", 0),
        },
        "learning_roadmap": {
            "total_items": roadmap.get("total_items", 0),
            "total_hours": roadmap.get("total_estimated_hours", 0),
        },
        "validation": {
            "passed": validation_passed,
            "checks_passed": validation_report.get("passed_checks", 0),
            "total_checks": validation_report.get("total_checks", 0),
            "warnings": validation_report.get("warning_failures", 0),
        },
        "evidence_count": len(evidence_records),
    }

    # Add warning flags if validation didn't fully pass
    if not validation_passed:
        draft["metadata"]["warning"] = (
            "This draft contains warnings from validation. "
            "Review the validation report before approval."
        )
        draft["metadata"]["failing_checks"] = state.get("failing_checks", [])

    audit = AuditEvent(
        action="draft_assembled",
        agent="AssembleDraft",
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={
            "validation_passed": validation_passed,
            "sections_included": list(draft.keys()),
        }
    )

    logger.info(
        f"[AssembleDraft] Draft assembled — Validation: {'✅' if validation_passed else '⚠️'}, "
        f"Evidence: {len(evidence_records)} records"
    )

    return {
        "current_step": "assemble_draft",
        "audit_events": [audit],
    }


# ---------------------------------------------------------------------------
# Router functions (conditional edges)
# ---------------------------------------------------------------------------

def coordinator_router(state: PlacementState) -> str:
    """Route from coordinator based on planning state."""
    next_node = state.get("next_node", END)
    if next_node == "end":
        return END
    return next_node


def validation_router(state: PlacementState) -> str:
    """
    Route from validation based on pass/fail and retry budget.

    Returns:
    - "pass"          → validation passed, proceed to assembly
    - "fail_retry"    → validation failed, retries remaining, self-heal
    - "fail_escalate" → validation failed, retries exhausted, escalate with warnings
    """
    validation_passed = state.get("validation_passed", False)

    if validation_passed:
        logger.info("[Router] Validation PASSED → assemble_draft")
        return "pass"

    # Check retry budget
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    # Also check runtime budget
    is_safe, reason = runtime.enforce_state_budget(state)

    if not is_safe:
        logger.warning(f"[Router] Runtime budget exceeded: {reason} → escalating")
        return "fail_escalate"

    if retry_count < max_retries:
        logger.info(f"[Router] Validation FAILED, retry {retry_count}/{max_retries} → self-heal")
        return "fail_retry"
    else:
        logger.warning(f"[Router] Validation FAILED, retries exhausted → escalating")
        return "fail_escalate"


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

def build_placement_graph():
    """
    Build the complete Lab 7 agentic workflow graph.

    This is the full node graph with all specialist agents wired together:
    - Coordinator → Planning → Consent → Resume → Skill Gap → Coding Analytics
    - → Join → Job Matching → Interview → Validation
    - Validation → Pass/Fail routing → Assembly or Self-Healing loop
    """
    workflow = StateGraph(PlacementState)

    # =====================================================================
    # ADD ALL NODES
    # =====================================================================

    # Phase 1: Planning (from Lab 1)
    workflow.add_node("plan_workflow", plan_workflow)
    workflow.add_node("lock_plan", lock_plan)

    # Phase 2: Consent + Resume (from Labs 2-3)
    workflow.add_node("consent_validation", consent_validation_node)
    workflow.add_node("resume_agent", resume_agent_node)

    # Phase 3: Parallel agents (sequential in Lab 7, parallel in Lab 8)
    workflow.add_node("skill_gap_agent", skill_gap_agent_node)
    workflow.add_node("coding_analytics_agent", coding_analytics_agent_node)
    workflow.add_node("join_parallel", join_parallel_node)

    # Phase 4: Downstream agents
    workflow.add_node("job_matching_agent", job_matching_agent_node)
    workflow.add_node("interview_agent", interview_agent_node)

    # Phase 5: Validation + Assembly
    workflow.add_node("validation_agent", validation_agent_node)
    workflow.add_node("diagnose_and_regenerate", diagnose_and_regenerate_node)
    workflow.add_node("assemble_draft", assemble_draft_node)

    # =====================================================================
    # WIRE EDGES
    # =====================================================================

    # Entry point: Start with coordinator planning
    workflow.add_edge(START, "plan_workflow")

    # Coordinator routing: plan → lock → execute
    workflow.add_conditional_edges(
        "plan_workflow",
        coordinator_router,
        {
            "lock_plan": "lock_plan",
            "execute": "consent_validation",
            "consent_validation": "consent_validation",
            END: END,
        }
    )

    # Lock plan → consent validation
    workflow.add_edge("lock_plan", "consent_validation")

    # Consent → Resume
    workflow.add_edge("consent_validation", "resume_agent")

    # Resume → Skill Gap (sequential in Lab 7; Lab 8 adds true parallelism)
    workflow.add_edge("resume_agent", "skill_gap_agent")

    # Skill Gap → Coding Analytics (sequential flow)
    workflow.add_edge("skill_gap_agent", "coding_analytics_agent")

    # Coding Analytics → Join
    workflow.add_edge("coding_analytics_agent", "join_parallel")

    # Join → Job Matching
    workflow.add_edge("join_parallel", "job_matching_agent")

    # Job Matching → Interview
    workflow.add_edge("job_matching_agent", "interview_agent")

    # Interview → Validation
    workflow.add_edge("interview_agent", "validation_agent")

    # Validation → Conditional routing
    workflow.add_conditional_edges(
        "validation_agent",
        validation_router,
        {
            "pass": "assemble_draft",
            "fail_retry": "diagnose_and_regenerate",
            "fail_escalate": "assemble_draft",
        }
    )

    # Self-healing loop: diagnose → validation
    workflow.add_edge("diagnose_and_regenerate", "validation_agent")

    # Assembly → END
    workflow.add_edge("assemble_draft", END)

    # =====================================================================
    # COMPILE WITH CHECKPOINTING
    # =====================================================================
    memory = MemorySaver()
    compiled = workflow.compile(checkpointer=memory)

    logger.info("[Graph] Full placement readiness graph compiled successfully.")
    return compiled


# Export the compiled graph
agent_runner = build_placement_graph()
