"""Audit Service — Append-only logging for governance."""
import uuid
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workflow import AuditLog
from app.agents.state import AuditEvent

logger = logging.getLogger(__name__)

async def log_workflow_events(
    db: AsyncSession, 
    workflow_run_id: str, 
    events: List[AuditEvent],
    actor_id: str = "system",
    actor_type: str = "agent"
):
    """
    Writes governed state events sequentially to the un-modifiable audit table.
    Ensures human reviewers can trace exactly *why* an AI made a decision.
    """
    if not events:
        return

    try:
        correlation_id = uuid.uuid4()
        
        for event in events:
            # We strictly enforce that LangGraph state events become physical rows
            log_entry = AuditLog(
                workflow_run_id=uuid.UUID(workflow_run_id) if workflow_run_id else None,
                actor_id=uuid.UUID(actor_id) if actor_id != "system" else None,
                actor_type=actor_type,
                agent_name=event.agent,
                action=event.action,
                details=event.details,
                correlation_id=correlation_id,
                # Convert the ISO string back to datetime
                timestamp=datetime.fromisoformat(event.timestamp) if event.timestamp else datetime.now(timezone.utc)
            )
            db.add(log_entry)
            
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"FATAL: Audit log failed to write. System governance compromised. Error: {str(e)}")
        # In a real system, you might trigger a hard halt or alert to Datadog here.
