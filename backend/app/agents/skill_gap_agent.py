"""
Skill Gap Agent (A2) — Compares student skills against target-role requirements.

Architecture Contract:
- Input: student_profile, target role requirements, skill benchmarks
- Output: overall_coverage %, strengths list, gaps list with severity
- Tools: get_role_requirements, get_skill_benchmarks (via connector)
- Constraints: Use approved benchmarks ONLY, cite benchmark source, NEVER declare student 'unfit'
- LLM Usage: Gap analysis narration only
- Deterministic Logic: Gap severity calculation, coverage percentage

This agent is a HYBRID — deterministic scoring + LLM narration.
The LLM NEVER computes scores; it only explains them.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging

from pydantic import BaseModel, Field

from app.config import settings
from app.agents.state import PlacementState, AuditEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas for structured LLM output
# ---------------------------------------------------------------------------

class GapNarration(BaseModel):
    """LLM-generated narration for a single skill gap."""
    skill_name: str = Field(description="The skill being assessed")
    explanation: str = Field(description="Human-readable explanation of the gap")
    learning_suggestion: str = Field(description="Concrete suggestion for closing this gap")


class GapReportNarration(BaseModel):
    """LLM-generated narrations for the full gap report."""
    summary: str = Field(description="2-3 sentence executive summary of the student's position")
    strength_highlights: List[str] = Field(description="Key strength highlights to surface, max 5")
    gap_narrations: List[GapNarration] = Field(description="Narrations for each identified gap")
    overall_assessment: str = Field(
        description="One of: 'strong_candidate', 'competitive', 'developing', 'early_stage'. "
                    "NEVER use 'unfit' or any negative absolute label."
    )


# ---------------------------------------------------------------------------
# Proficiency level hierarchy for deterministic comparison
# ---------------------------------------------------------------------------

PROFICIENCY_LEVELS = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}

SEVERITY_MAP = {
    0: "none",       # Student meets or exceeds requirement
    1: "low",        # One level below requirement
    2: "medium",     # Two levels below requirement
    3: "high",       # Three levels below requirement
    4: "critical",   # Skill completely missing
}


def _proficiency_to_int(level: str) -> int:
    """Convert a proficiency string to an integer for comparison."""
    return PROFICIENCY_LEVELS.get(level.lower().strip(), 0)


def _compute_gap_severity(required_level: str, current_level: Optional[str]) -> str:
    """
    Deterministic severity calculation.
    If the student doesn't have the skill at all, that's 'critical'.
    Otherwise, severity = max(0, required - current).
    """
    if not current_level:
        return "critical"

    required_int = _proficiency_to_int(required_level)
    current_int = _proficiency_to_int(current_level)

    delta = max(0, required_int - current_int)
    return SEVERITY_MAP.get(delta, "critical")


def _compute_skill_coverage(
    student_skills: List[Dict[str, Any]],
    required_skills: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Deterministic skill coverage computation.

    Returns:
        {
            "overall_coverage": float (0-100),
            "strengths": [...],
            "gaps": [...],
            "total_required": int,
            "matched": int,
        }
    """
    if not required_skills:
        return {
            "overall_coverage": 100.0,
            "strengths": [],
            "gaps": [],
            "total_required": 0,
            "matched": 0,
        }

    # Build a lookup map: normalized_skill_name -> proficiency
    student_skill_map = {}
    for skill in student_skills:
        name = skill.get("name", "").strip().lower()
        prof = skill.get("proficiency", "beginner")
        if name:
            student_skill_map[name] = prof

    strengths = []
    gaps = []
    matched = 0

    for req in required_skills:
        req_name = req.get("skill_name", req.get("name", "")).strip().lower()
        req_level = req.get("expected_level", req.get("min_proficiency", "intermediate"))
        importance = req.get("importance", "required")
        source = req.get("source", "system_benchmark")

        student_level = student_skill_map.get(req_name)

        severity = _compute_gap_severity(req_level, student_level)

        entry = {
            "skill": req_name.title(),
            "required_level": req_level,
            "current_level": student_level or "missing",
            "severity": severity,
            "importance": importance,
            "benchmark_source": source,
        }

        if severity == "none":
            matched += 1
            strengths.append({
                "skill": req_name.title(),
                "level": student_level,
                "evidence": f"Matched or exceeded requirement ({req_level}) from {source}",
            })
        else:
            gaps.append(entry)

    total_required = len(required_skills)
    coverage = (matched / total_required * 100) if total_required > 0 else 0.0

    return {
        "overall_coverage": round(coverage, 1),
        "strengths": strengths,
        "gaps": gaps,
        "total_required": total_required,
        "matched": matched,
    }


