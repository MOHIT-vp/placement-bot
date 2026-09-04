"""
Coding Analytics Agent (A3) — Aggregates coding platform data into structured analytics.

Architecture Contract:
- Input: student_id, platform data (from connector), consent status
- Output: summary stats, topic analysis, difficulty distribution, activity trend, recommendations
- Tools: get_coding_analytics (via connector)
- Constraints: Consent required, never expose raw private submissions, surface aggregated trends only
- LLM Usage: Trend analysis narration only
- Deterministic Logic: Statistical aggregation, percentile calculation

This agent is HYBRID — deterministic aggregation + LLM trend narration.
The LLM does NOT compute statistics; it only interprets them.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import math
import logging

from pydantic import BaseModel, Field

from app.config import settings
from app.agents.state import PlacementState, AuditEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas for structured LLM output
# ---------------------------------------------------------------------------

class TopicInsight(BaseModel):
    """LLM-generated insight for a coding topic."""
    topic: str
    assessment: str = Field(description="Brief assessment of the student's ability in this topic")
    priority: str = Field(description="One of: 'focus_area', 'maintain', 'strength'. Based on the data provided.")


class CodingNarration(BaseModel):
    """LLM-generated narration of the coding analytics."""
    overall_assessment: str = Field(description="2-3 sentence summary of coding ability")
    trend_analysis: str = Field(description="Analysis of whether student is improving, stable, or declining")
    key_strengths: List[str] = Field(description="Top 3 coding strengths based on the data")
    improvement_areas: List[str] = Field(description="Top 3 areas needing improvement")
    topic_insights: List[TopicInsight] = Field(description="Per-topic insights")
    recommendations: List[str] = Field(description="3-5 actionable recommendations")


# ---------------------------------------------------------------------------
# Mock coding platform data (Lab 7 — will be replaced by real connectors)
# ---------------------------------------------------------------------------

def _get_mock_platform_data(student_id: str) -> Dict[str, Any]:
    """
    Returns mock coding platform data.
    In production, this comes from the CodingConnector → coding_analytics table
    or external platform APIs (LeetCode, Codeforces, HackerRank).
    """
    return {
        "platform": "LeetCode",
        "username": f"student_{student_id[:8]}",
        "total_problems_solved": 187,
        "difficulty_distribution": {
            "easy": 82,
            "medium": 78,
            "hard": 27,
        },
        "contest_participation": {
            "total_contests": 14,
            "best_rating": 1623,
            "current_rating": 1547,
            "global_ranking_percentile": 72.3,
        },
        "topic_breakdown": [
            {"topic": "Arrays", "solved": 34, "total_attempted": 38, "accuracy": 89.5},
            {"topic": "Strings", "solved": 22, "total_attempted": 25, "accuracy": 88.0},
            {"topic": "Dynamic Programming", "solved": 18, "total_attempted": 28, "accuracy": 64.3},
            {"topic": "Trees", "solved": 21, "total_attempted": 24, "accuracy": 87.5},
            {"topic": "Graphs", "solved": 14, "total_attempted": 22, "accuracy": 63.6},
            {"topic": "Binary Search", "solved": 15, "total_attempted": 17, "accuracy": 88.2},
            {"topic": "Linked Lists", "solved": 12, "total_attempted": 13, "accuracy": 92.3},
            {"topic": "Stack/Queue", "solved": 16, "total_attempted": 18, "accuracy": 88.9},
            {"topic": "Sorting", "solved": 11, "total_attempted": 12, "accuracy": 91.7},
            {"topic": "Recursion/Backtracking", "solved": 10, "total_attempted": 15, "accuracy": 66.7},
            {"topic": "Greedy", "solved": 8, "total_attempted": 10, "accuracy": 80.0},
            {"topic": "Math", "solved": 6, "total_attempted": 8, "accuracy": 75.0},
        ],
        "monthly_activity": [
            {"month": "2026-03", "problems_solved": 12, "contests": 1},
            {"month": "2026-04", "problems_solved": 18, "contests": 2},
            {"month": "2026-05", "problems_solved": 24, "contests": 2},
            {"month": "2026-06", "problems_solved": 28, "contests": 3},
            {"month": "2026-07", "problems_solved": 32, "contests": 3},
            {"month": "2026-08", "problems_solved": 21, "contests": 1},
        ],
        "languages_used": {
            "Python": 65,
            "C++": 22,
            "Java": 13,
        },
        "streak_days": 28,
        "last_submission_date": "2026-08-24",
    }


# ---------------------------------------------------------------------------
# Deterministic computation functions
# ---------------------------------------------------------------------------

def _compute_difficulty_score(distribution: Dict[str, int]) -> float:
    """
    Compute a weighted difficulty score (0-100).
    Easy=1x, Medium=2x, Hard=4x weight.
    """
    easy = distribution.get("easy", 0)
    medium = distribution.get("medium", 0)
    hard = distribution.get("hard", 0)
    total = easy + medium + hard

    if total == 0:
        return 0.0

    weighted = (easy * 1) + (medium * 2) + (hard * 4)
    max_possible = total * 4  # If all were hard
    return round((weighted / max_possible) * 100, 1)


def _compute_activity_trend(monthly_data: List[Dict[str, Any]]) -> str:
    """
    Deterministic trend detection using simple linear regression slope.
    Returns: 'improving', 'stable', or 'declining'
    """
    if len(monthly_data) < 3:
        return "insufficient_data"

    # Use last 6 months of data
    recent = monthly_data[-6:]
    n = len(recent)
    problems = [m.get("problems_solved", 0) for m in recent]

    # Simple linear regression slope
    x_mean = (n - 1) / 2
    y_mean = sum(problems) / n

    numerator = sum((i - x_mean) * (problems[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return "stable"

    slope = numerator / denominator

    # Threshold: ±2 problems/month change is "stable"
    if slope > 2:
        return "improving"
    elif slope < -2:
        return "declining"
    else:
        return "stable"


def _compute_topic_strengths(topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministic topic strength classification.
    Uses combination of volume (solved count) and accuracy.
    """
    results = []
    for topic in topics:
        solved = topic.get("solved", 0)
        accuracy = topic.get("accuracy", 0)

        # Strength score = sqrt(solved) * (accuracy/100)
        # This rewards both volume and accuracy
        strength_score = round(math.sqrt(solved) * (accuracy / 100), 2)

        if accuracy >= 85 and solved >= 15:
            strength_level = "strong"
        elif accuracy >= 75 and solved >= 10:
            strength_level = "competent"
        elif accuracy >= 60 and solved >= 5:
            strength_level = "developing"
        else:
            strength_level = "needs_work"

        results.append({
            "topic": topic["topic"],
            "solved": solved,
            "total_attempted": topic.get("total_attempted", solved),
            "accuracy": accuracy,
            "strength_score": strength_score,
            "strength_level": strength_level,
        })

    # Sort by strength score descending
    results.sort(key=lambda x: x["strength_score"], reverse=True)
    return results


