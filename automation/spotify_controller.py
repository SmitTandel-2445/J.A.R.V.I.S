"""
Spotify Automation Controller Module for J.A.R.V.I.S.
------------------------------------------------------
Provides search and automatic playback execution inside the Spotify application.
Uses keyboard hotkeys (Ctrl+K search, clipboard injection, Enter play) and
window focus management.
"""

import os
import time
from typing import Tuple

import pyautogui
import pygetwindow as gw
import pyperclip

from core.context import context_manager
from utils.logger import logger

pyautogui.FAILSAFE = False


class SpotifyController:
    """Manages searching and playing music inside the Spotify desktop client."""

    @staticmethod
    def focus_spotify() -> bool:
        """Brings the Spotify desktop window to the foreground."""
        try:
            for win in gw.getAllWindows():
                if win.title and "spotify" in win.title.lower():
                    if not win.isActive:
                        win.activate()
                        time.sleep(0.3)
                    return True
        except Exception as e:
            logger.warning(f"Could not focus Spotify window: {e}")
        return False

    @classmethod
    def play_song(cls, song: str) -> Tuple[bool, str]:
        """
        Searches for a song in Spotify and automatically starts playback.

        :param song: Title, artist, or query to play
        :return: (success: bool, spoken_response: str)
        """
        song = song.strip()
        if not song:
            return False, "What song would you like me to play on Spotify, sir?"

        logger.info(f"Initiating Spotify playback for: '{song}'")

        # 1. Ensure Spotify is running
        if not context_manager.is_spotify_active():
            try:
                os.startfile("spotify:")
                time.sleep(1.8)
            except Exception as e:
                logger.error(f"Failed to launch Spotify: {e}")

        # 2. Focus Spotify window
        cls.focus_spotify()
        time.sleep(0.2)

        try:
            # Focus search bar in Spotify (Ctrl+K or Ctrl+L)
            pyautogui.hotkey("ctrl", "k")
            time.sleep(0.3)

            # Paste song name instantly
            pyperclip.copy(song)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.5)

            # Select and play top result
            pyautogui.press("enter")
            time.sleep(0.2)
            pyautogui.press("enter")

            # Update session context
            context_manager.set("app", "spotify")
            context_manager.set("last_song", song)

            logger.info(f"Dispatched play command for '{song}' in Spotify.")
            return True, f"Playing {song} on Spotify, sir."

        except Exception as e:
            logger.error(f"Error during Spotify search & play automation: {e}")
            return False, f"I had trouble playing {song} in Spotify, sir."


# Global default instance
spotify_controller = SpotifyController()