def _get_mock_role_requirements(target_roles: List[str]) -> List[Dict[str, Any]]:
    """
    Mock role requirements for Lab 7.
    In production, this comes from the RoleConnector → skill_benchmarks table.
    """
    # Default requirements for a "Software Engineer" target role
    default_requirements = [
        {"skill_name": "Python", "expected_level": "intermediate", "importance": "required", "source": "system_benchmark_v1"},
        {"skill_name": "JavaScript", "expected_level": "intermediate", "importance": "required", "source": "system_benchmark_v1"},
        {"skill_name": "React.js", "expected_level": "intermediate", "importance": "preferred", "source": "system_benchmark_v1"},
        {"skill_name": "Node.js", "expected_level": "beginner", "importance": "preferred", "source": "system_benchmark_v1"},
        {"skill_name": "SQL", "expected_level": "intermediate", "importance": "required", "source": "system_benchmark_v1"},
        {"skill_name": "Git", "expected_level": "intermediate", "importance": "required", "source": "system_benchmark_v1"},
        {"skill_name": "Data Structures", "expected_level": "advanced", "importance": "required", "source": "system_benchmark_v1"},
        {"skill_name": "Algorithms", "expected_level": "advanced", "importance": "required", "source": "system_benchmark_v1"},
        {"skill_name": "System Design", "expected_level": "beginner", "importance": "nice_to_have", "source": "system_benchmark_v1"},
        {"skill_name": "Docker", "expected_level": "beginner", "importance": "nice_to_have", "source": "system_benchmark_v1"},
    ]

    return default_requirements


def _get_llm():
    """Get LLM for narration only (lazy import — keeps module importable without LangChain)."""
    from langchain_core.messages import SystemMessage, HumanMessage  # noqa: F401
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        temperature=0.2,
        google_api_key=settings.LLM_API_KEY if settings.LLM_API_KEY else "dummy",
    )


