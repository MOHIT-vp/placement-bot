"""API router for retrieving Evidence Grounding records."""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.agents.graph import agent_runner
from app.models.user import User


router = APIRouter(prefix="/evidence", tags=["Evidence"])


class EvidenceResponse(BaseModel):
    run_id: str
    total_records: int
    records: List[Dict[str, Any]]


@router.get("/{run_id}", response_model=EvidenceResponse)
async def get_workflow_evidence(
    run_id: uuid.UUID,
    entity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve evidence records for a specific workflow run.
    Optionally filter by entity_type.
    """
    # Use LangGraph checkpointer to get the state for this thread_id
    config = {"configurable": {"thread_id": str(run_id)}}
    
    try:
        # get_state returns a StateSnapshot object
        state_snapshot = agent_runner.get_state(config)
        
        if not state_snapshot or not state_snapshot.values:
            raise HTTPException(status_code=404, detail="Workflow run state not found or has no state values.")
            
        state_values = state_snapshot.values
        evidence_records = state_values.get("evidence_records", [])
        
        # Filter by entity_type if provided
        if entity_type:
            evidence_records = [
                record for record in evidence_records 
                if record.get("entity_type") == entity_type
            ]
            
        return {
            "run_id": str(run_id),
            "total_records": len(evidence_records),
            "records": evidence_records
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve evidence: {str(e)}")
