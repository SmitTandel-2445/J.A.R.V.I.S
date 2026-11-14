"""
Action Risk Classification Module for J.A.R.V.I.S.
---------------------------------------------------
Implements a 4-Tier Risk Classification System aligned with OWASP Top 10 for
Agentic Applications and NIST Secure Software Development Framework:

- LEVEL 1 — LOW RISK: Read-only queries, general conversation, time, battery, telemetry.
- LEVEL 2 — MODERATE RISK: Launching approved apps, safe browsing, taking screenshots, window navigation.
- LEVEL 3 — HIGH RISK: File creation, process termination, system sleep/lock, text injection.
- LEVEL 4 — CRITICAL RISK: Permanent deletion (Recycle Bin), administrative execution, dangerous utilities.
"""

from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple


class RiskLevel(Enum):
    """Enumeration of security risk levels for all J.A.R.V.I.S. actions."""
    LEVEL_1_LOW = 1
    LEVEL_2_MODERATE = 2
    LEVEL_3_HIGH = 3
    LEVEL_4_CRITICAL = 4

    def __str__(self) -> str:
        return self.name

    @property
    def label(self) -> str:
        labels = {
            RiskLevel.LEVEL_1_LOW: "LOW RISK (Level 1)",
            RiskLevel.LEVEL_2_MODERATE: "MODERATE RISK (Level 2)",
            RiskLevel.LEVEL_3_HIGH: "HIGH RISK (Level 3)",
            RiskLevel.LEVEL_4_CRITICAL: "CRITICAL RISK (Level 4)",
        }
        return labels.get(self, "UNKNOWN RISK")


