"""
Context Management Module for J.A.R.V.I.S.
-------------------------------------------
Tracks runtime conversational state and detects active desktop application contexts
(e.g., Spotify, YouTube, Google Browser) to resolve ambiguous voice commands.
"""

import threading
from typing import Any, Dict, Optional
import psutil
import pygetwindow as gw
from utils.logger import logger


class ContextManager:
    """Manages active session context and detects currently focused applications."""

    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: Any) -> None:
        """Stores a key-value pair in active session context."""
        with self._lock:
            self._context[key] = value
            logger.info(f"Context updated: '{key}' = '{value}'")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a value from session context."""
        with self._lock:
            return self._context.get(key, default)

    def clear(self) -> None:
        """Clears all session context."""
        with self._lock:
            self._context.clear()
            logger.info("Session context cleared.")

    def is_spotify_active(self) -> bool:
        """
        Determines whether Spotify is actively open, focused, or in recent context.
        """
        # 1. Check if the active window title contains Spotify
        try:
            active = gw.getActiveWindowTitle()
            if active and "spotify" in active.lower():
                return True
            for win in gw.getAllWindows():
                if win.title and "spotify" in win.title.lower():
                    return True
        except Exception:
            pass

        # 2. Check running processes
        try:
            for p in psutil.process_iter(["name"]):
                name = p.info.get("name")
                if name and name.lower() == "spotify.exe":
                    return True
        except Exception:
            pass

        # 3. Check explicit recent context
        return self.get("app") == "spotify"

    def is_youtube_active(self) -> bool:
        """
        Determines whether a YouTube tab is currently open or focused in any browser.
        """
        # 1. Check window titles for YouTube tab
        try:
            active = gw.getActiveWindowTitle()
            if active and "youtube" in active.lower():
                return True
            for win in gw.getAllWindows():
                if win.title and "youtube" in win.title.lower():
                    return True
        except Exception:
            pass

        # 2. Check explicit recent context
        return self.get("app") == "youtube"


# Global default instance
context_manager = ContextManager()

