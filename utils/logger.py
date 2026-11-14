"""
Logging Configuration Module for J.A.R.V.I.S.
----------------------------------------------
Provides thread-safe rotating file and stream logging with automated
credential redaction to prevent accidental secret leakage into logs.
"""

import logging
from logging.handlers import RotatingFileHandler
import re
from typing import Optional

from config import LOG_FILE, LOGS_DIR


class RedactingFormatter(logging.Formatter):
    """Logging formatter that intercepts and masks credentials and secrets."""

    KEY_VAL_PATTERN = re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password|auth|bearer)(\s*[:=]\s*['\"]?)[a-zA-Z0-9_\-]{6,}['\"]?"
    )
    TOKEN_PATTERNS = [
        re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
        re.compile(r"sk-[a-zA-Z0-9]{20,}"),
        re.compile(r"ghp_[a-zA-Z0-9]{20,}"),
    ]

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        try:
            formatted = self.KEY_VAL_PATTERN.sub(r"\1\2***REDACTED***", formatted)
            for pattern in self.TOKEN_PATTERNS:
                formatted = pattern.sub("***REDACTED_TOKEN***", formatted)
        except Exception:
            pass
        return formatted


# Ensure logs folder exists relative to project root
handlers = []
formatter = RedactingFormatter("%(asctime)s | %(levelname)s | %(message)s")

try:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    # Rotating file handler: 5MB max size per file, retaining 5 backups
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
except OSError:
    pass

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
handlers.append(console_handler)

logging.basicConfig(
    level=logging.INFO,
    handlers=handlers,
)

logger = logging.getLogger("JARVIS")
