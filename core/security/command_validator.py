"""
Command & Input Validator Module for J.A.R.V.I.S.
--------------------------------------------------
Enforces strict input validation, protects against command injection,
blocks targeting of critical Windows/system processes, and validates
network URLs and application names.
"""

import os
import re
from typing import Optional, Set, Tuple


class CommandValidator:
    """Validates command arguments, application names, process targets, and URLs."""

    # Shell metacharacters that must never be passed into dynamic system calls
    DANGEROUS_SHELL_CHARS = re.compile(r"[;&|`$><\n\r]")

    # Malicious injection patterns commonly used in prompt/command injection
    INJECTION_PATTERNS = [
        re.compile(r"\b(?:powershell|cmd|bash|sh|zsh)\s*-(?:e|enc|encodedcommand)\b", re.IGNORECASE),
        re.compile(r"\b(?:invoke-expression|iex|downloadstring|curl|wget)\b", re.IGNORECASE),
        re.compile(r"\b(?:rmdir|del|format|diskpart|reg\s+add|reg\s+delete)\b", re.IGNORECASE),
        re.compile(r"\b(?:net\s+user|net\s+localgroup|whoami\s+/priv)\b", re.IGNORECASE),
    ]

    # Windows OS critical processes that must NEVER be terminated
    PROTECTED_SYSTEM_PROCESSES: Set[str] = {
        "system",
        "system idle process",
        "idle",
        "registry",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "fontdrvhost.exe",
        "winlogon.exe",
        "dwm.exe",
        "explorer.exe",
        "spoolsv.exe",
        "taskhostw.exe",
        "sihost.exe",
        "ctfmon.exe",
        "audiodg.exe",
    }

    # J.A.R.V.I.S. internal processes that must not self-terminate via process kill
    PROTECTED_JARVIS_PROCESSES: Set[str] = {
        "python.exe",
        "pythonw.exe",
    }

    # Allowed URL schemes for web navigation
    ALLOWED_URL_SCHEMES = ("https://", "http://")

    # Prohibited URL schemes
    BLOCKED_URL_SCHEMES = ("file://", "javascript:", "data:", "vbscript:", "about:")

    @classmethod
    def sanitize_input(cls, text: Optional[str]) -> str:
        """Removes null bytes and normalizes whitespace."""
        if not text:
            return ""
        # Remove null bytes and control chars except space/tab
        clean = "".join(ch for ch in text if ch == " " or ch == "\t" or (ch.isprintable() and ord(ch) >= 32))
        return clean.strip()

    @classmethod
    def validate_command_string(cls, command_str: str) -> Tuple[bool, str]:
        """
        Validates that a command string does not contain shell injection payloads.
        :return: (is_valid: bool, error_message: str)
        """
        clean = cls.sanitize_input(command_str)
        if not clean:
            return False, "Command cannot be empty."

        # Check for dangerous shell metacharacters
        if cls.DANGEROUS_SHELL_CHARS.search(clean):
            return False, f"Prohibited shell metacharacters detected in command: '{clean}'"

        # Check for known dangerous command injection tokens
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(clean):
                return False, f"Potentially malicious execution pattern detected: '{clean}'"

        return True, ""

    @classmethod
    def validate_process_target(cls, target_name: str) -> Tuple[bool, str, str]:
        """
        Validates that a process name is safe and does not target protected OS services.
        Rejects ambiguous or single-character target names.

        :param target_name: Raw process name requested by user
        :return: (is_valid: bool, canonical_name: str, error_message: str)
        """
        clean = cls.sanitize_input(target_name).lower()
        if not clean:
            return False, "", "Process target cannot be empty."

        # Disallow dangerously short/ambiguous targets that would match too broadly
        if len(clean) < 2:
            return False, "", f"Target name '{clean}' is too short and ambiguous for process operations."

        # Normalize with extension if not present
        normalized = clean if clean.endswith(".exe") else f"{clean}.exe"
        base_name = os.path.basename(clean)

        # Check against Windows protected processes
        if clean in cls.PROTECTED_SYSTEM_PROCESSES or normalized in cls.PROTECTED_SYSTEM_PROCESSES or base_name in cls.PROTECTED_SYSTEM_PROCESSES:
            return False, clean, f"Process '{clean}' is a critical Windows system process and is protected from termination."

        # Check against J.A.R.V.I.S. self process
        if clean in cls.PROTECTED_JARVIS_PROCESSES or normalized in cls.PROTECTED_JARVIS_PROCESSES:
            return False, clean, "Terminating J.A.R.V.I.S. core process via Task Manager is prohibited. Use 'go offline' instead."

        return True, clean, ""

    @classmethod
    def validate_url(cls, url: str) -> Tuple[bool, str]:
        """
        Validates that a web URL uses safe HTTP/HTTPS schemes.
        :return: (is_valid: bool, error_message: str)
        """
        clean = cls.sanitize_input(url).strip()
        if not clean:
            return False, "URL cannot be empty."

        lower_url = clean.lower()

        # Block dangerous schemes
        for blocked in cls.BLOCKED_URL_SCHEMES:
            if lower_url.startswith(blocked):
                return False, f"Prohibited URL scheme '{blocked}' in target: {clean}"

        # If it doesn't start with http/https, verify it looks like a domain name
        if not lower_url.startswith(cls.ALLOWED_URL_SCHEMES):
            if re.search(r"\.(?:com|org|net|edu|gov|io|ai|co|dev|app|in|uk|de|xyz)(?:/.*)?$", lower_url):
                return True, ""
            return False, f"Invalid or non-HTTPS URL target: '{clean}'"

        return True, ""

