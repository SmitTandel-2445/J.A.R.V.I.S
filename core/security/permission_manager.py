"""
Permission & Access Control Policy Manager for J.A.R.V.I.S.
-----------------------------------------------------------
Enforces least-privilege security policies, evaluates action permissions,
and determines when user confirmation is required based on Risk Levels.
"""

from enum import Enum
from typing import Any, Dict, Optional, Tuple
from core.security.action_classifier import RiskLevel


class SecurityPolicyMode(Enum):
    """Operational security policy profiles."""
    STRICT = "STRICT"        # High security: Level 3 and Level 4 require explicit confirmation
    BALANCED = "BALANCED"    # Default: Level 4 always requires confirmation; Level 3 destructive requires confirmation
    PERMISSIVE = "PERMISSIVE"# Testing/Developer: Only Level 4 critical requires confirmation


class PermissionManager:
    """Evaluates whether an action is authorized and if user confirmation is mandatory."""

    def __init__(self, mode: SecurityPolicyMode = SecurityPolicyMode.BALANCED):
        self.mode = mode

    def check_permission(
        self,
        intent_val: str,
        risk_level: RiskLevel,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, bool, str]:
        """
        Evaluates permissions for an intended action.

        :param intent_val: Intent string identifier
        :param risk_level: Evaluated RiskLevel from ActionClassifier
        :param params: Action parameters
        :return: (is_permitted: bool, requires_confirmation: bool, reason: str)
        """
        params = params or {}

        # LEVEL 1 — LOW RISK: Always permitted, never requires confirmation
        if risk_level == RiskLevel.LEVEL_1_LOW:
            return True, False, "Action permitted (Low Risk)."

        # LEVEL 2 — MODERATE RISK: Permitted with argument validation
        if risk_level == RiskLevel.LEVEL_2_MODERATE:
            return True, False, "Action permitted with validation (Moderate Risk)."

        # LEVEL 3 — HIGH RISK
        if risk_level == RiskLevel.LEVEL_3_HIGH:
            if self.mode == SecurityPolicyMode.STRICT:
                return True, True, "Confirmation required by Strict Security Policy for Level 3 action."

            # In Balanced mode: Destructive or system-state altering actions require confirmation
            action = params.get("action", "")
            if intent_val in ("close_app", "system_power") or action in ("kill", "sleep", "create_folder", "latest_download"):
                # System sleep and process termination are destructive/suspensive
                if action in ("sleep", "kill") or intent_val == "close_app" or action == "latest_download":
                    return True, True, f"Confirmation required for high-impact action ({intent_val})."

            return True, False, "Action permitted under Balanced Security Policy."

        # LEVEL 4 — CRITICAL RISK: Always requires explicit confirmation or authorization
        if risk_level == RiskLevel.LEVEL_4_CRITICAL:
            return True, True, "Confirmation mandatory for Critical Risk (Level 4) operation."

        return False, False, f"Action denied: Unrecognized risk level {risk_level}."


# Global default instance
permission_manager = PermissionManager()

