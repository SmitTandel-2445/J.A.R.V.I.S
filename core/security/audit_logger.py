"""
Security Audit Logger Module for J.A.R.V.I.S.
----------------------------------------------
Provides dedicated, tamper-resistant, rotating security audit logging.
Maintains an immutable record of all security decisions, risk evaluations,
permission checks, confirmation flows, and blocked adversarial attempts.
Equipped with automated secret redaction to prevent credential leakage.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
from typing import Any, Dict, Optional

import config


class AuditLogger:
    """Manages dedicated security audit logging with automatic credential masking."""

    # Regex patterns for detecting and redacting secrets in log records
    KEY_VAL_PATTERN = re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password|auth|bearer)(\s*[:=]\s*['\"]?)[a-zA-Z0-9_\-]{6,}['\"]?"
    )
    TOKEN_PATTERNS = [
        re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
        re.compile(r"sk-[a-zA-Z0-9]{20,}"),
        re.compile(r"ghp_[a-zA-Z0-9]{20,}"),
    ]

    def __init__(self, log_dir: Optional[Path] = None, max_bytes: int = 5 * 1024 * 1024, backup_count: int = 5):
        self.log_dir = log_dir or getattr(config, "LOGS_DIR", Path("logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log_file = self.log_dir / "security_audit.log"

        self._logger = logging.getLogger("JARVIS_AUDIT")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        # Configure rotating file handler if not already present
        if not self._logger.handlers:
            handler = RotatingFileHandler(
                self.audit_log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def redact_secrets(self, message: str) -> str:
        """Sanitizes text by replacing detected credentials with ***REDACTED***."""
        if not message:
            return ""
        clean = message
        try:
            clean = self.KEY_VAL_PATTERN.sub(r"\1\2***REDACTED***", clean)
            for pattern in self.TOKEN_PATTERNS:
                clean = pattern.sub("***REDACTED_TOKEN***", clean)
        except Exception:
            pass
        return clean

    def log_decision(
        self,
        event: str,
        intent: str,
        risk_level: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        query: str = "",
    ) -> None:
        """
        Records a structured security decision in the audit log.

        :param event: Type of security event (EVALUATE, CONFIRM_REQ, CONFIRMED, CANCELLED, BLOCKED)
        :param intent: Intent identifier
        :param risk_level: Risk classification label
        :param status: ALLOWED, DENIED, PENDING
        :param details: Additional contextual parameters
        :param query: Raw user query (sanitized)
        """
        clean_query = self.redact_secrets(query)
        details_str = str(details) if details else "{}"
        clean_details = self.redact_secrets(details_str)

        log_entry = (
            f"EVENT={event} | INTENT={intent} | RISK={risk_level} | "
            f"STATUS={status} | QUERY='{clean_query}' | DETAILS={clean_details}"
        )
        self._logger.info(log_entry)

    def log_blocked(self, intent: str, reason: str, query: str = "") -> None:
        """Logs a blocked action attempt."""
        self.log_decision(
            event="ACTION_BLOCKED",
            intent=intent,
            risk_level="CRITICAL",
            status="DENIED",
            details={"reason": reason},
            query=query,
        )

    def log_confirmation_requested(self, intent: str, risk_level: str, prompt: str) -> None:
        """Logs that confirmation was requested from user."""
        self.log_decision(
            event="CONFIRMATION_REQUESTED",
            intent=intent,
            risk_level=risk_level,
            status="PENDING",
            details={"prompt": prompt},
        )

    def log_confirmation_outcome(self, intent: str, confirmed: bool) -> None:
        """Logs the user's confirmation decision."""
        status = "CONFIRMED" if confirmed else "CANCELLED"
        self.log_decision(
            event="CONFIRMATION_OUTCOME",
            intent=intent,
            risk_level="HIGH",
            status=status,
        )


# Global default instance
audit_logger = AuditLogger()
