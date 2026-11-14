"""
Confirmation & Authorization Manager for J.A.R.V.I.S.
--------------------------------------------------------
Manages user authorization gates for High (Level 3) and Critical (Level 4) actions.
Ensures that no destructive or irreversible action executes without explicit confirmation.
Guards against voice spoofing, replay attacks, and accidental background triggers.
"""

from dataclasses import dataclass, field
import datetime
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple
import uuid


@dataclass
class PendingAction:
    """Represents an action awaiting explicit user confirmation."""
    action_id: str
    intent_val: str
    parameters: Dict[str, Any]
    prompt: str
    handler: Callable[[], Tuple[bool, str]]
    risk_level: str
    created_at: float = field(default_factory=time.time)
    timeout_seconds: float = 30.0

    @property
    def is_expired(self) -> bool:
        """Checks if the confirmation window has elapsed."""
        return (time.time() - self.created_at) > self.timeout_seconds


class ConfirmationManager:
    """Thread-safe manager for holding and verifying high-risk pending actions."""

    # Explicit positive confirmation phrases
    POSITIVE_CONFIRMATIONS = {
        "yes", "confirm", "proceed", "affirmative", "yes please",
        "do it", "sure", "yeah", "yep", "go ahead", "approved",
    }

    # Explicit negative cancellation phrases
    NEGATIVE_CONFIRMATIONS = {
        "no", "cancel", "abort", "stop", "nevermind", "dont",
        "don't", "negative", "halt", "deny",
    }

    def __init__(self, timeout_seconds: float = 30.0):
        self.default_timeout = timeout_seconds
        self._pending: Optional[PendingAction] = None
        self._lock = threading.Lock()

    def request_confirmation(
        self,
        intent_val: str,
        parameters: Dict[str, Any],
        prompt: str,
        handler: Callable[[], Tuple[bool, str]],
        risk_level: str = "LEVEL_3_HIGH",
    ) -> str:
        """
        Registers an action requiring explicit confirmation.

        :param intent_val: Intent identifier string
        :param parameters: Action parameters
        :param prompt: Question spoken to user (e.g. "Are you sure you want to...")
        :param handler: Zero-argument callable to invoke upon confirmation
        :param risk_level: Label of the action's risk level
        :return: Dynamic action ID
        """
        with self._lock:
            action_id = str(uuid.uuid4())[:8]
            self._pending = PendingAction(
                action_id=action_id,
                intent_val=intent_val,
                parameters=parameters,
                prompt=prompt,
                handler=handler,
                risk_level=risk_level,
                timeout_seconds=self.default_timeout,
            )
            return action_id

    def has_pending(self) -> bool:
        """Checks if there is an active, unexpired pending confirmation."""
        with self._lock:
            if not self._pending:
                return False
            if self._pending.is_expired:
                self._pending = None
                return False
            return True

    def get_pending_prompt(self) -> Optional[str]:
        """Returns the pending action's prompt text if active."""
        with self._lock:
            if self._pending and not self._pending.is_expired:
                return self._pending.prompt
            return None

    def evaluate_response(self, text: str) -> Tuple[bool, bool, str, Optional[Dict[str, Any]]]:
        """
        Evaluates whether the user's spoken input is a confirmation, cancellation, or unrelated.

        :param text: User speech transcription
        :return: (is_handled: bool, success: bool, spoken_response: str, action_data: Optional[dict])
        """
        clean = text.lower().strip()
        for punct in (".", "!", "?", ",", "-"):
            clean = clean.replace(punct, "")
        words = clean.split()

        with self._lock:
            if not self._pending:
                return False, False, "", None

            if self._pending.is_expired:
                expired_intent = self._pending.intent_val
                self._pending = None
                return True, False, "The previous confirmation window has expired, sir. Action was not executed.", {"expired": True, "intent": expired_intent}

            pending = self._pending

            # Check for positive confirmation
            is_positive = (
                clean in self.POSITIVE_CONFIRMATIONS
                or any(w in self.POSITIVE_CONFIRMATIONS for w in words)
                or "yes jarvis" in clean
                or "confirm jarvis" in clean
            )

            # Check for negative cancellation
            is_negative = (
                clean in self.NEGATIVE_CONFIRMATIONS
                or any(w in self.NEGATIVE_CONFIRMATIONS for w in words)
                or "cancel jarvis" in clean
                or "no jarvis" in clean
            )

            if is_positive and not is_negative:
                self._pending = None
                try:
                    ok, speech = pending.handler()
                    return True, ok, speech, {"action_id": pending.action_id, "status": "CONFIRMED", "intent": pending.intent_val}
                except Exception as e:
                    return True, False, f"Error executing confirmed action: {e}", {"action_id": pending.action_id, "status": "ERROR"}

            if is_negative:
                self._pending = None
                return True, True, "Action cancelled, sir.", {"action_id": pending.action_id, "status": "CANCELLED", "intent": pending.intent_val}

            # Unrelated input: cancel pending action to prevent stale confirmation hijacks
            self._pending = None
            return False, False, "", None

    def cancel_pending(self) -> None:
        """Clears any pending confirmation."""
        with self._lock:
            self._pending = None


# Global default instance
confirmation_manager = ConfirmationManager()

