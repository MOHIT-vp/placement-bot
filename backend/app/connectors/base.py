"""Base connector interface for governed data access."""
from typing import Any, Dict, List, Optional
import uuid
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ConnectorError(Exception):
    """Base exception for all connector-related errors."""
    pass

class DataAccessDeniedError(ConnectorError):
    """Raised when an agent attempts to access un-consented or out-of-scope data."""
    pass

class BaseConnector:
    """
    The Base Connector ensures that all data fetching is:
    1. Typed (Returns Pydantic schemas, not raw dicts or ORM models)
    2. Governed (Will eventually hook into audit logs)
    3. Isolated (Agents cannot arbitrary query the DB)
    """
    def __init__(self, db: AsyncSession, actor_id: str = "system"):
        self.db = db
        self.actor_id = actor_id  # Used for audit logging

    # Utility for executing and wrapping DB errors securely
    async def safe_execute(self, query):
        try:
            return await self.db.execute(query)
        except Exception as e:
            logger.error(f"Database error in connector: {str(e)}")
            raise ConnectorError(f"Secure data access failed.")
