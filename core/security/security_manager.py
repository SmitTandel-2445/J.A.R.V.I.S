"""
Central Security Manager Module for J.A.R.V.I.S.
-------------------------------------------------
Orchestrates the complete security boundary for J.A.R.V.I.S. desktop operations.
Intercepts all incoming user commands, validates arguments, enforces path boundaries,
classifies risk levels (1-4), triggers confirmation gates, and writes to the audit log.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from core.security.action_classifier import ActionClassifier, RiskLevel
from core.security.audit_logger import AuditLogger, audit_logger as default_audit
from core.security.command_validator import CommandValidator
from core.security.confirmation_manager import ConfirmationManager, confirmation_manager as default_confirm
from core.security.file_access_guard import FileAccessGuard, file_access_guard as default_guard
from core.security.permission_manager import PermissionManager, permission_manager as default_perms
from core.security.tool_registry import ToolRegistry, tool_registry as default_tools
from utils.logger import logger


@dataclass
class SecurityDecision:
    """Represents the outcome of a security inspection on an intended action."""
    allowed: bool
    risk_level: RiskLevel
    requires_confirmation: bool = False
    confirmation_prompt: str = ""
    reason: str = ""
    sanitized_params: Dict[str, Any] = field(default_factory=dict)


class SecurityManager:
    """Central gateway enforcing security policies, validation, and confirmation across all actions."""

    def __init__(
        self,
        classifier: Optional[ActionClassifier] = None,
        validator: Optional[CommandValidator] = None,
        guard: Optional[FileAccessGuard] = None,
        permission_mgr: Optional[PermissionManager] = None,
        confirm_mgr: Optional[ConfirmationManager] = None,
        tools: Optional[ToolRegistry] = None,
        auditor: Optional[AuditLogger] = None,
    ):
        self.classifier = classifier or ActionClassifier
        self.validator = validator or CommandValidator
        self.guard = guard or default_guard
        self.permission_mgr = permission_mgr or default_perms
        self.confirm_mgr = confirm_mgr or default_confirm
        self.tools = tools or default_tools
        self.auditor = auditor or default_audit

    def evaluate(
        self,
        intent_val: str,
        parameters: Optional[Dict[str, Any]] = None,
        raw_text: str = "",
    ) -> SecurityDecision:
        """
        Performs comprehensive pre-execution security evaluation.

        :param intent_val: Intent type identifier (e.g. 'file_folder', 'open_app', 'close_app')
        :param parameters: Intent parameters dict
        :param raw_text: Raw query text
        :return: SecurityDecision
        """
        params = dict(parameters or {})
        sanitized_query = self.validator.sanitize_input(raw_text)

        # 1. Base Command String Validation
        is_valid_cmd, cmd_err = self.validator.validate_command_string(sanitized_query or intent_val)
        if not is_valid_cmd:
            self.auditor.log_blocked(intent=intent_val, reason=cmd_err, query=sanitized_query)
            logger.warning(f"SecurityManager blocked command: {cmd_err}")
            return SecurityDecision(
                allowed=False,
                risk_level=RiskLevel.LEVEL_4_CRITICAL,
                reason=cmd_err,
            )

        # 2. Domain-Specific Parameter Validation
        # 2.1 Process Terminations (close_app, task_manager kill)
        if intent_val in ("close_app", "task_manager"):
            target_proc = params.get("app_name") or params.get("target")
            if target_proc and (intent_val == "close_app" or params.get("action") == "kill"):
                valid_proc, canon_proc, proc_err = self.validator.validate_process_target(str(target_proc))
                if not valid_proc:
                    self.auditor.log_blocked(intent=intent_val, reason=proc_err, query=sanitized_query)
                    logger.warning(f"SecurityManager blocked process operation: {proc_err}")
                    return SecurityDecision(
                        allowed=False,
                        risk_level=RiskLevel.LEVEL_4_CRITICAL,
                        reason=proc_err,
                    )
                # Store normalized process name
                if "app_name" in params:
                    params["app_name"] = canon_proc
                if "target" in params:
                    params["target"] = canon_proc

        # 2.2 Folder Creation (Path Traversal Guard)
        if intent_val == "file_folder" and params.get("action") == "create_folder":
            folder_name = params.get("folder_name", "")
            desktop_dir = self.guard.user_home / "Desktop"
            valid_folder, canon_path, folder_err = self.guard.validate_folder_creation(desktop_dir, str(folder_name))
            if not valid_folder:
                self.auditor.log_blocked(intent=intent_val, reason=folder_err, query=sanitized_query)
                logger.warning(f"SecurityManager blocked folder creation: {folder_err}")
                return SecurityDecision(
                    allowed=False,
                    risk_level=RiskLevel.LEVEL_3_HIGH,
                    reason=folder_err,
                )
            params["canonical_path"] = canon_path

        # 2.3 URL Validation
        if intent_val == "browser_tab" and params.get("action") == "navigate":
            target_url = params.get("url", "")
            valid_url, url_err = self.validator.validate_url(target_url)
            if not valid_url:
                self.auditor.log_blocked(intent=intent_val, reason=url_err, query=sanitized_query)
                logger.warning(f"SecurityManager blocked URL navigation: {url_err}")
                return SecurityDecision(
                    allowed=False,
                    risk_level=RiskLevel.LEVEL_3_HIGH,
                    reason=url_err,
                )

        # 3. Risk Level Classification
        risk_level, risk_reason = self.classifier.classify(intent_val, params)

        # 4. Permission Check & Confirmation Requirement
        is_permitted, requires_confirm, perm_reason = self.permission_mgr.check_permission(intent_val, risk_level, params)

        if not is_permitted:
            self.auditor.log_blocked(intent=intent_val, reason=perm_reason, query=sanitized_query)
            return SecurityDecision(
                allowed=False,
                risk_level=risk_level,
                reason=perm_reason,
            )

        # 5. Formulate Confirmation Prompt if Required
        prompt = ""
        if requires_confirm:
            prompt = self._build_confirmation_prompt(intent_val, params, risk_level)
            self.auditor.log_confirmation_requested(intent=intent_val, risk_level=str(risk_level), prompt=prompt)

        # 6. Audit Successful Evaluation
        self.auditor.log_decision(
            event="ACTION_EVALUATED",
            intent=intent_val,
            risk_level=str(risk_level),
            status="PENDING_CONFIRMATION" if requires_confirm else "ALLOWED",
            details=params,
            query=sanitized_query,
        )

        return SecurityDecision(
            allowed=True,
            risk_level=risk_level,
            requires_confirmation=requires_confirm,
            confirmation_prompt=prompt,
            reason=risk_reason,
            sanitized_params=params,
        )

    def _build_confirmation_prompt(self, intent_val: str, params: Dict[str, Any], risk_level: RiskLevel) -> str:
        """Constructs an articulate, natural-language confirmation query for J.A.R.V.I.S."""
        if intent_val == "file_folder" and params.get("action") == "empty_recycle_bin":
            return "This will permanently delete all files currently in your Recycle Bin, sir. Are you sure you wish to proceed?"

        if intent_val == "system_power":
            action = params.get("action", "")
            if action == "sleep":
                return "Putting your computer to sleep will suspend active work. Shall I proceed into sleep mode, sir?"
            if action in ("shutdown", "restart"):
                return f"Initiating system {action} will close all active applications. Please confirm to proceed, sir."

        if intent_val == "close_app":
            target = params.get("app_name", "the application")
            return f"Closing {target} will terminate running instances. Are you sure you want me to close it, sir?"

        if intent_val == "task_manager" and params.get("action") == "kill":
            target = params.get("target", "the process")
            return f"Terminating process {target} may cause unsaved data loss. Do you confirm this termination, sir?"

        if intent_val == "file_folder" and params.get("action") == "latest_download":
            return "Opening recently downloaded files carries potential security risks. Do you wish to open your latest download, sir?"

        return f"This action carries elevated system impact ({risk_level.label}). Do you wish to proceed, sir?"

    def handle_user_response(self, text: str) -> Tuple[bool, bool, str, Optional[Dict[str, Any]]]:
        """
        Intercepts speech when a confirmation is pending to see if the user confirmed or cancelled.
        :return: (is_handled: bool, success: bool, spoken_response: str, action_data: Optional[dict])
        """
        if not self.confirm_mgr.has_pending():
            return False, False, "", None

        handled, ok, speech, data = self.confirm_mgr.evaluate_response(text)
        if handled:
            intent = data.get("intent", "UNKNOWN") if data else "UNKNOWN"
            status = data.get("status", "") if data else ""
            self.auditor.log_confirmation_outcome(intent, confirmed=(status == "CONFIRMED"))
        return handled, ok, speech, data


# Global default instance
security_manager = SecurityManager()