class ActionClassifier:
    """Classifies user actions, intents, and commands into standardized Risk Levels."""

    # Default baseline risk mapping per IntentType string value
    INTENT_BASE_RISK: Dict[str, RiskLevel] = {
        "time_date": RiskLevel.LEVEL_1_LOW,
        "system_telemetry": RiskLevel.LEVEL_1_LOW,
        "web_search": RiskLevel.LEVEL_1_LOW,
        "youtube_play": RiskLevel.LEVEL_1_LOW,
        "spotify_play": RiskLevel.LEVEL_1_LOW,
        "play_media": RiskLevel.LEVEL_1_LOW,
        "media_control": RiskLevel.LEVEL_1_LOW,
        "system_volume": RiskLevel.LEVEL_1_LOW,
        "system_brightness": RiskLevel.LEVEL_1_LOW,
        "conversation_ai": RiskLevel.LEVEL_1_LOW,
        "go_offline": RiskLevel.LEVEL_1_LOW,

        "browser_tab": RiskLevel.LEVEL_2_MODERATE,
        "window_control": RiskLevel.LEVEL_2_MODERATE,
        "screenshot": RiskLevel.LEVEL_2_MODERATE,
        "open_app": RiskLevel.LEVEL_2_MODERATE,
        "display": RiskLevel.LEVEL_2_MODERATE,
        "timer": RiskLevel.LEVEL_2_MODERATE,
        "network": RiskLevel.LEVEL_2_MODERATE,

        "system_power": RiskLevel.LEVEL_3_HIGH,
        "close_app": RiskLevel.LEVEL_3_HIGH,
        "task_manager": RiskLevel.LEVEL_3_HIGH,
        "shortcut": RiskLevel.LEVEL_3_HIGH,
        "clipboard": RiskLevel.LEVEL_3_HIGH,
        "file_folder": RiskLevel.LEVEL_3_HIGH,
    }

    # High-privilege / administrative binaries that elevate risk to CRITICAL
    CRITICAL_TARGETS = {
        "powershell", "powershell.exe", "cmd", "cmd.exe", "regedit", "regedit.exe",
        "format", "format.com", "vssadmin", "vssadmin.exe", "diskpart", "diskpart.exe",
        "bcdedit", "bcdedit.exe", "taskkill", "taskkill.exe", "netsh", "netsh.exe",
        "shutdown", "shutdown.exe", "rundll32", "rundll32.exe"
    }

    @classmethod
    def classify(cls, intent_val: str, params: Optional[Dict[str, Any]] = None) -> Tuple[RiskLevel, str]:
        """
        Calculates the risk level for a given intent and its specific parameters.

        :param intent_val: String representation of IntentType
        :param params: Parameter dictionary associated with the intent
        :return: (RiskLevel, explanation_reason)
        """
        params = params or {}
        base_risk = cls.INTENT_BASE_RISK.get(intent_val, RiskLevel.LEVEL_2_MODERATE)

        # -------------------------------------------------------------
        # 1. FILE & FOLDER ACTIONS
        # -------------------------------------------------------------
        if intent_val == "file_folder":
            action = params.get("action", "")
            if action == "empty_recycle_bin":
                return RiskLevel.LEVEL_4_CRITICAL, "Permanent deletion of Recycle Bin contents."
            elif action == "create_folder":
                return RiskLevel.LEVEL_3_HIGH, "File system directory modification on Desktop."
            elif action in ("open_folder", "open_drive"):
                return RiskLevel.LEVEL_2_MODERATE, "Opening local folder in File Explorer."
            elif action == "latest_download":
                return RiskLevel.LEVEL_3_HIGH, "Launching recently downloaded file from Downloads."

        # -------------------------------------------------------------
        # 2. APPLICATION LAUNCH
        # -------------------------------------------------------------
        if intent_val == "open_app":
            app_name = str(params.get("app_name", "")).strip().lower()
            if app_name in cls.CRITICAL_TARGETS or any(app_name.endswith(ext) for ext in (".bat", ".cmd", ".vbs", ".ps1")):
                return RiskLevel.LEVEL_4_CRITICAL, f"Execution of administrative or scripting interpreter '{app_name}'."
            return RiskLevel.LEVEL_2_MODERATE, f"Launching approved application '{app_name}'."

        # -------------------------------------------------------------
        # 3. PROCESS TERMINATION & CLOSE
        # -------------------------------------------------------------
        if intent_val == "close_app":
            app_name = str(params.get("app_name", "")).strip().lower()
            if app_name in cls.CRITICAL_TARGETS:
                return RiskLevel.LEVEL_4_CRITICAL, f"Terminating administrative process '{app_name}'."
            return RiskLevel.LEVEL_3_HIGH, f"Terminating application process '{app_name}'."

        if intent_val == "task_manager":
            action = params.get("action", "")
            if action == "kill":
                target = str(params.get("target", "")).strip().lower()
                return RiskLevel.LEVEL_3_HIGH, f"Forcefully terminating process '{target}'."
            return RiskLevel.LEVEL_1_LOW, "Inspecting system process and resource telemetry."

        # -------------------------------------------------------------
        # 4. SYSTEM POWER
        # -------------------------------------------------------------
        if intent_val == "system_power":
            action = params.get("action", "")
            if action in ("shutdown", "restart"):
                return RiskLevel.LEVEL_4_CRITICAL, f"System {action} requested."
            if action in ("sleep", "hibernate"):
                return RiskLevel.LEVEL_3_HIGH, "Placing workstation into suspended power state."
            if action == "lock":
                return RiskLevel.LEVEL_2_MODERATE, "Locking workstation display."

        # -------------------------------------------------------------
        # 5. CLIPBOARD & TEXT INJECTION
        # -------------------------------------------------------------
        if intent_val == "clipboard":
            action = params.get("action", "")
            if action == "type":
                return RiskLevel.LEVEL_3_HIGH, "Automated keyboard text injection into active cursor."
            if action == "clear":
                return RiskLevel.LEVEL_2_MODERATE, "Clearing clipboard contents."
            return RiskLevel.LEVEL_1_LOW, "Reading or copying text to clipboard."

        # -------------------------------------------------------------
        # 6. GLOBAL SHORTCUTS
        # -------------------------------------------------------------
        if intent_val == "shortcut":
            action = params.get("action", "")
            if action in ("cut", "paste", "save"):
                return RiskLevel.LEVEL_2_MODERATE, f"Dispatched keyboard shortcut '{action}'."
            return RiskLevel.LEVEL_1_LOW, f"Dispatched navigation shortcut '{action}'."

        return base_risk, f"Standard execution for {intent_val}."

