"""
Media Controller Module for J.A.R.V.I.S.
----------------------------------------
Provides global hardware-level media controls (Play/Pause, Next Track, Previous Track)
using Windows virtual media key events via PyAutoGUI.
Works across Spotify, YouTube, VLC, Apple Music, and Windows Media Player.
"""

from typing import Tuple
import pyautogui
from utils.logger import logger

pyautogui.FAILSAFE = False


class MediaController:
    """Manages global multimedia playback controls."""

    @staticmethod
    def play_pause() -> Tuple[bool, str]:
        """Toggles play/pause on the active media player."""
        try:
            pyautogui.press("playpause")
            logger.info("Media key pressed: playpause")
            return True, "Toggling media playback, sir."
        except Exception as e:
            logger.error(f"Failed to toggle media playback: {e}")
            return False, "Could not send media command, sir."

    @staticmethod
    def next_track() -> Tuple[bool, str]:
        """Skips to the next media track."""
        try:
            pyautogui.press("nexttrack")
            logger.info("Media key pressed: nexttrack")
            return True, "Playing next track, sir."
        except Exception as e:
            logger.error(f"Failed to skip track: {e}")
            return False, "Could not skip track, sir."

    @staticmethod
    def previous_track() -> Tuple[bool, str]:
        """Returns to the previous media track."""
        try:
            pyautogui.press("prevtrack")
            logger.info("Media key pressed: prevtrack")
            return True, "Playing previous track, sir."
        except Exception as e:
            logger.error(f"Failed to return to previous track: {e}")
            return False, "Could not return to previous track, sir."

    @staticmethod
    def stop() -> Tuple[bool, str]:
        """Stops active media playback."""
        try:
            pyautogui.press("stop")
            logger.info("Media key pressed: stop")
            return True, "Media playback stopped, sir."
        except Exception as e:
            logger.error(f"Failed to stop media: {e}")
            return False, "Could not stop media, sir."


# Global default instance
media_controller = MediaController()

