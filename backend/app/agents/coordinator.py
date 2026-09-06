from typing import Dict, Any
from datetime import datetime, timezone
import json

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from app.config import settings
from app.agents.state import PlacementState, ExecutionPlan, ExecutionStep, AuditEvent


def get_llm():
    """Get the configured LLM for orchestration."""
    # We will use Gemini based on settings
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        temperature=0.1,  # Low temperature for orchestration/planning
        google_api_key=settings.LLM_API_KEY if settings.LLM_API_KEY else "dummy",
    )


def plan_workflow(state: PlacementState) -> Dict[str, Any]:
    """
    Node: Create or revise the execution plan.
    """
    # If a plan is already locked, this node shouldn't modify it
    if state.get("plan_locked", False):
        return {"current_step": "plan_workflow", "next_node": "execute"}

    llm = get_llm().with_structured_output(ExecutionPlan)
    
    prompt = f"""
    You are the Coordinator for the Placement Readiness & Career Intelligence Portal.
    Your task is to create a deterministic Execution Plan for the student based on this context.
    
    Student Request Context: {state.get('request_context', 'Standard Full Placement Pipeline')}
    Target Roles: {state.get('target_roles', [])}
    
    Standard Flow:
    1. Consent Validation (Rule: Consent must be checked first)
    2. Resume Agent (Rule: Parse structured file)
    3. Parallel: Skill Gap Agent & Coding Analytics Agent
    4. Job Matching Agent (Requires Skill Gap and Coding passing)
    5. Interview Agent (Requires Job Matching to finish)
    6. Validation Agent (Rule: Must validate everything)
    
    Review any existing plan errors: {state.get('errors', [])}
    """
    
    try:
        new_plan: ExecutionPlan = llm.invoke([
            SystemMessage(content=prompt),
            HumanMessage(content="Generate the execution plan.")
        ])
        
        # Log the event
        audit_event = AuditEvent(
            action="plan_generated",
            agent="Coordinator",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={"steps_count": len(new_plan.steps)}
        )
        
        return {
            "plan": new_plan,
            "audit_events": [audit_event],
            "current_step": "plan_workflow",
            "next_node": "lock_plan"
        }
    except Exception as e:
        print(f"Planning error: {e}. Falling back to mock plan.")
        mock_plan = ExecutionPlan(
            goal_summary="Standard Placement Pipeline (Mock Fallback)",
            steps=[
                ExecutionStep(step_id="1", agent="ConsentValidation", description="Validate consent", requires_input_from=[]),
                ExecutionStep(step_id="2", agent="ResumeAgent", description="Parse resume", requires_input_from=["1"]),
                ExecutionStep(step_id="3", agent="SkillGapAgent", description="Skill gap analysis", requires_input_from=["2"]),
                ExecutionStep(step_id="4", agent="CodingAnalyticsAgent", description="Coding stats", requires_input_from=["2"]),
                ExecutionStep(step_id="5", agent="JobMatchingAgent", description="Match jobs", requires_input_from=["3", "4"]),
                ExecutionStep(step_id="6", agent="InterviewAgent", description="Interview prep", requires_input_from=["5"]),
                ExecutionStep(step_id="7", agent="ValidationAgent", description="Validate readiness", requires_input_from=["6"]),
            ]
        )
        return {
            "plan": mock_plan,
            "errors": [f"Planning error: {str(e)} - used fallback"],
            "current_step": "plan_workflow",
            "next_node": "lock_plan"
        }

def lock_plan(state: PlacementState) -> Dict[str, Any]:
    """
    Node: Lock the plan before execution. 
    A locked plan cannot be mutated further to guarantee determinism.
    """
    plan = state.get("plan")
    if not plan:
        return {"errors": ["Attempted to lock an empty plan"], "next_node": "end"}
        
    plan.is_locked = True
    
    audit_event = AuditEvent(
        action="plan_locked",
        agent="Coordinator",
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={"locked": True}
    )
    
    return {
        "plan": plan, 
        "plan_locked": True, 
        "audit_events": [audit_event],
        "current_step": "lock_plan",
        "next_node": "consent_validation" # Real pipeline entrypoint
    }
