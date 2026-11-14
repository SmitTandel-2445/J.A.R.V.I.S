"""
J.A.R.V.I.S. Security Architecture Package
-------------------------------------------
Exports centralized security components:
- SecurityManager: Primary enforcement orchestrator
- ActionClassifier, RiskLevel: 4-tier action risk categorizer
- CommandValidator: Shell injection and process target validator
- FileAccessGuard: File system sandbox and directory traversal protection
- ConfirmationManager: Two-step confirmation gate for destructive actions
- PermissionManager, SecurityPolicyMode: Access control policy manager
- ToolRegistry, ToolType, ToolDefinition: Centralized capability catalog
- AuditLogger: Rotating, secret-redacting security audit log
"""

from core.security.action_classifier import ActionClassifier, RiskLevel
from core.security.audit_logger import AuditLogger, audit_logger
from core.security.command_validator import CommandValidator
from core.security.confirmation_manager import ConfirmationManager, confirmation_manager
from core.security.file_access_guard import FileAccessGuard, file_access_guard
from core.security.permission_manager import PermissionManager, SecurityPolicyMode, permission_manager
from core.security.security_manager import SecurityDecision, SecurityManager, security_manager
from core.security.tool_registry import ToolDefinition, ToolRegistry, ToolType, tool_registry

__all__ = [
    "SecurityManager",
    "security_manager",
    "SecurityDecision",
    "ActionClassifier",
    "RiskLevel",
    "CommandValidator",
    "FileAccessGuard",
    "file_access_guard",
    "ConfirmationManager",
    "confirmation_manager",
    "PermissionManager",
    "SecurityPolicyMode",
    "permission_manager",
    "ToolRegistry",
    "ToolDefinition",
    "ToolType",
    "tool_registry",
    "AuditLogger",
    "audit_logger",
]