def _compute_percentile_estimate(
    total_solved: int,
    contest_rating: int,
    difficulty_score: float,
) -> float:
    """
    Estimate an overall coding percentile (0-100).
    This is a simplified model — production would use real platform percentiles.
    """
    # Weighted combination
    volume_factor = min(total_solved / 500, 1.0) * 30       # Max 30 pts for volume
    rating_factor = min(contest_rating / 2500, 1.0) * 40    # Max 40 pts for rating
    difficulty_factor = (difficulty_score / 100) * 30         # Max 30 pts for difficulty mix

    return round(volume_factor + rating_factor + difficulty_factor, 1)


def _get_llm():
    """Get LLM for narration only."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        temperature=0.3,
        google_api_key=settings.LLM_API_KEY if settings.LLM_API_KEY else "dummy",
    )


# ---------------------------------------------------------------------------
# Main Agent Node
# ---------------------------------------------------------------------------

def coding_analytics_agent_node(state: PlacementState) -> Dict[str, Any]:
    """
    LangGraph Node: Coding Analytics Agent.

    1. Checks consent for coding_platform data access
    2. Fetches platform data via connector (mock for Lab 7)
    3. Runs DETERMINISTIC statistical aggregation
    4. Uses LLM ONLY for trend narration and recommendations
    5. Returns coding_analytics to state
    """
    logger.info("[CodingAnalyticsAgent] Starting coding analytics aggregation...")

    # ---------- STEP 1: Consent verification ----------
    if not state.get("consent_validated", False):
        return {
            "errors": ["CodingAnalyticsAgent: Consent not validated. Cannot access coding data."],
            "current_step": "coding_analytics_agent",
        }

    student_id = state.get("student_id", "unknown")

    # ---------- STEP 2: Fetch platform data ----------
    platform_data = _get_mock_platform_data(student_id)

    # ---------- STEP 3: Deterministic computations ----------
    difficulty_distribution = platform_data.get("difficulty_distribution", {})
    difficulty_score = _compute_difficulty_score(difficulty_distribution)

    monthly_activity = platform_data.get("monthly_activity", [])
    activity_trend = _compute_activity_trend(monthly_activity)

    topic_analysis = _compute_topic_strengths(platform_data.get("topic_breakdown", []))

    contest = platform_data.get("contest_participation", {})
    percentile = _compute_percentile_estimate(
        total_solved=platform_data.get("total_problems_solved", 0),
        contest_rating=contest.get("current_rating", 0),
        difficulty_score=difficulty_score,
    )

    summary_stats = {
        "total_solved": platform_data.get("total_problems_solved", 0),
        "difficulty_distribution": difficulty_distribution,
        "difficulty_score": difficulty_score,
        "contest_rating": contest.get("current_rating", 0),
        "best_rating": contest.get("best_rating", 0),
        "contest_count": contest.get("total_contests", 0),
        "global_ranking_percentile": contest.get("global_ranking_percentile", 0),
        "activity_trend": activity_trend,
        "coding_percentile": percentile,
        "streak_days": platform_data.get("streak_days", 0),
        "primary_language": max(
            platform_data.get("languages_used", {"Unknown": 1}).items(),
            key=lambda x: x[1]
        )[0],
    }

    # ---------- STEP 4: LLM narration ----------
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        llm = _get_llm().with_structured_output(CodingNarration)

        topic_summary = [
            {"topic": t["topic"], "solved": t["solved"], "accuracy": t["accuracy"], "level": t["strength_level"]}
            for t in topic_analysis
        ]

        narration_prompt = f"""
        You are the Coding Analytics Agent for a Placement Readiness system.

        CRITICAL RULES:
        1. Use ONLY the data provided below — never invent statistics
        2. Keep raw submission data PRIVATE — only discuss trends and aggregates
        3. Be constructive — identify both strengths AND improvement areas
        4. Recommendations must be specific and actionable

        COMPUTED STATISTICS (GROUND TRUTH — do NOT recalculate):
        - Total Problems Solved: {summary_stats['total_solved']}
        - Difficulty Score: {difficulty_score}/100
        - Contest Rating: {summary_stats['contest_rating']} (Best: {summary_stats['best_rating']})
        - Activity Trend: {activity_trend}
        - Coding Percentile Estimate: {percentile}%
        - Primary Language: {summary_stats['primary_language']}
        - Current Streak: {summary_stats['streak_days']} days

        TOPIC ANALYSIS (sorted by strength):
        {topic_summary}

        MONTHLY ACTIVITY:
        {monthly_activity}

        Generate insights that EXPLAIN these pre-computed results.
        """

        narration: CodingNarration = llm.invoke([
            SystemMessage(content=narration_prompt),
            HumanMessage(content="Generate the coding analytics narration based on the computed data above.")
        ])

        narration_data = {
            "overall_assessment": narration.overall_assessment,
            "trend_analysis": narration.trend_analysis,
            "key_strengths": narration.key_strengths,
            "improvement_areas": narration.improvement_areas,
            "recommendations": narration.recommendations,
        }

    except Exception as e:
        logger.warning(f"[CodingAnalyticsAgent] LLM narration failed, using fallback: {e}")
        # Deterministic fallback
        strong_topics = [t["topic"] for t in topic_analysis if t["strength_level"] == "strong"]
        weak_topics = [t["topic"] for t in topic_analysis if t["strength_level"] in ("needs_work", "developing")]

        narration_data = {
            "overall_assessment": f"Student has solved {summary_stats['total_solved']} problems "
                                  f"with a {activity_trend} trend. Coding percentile: {percentile}%.",
            "trend_analysis": f"Activity trend is {activity_trend} over the last 6 months.",
            "key_strengths": strong_topics[:3] if strong_topics else ["Consistent problem-solving activity"],
            "improvement_areas": weak_topics[:3] if weak_topics else ["Increase hard problem attempts"],
            "recommendations": [
                f"Focus on {weak_topics[0]} problems" if weak_topics else "Maintain current pace",
                "Increase contest participation for rating improvement",
                "Attempt more Hard difficulty problems",
            ],
        }

    # ---------- STEP 5: Assemble final report ----------
    coding_analytics = {
        "summary": summary_stats,
        "topic_analysis": topic_analysis,
        "narration": narration_data,
        "platform": platform_data.get("platform", "unknown"),
        "monthly_activity": monthly_activity,
        "languages_used": platform_data.get("languages_used", {}),
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    # ---------- STEP 6: Evidence record ----------
    from app.schemas.evidence import EvidenceRecord
    evidence = EvidenceRecord(
        entity_type="coding_analytics",
        evidence_type="platform_aggregation",
        source="coding_analytics_agent",
        content=f"Platform: {platform_data.get('platform')}, "
                   f"Total Solved: {summary_stats['total_solved']}, "
                   f"Rating: {summary_stats['contest_rating']}, "
                   f"Percentile: {percentile}%",
        scope_tags=["coding", "analytics", "platform_data"],
    ).model_dump()

    audit = AuditEvent(
        action="coding_analytics_computed",
        agent="CodingAnalyticsAgent",
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={
            "total_solved": summary_stats["total_solved"],
            "difficulty_score": difficulty_score,
            "activity_trend": activity_trend,
            "percentile": percentile,
        }
    )

    logger.info(
        f"[CodingAnalyticsAgent] Complete — Solved: {summary_stats['total_solved']}, "
        f"Rating: {summary_stats['contest_rating']}, Trend: {activity_trend}"
    )

    return {
        "coding_analytics": coding_analytics,
        "evidence_records": [evidence],
        "audit_events": [audit],
        "current_step": "coding_analytics_agent",
    }