def skill_gap_agent_node(state: PlacementState) -> Dict[str, Any]:
    """
    LangGraph Node: Skill Gap Agent.

    1. Reads student_profile from state (set by Resume Agent)
    2. Fetches role requirements (mock for now)
    3. Runs DETERMINISTIC gap analysis (coverage, severity)
    4. Uses LLM ONLY for narration/explanation of the computed gaps
    5. Returns skill_gap_report to state
    """
    logger.info("[SkillGapAgent] Starting skill gap analysis...")

    student_profile = state.get("student_profile")
    if not student_profile:
        return {
            "errors": ["SkillGapAgent: No student profile available in state."],
            "current_step": "skill_gap_agent",
        }

    target_roles = state.get("target_roles", ["software_engineer"])
    student_skills = student_profile.get("skills", [])

    # ---------- STEP 1: Get role requirements (deterministic) ----------
    role_requirements = _get_mock_role_requirements(target_roles)

    # ---------- STEP 2: Deterministic gap computation ----------
    coverage_result = _compute_skill_coverage(student_skills, role_requirements)

    # ---------- STEP 3: LLM narration (explanation only) ----------
    try:
        llm = _get_llm().with_structured_output(GapReportNarration)

        narration_prompt = f"""
        You are the Skill Gap Agent for a Placement Readiness system.

        CRITICAL RULES:
        1. Use ONLY the data provided below — never invent skills or requirements
        2. NEVER label a student "unfit" — classify using: strong_candidate, competitive, developing, early_stage
        3. Cite the benchmark source for each gap
        4. Be constructive and encouraging while being honest

        STUDENT SKILLS:
        {student_skills}

        ROLE REQUIREMENTS:
        {role_requirements}

        COMPUTED RESULTS (these are GROUND TRUTH — do NOT recalculate):
        - Overall Coverage: {coverage_result['overall_coverage']}%
        - Strengths Found: {len(coverage_result['strengths'])}
        - Gaps Found: {len(coverage_result['gaps'])}
        - Gap Details: {coverage_result['gaps']}

        Generate narrations that EXPLAIN these pre-computed results. Do NOT change any numbers.
        """

        narration: GapReportNarration = llm.invoke([
            SystemMessage(content=narration_prompt),
            HumanMessage(content="Generate the gap report narration based on the computed data above.")
        ])

        # Merge deterministic results with LLM narration
        narration_map = {n.skill_name.lower(): n for n in narration.gap_narrations}
        for gap in coverage_result["gaps"]:
            skill_key = gap["skill"].lower()
            if skill_key in narration_map:
                gap["recommendation"] = narration_map[skill_key].learning_suggestion
                gap["explanation"] = narration_map[skill_key].explanation
            else:
                gap["recommendation"] = f"Study {gap['skill']} to reach {gap['required_level']} level."
                gap["explanation"] = f"Gap detected: current={gap['current_level']}, required={gap['required_level']}"

        summary = narration.summary
        overall_assessment = narration.overall_assessment
        strength_highlights = narration.strength_highlights

    except Exception as e:
        logger.warning(f"[SkillGapAgent] LLM narration failed, using fallback: {e}")
        # Fallback: Still return deterministic results even if LLM fails
        summary = f"Student has {coverage_result['overall_coverage']}% skill coverage against target role requirements."
        overall_assessment = (
            "strong_candidate" if coverage_result["overall_coverage"] >= 80
            else "competitive" if coverage_result["overall_coverage"] >= 60
            else "developing" if coverage_result["overall_coverage"] >= 40
            else "early_stage"
        )
        strength_highlights = [s["skill"] for s in coverage_result["strengths"][:5]]
        for gap in coverage_result["gaps"]:
            gap["recommendation"] = f"Study {gap['skill']} to reach {gap['required_level']} level."
            gap["explanation"] = f"Gap: current={gap['current_level']}, required={gap['required_level']}"

    # ---------- STEP 4: Assemble final report ----------
    skill_gap_report = {
        "overall_coverage": coverage_result["overall_coverage"],
        "total_required_skills": coverage_result["total_required"],
        "matched_skills": coverage_result["matched"],
        "overall_assessment": overall_assessment,
        "summary": summary,
        "strength_highlights": strength_highlights,
        "strengths": coverage_result["strengths"],
        "gaps": coverage_result["gaps"],
        "target_roles": target_roles,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    # ---------- STEP 5: Evidence record ----------
    from app.schemas.evidence import EvidenceRecord
    evidence = EvidenceRecord(
        entity_type="skill_gap_report",
        evidence_type="deterministic_computation",
        source="skill_gap_agent",
        content=f"Coverage: {coverage_result['overall_coverage']}%, "
                   f"Gaps: {len(coverage_result['gaps'])}, "
                   f"Strengths: {len(coverage_result['strengths'])}",
        scope_tags=["skill_gap", "benchmarks"],
    ).model_dump()

    audit = AuditEvent(
        action="skill_gap_analyzed",
        agent="SkillGapAgent",
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={
            "coverage": coverage_result["overall_coverage"],
            "gaps_count": len(coverage_result["gaps"]),
            "strengths_count": len(coverage_result["strengths"]),
            "assessment": overall_assessment,
        }
    )

    logger.info(
        f"[SkillGapAgent] Complete — Coverage: {coverage_result['overall_coverage']}%, "
        f"Gaps: {len(coverage_result['gaps'])}, Strengths: {len(coverage_result['strengths'])}"
    )

    return {
        "skill_gap_report": skill_gap_report,
        "evidence_records": [evidence],
        "audit_events": [audit],
        "current_step": "skill_gap_agent",
    }
