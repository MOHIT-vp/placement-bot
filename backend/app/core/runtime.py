"""Governed Runtime Controller — Budgets, Safety Gates, and Checkpoints."""
from typing import Dict, Any, Tuple
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class RuntimeController:
    """
    Governs the execution of the agent graph.
    Prevents runaways, enforces hard LLM token budgets, and verifies conditions.
    """
    def __init__(self, token_budget: int = settings.TOKEN_BUDGET, max_retries: int = settings.MAX_RETRIES):
        self.max_tokens = token_budget
        self.max_retries = max_retries

    def enforce_state_budget(self, state: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if the pipeline has exceeded its allowed run budgets.
        Called between graph nodes.
        Returns: (is_safe_to_continue, reason)
        """
        # 1. Retry Budget (Self-Healing runaways)
        retries = state.get("retry_count", 0)
        if retries >= self.max_retries:
            logger.warning(f"[HALT] Retry budget exhausted ({retries}/{self.max_retries})")
            return False, "RETRY_BUDGET_EXHAUSTED"
            
        # 2. Token Budget (Prevents massive billing on loop failures)
        remaining = state.get("budget_remaining", self.max_tokens)
        if remaining <= 0:
            logger.warning(f"[HALT] Token budget exhausted.")
            return False, "TOKEN_BUDGET_EXHAUSTED"

        # 3. System Error Saturation
        errors = state.get("errors", [])
        if len(errors) > 10:
            logger.warning(f"[HALT] Too many compounding errors (>10).")
            return False, "ERROR_SATURATION"

        return True, "OK"
        
    def check_approval_gate(self, state: Dict[str, Any]) -> str:
        """
        Enforce the human-in-the-loop hard gate rule from the spec.
        """
        approval = state.get("approval_status", "pending")
        if approval == "approved":
            return "publish"
        elif approval == "rejected":
            return "end"
        return "wait"

# Global runtime controller instance
runtime = RuntimeController()
