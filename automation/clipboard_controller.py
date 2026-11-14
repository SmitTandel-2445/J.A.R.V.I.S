"""
Clipboard Controller Module for J.A.R.V.I.S.
--------------------------------------------
Provides voice-activated clipboard and text automation:
- Read active clipboard contents aloud (with smart summarization for long text)
- Copy specific text or last conversational AI response to clipboard
- Clear clipboard contents
- Voice dictation / Auto-type: injects text into the active cursor position via clipboard paste
"""

from typing import Tuple
import time
import pyautogui
import pyperclip
from utils.logger import logger

pyautogui.FAILSAFE = True


class ClipboardController:
    """Manages reading, writing, clearing, and injecting clipboard text."""

    @staticmethod
    def read() -> Tuple[bool, str, str]:
        """
        Reads text from the Windows clipboard.
        :return: (success: bool, spoken_response: str, raw_text: str)
        """
        try:
            raw_text = pyperclip.paste()
            if not raw_text or not raw_text.strip():
                logger.info("Clipboard is empty or contains non-text data.")
                return True, "Your clipboard is currently empty, sir.", ""

            clean_text = raw_text.strip()

            # Security Check: Detect if clipboard contains sensitive credentials/tokens
            import re
            is_secret = (
                re.search(r"\b(?:AIzaSy|sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|bearer\s+[a-zA-Z0-9\._\-]+)\b", clean_text, re.I)
                or (len(clean_text) > 24 and " " not in clean_text and re.search(r"[0-9]", clean_text) and re.search(r"[a-z]", clean_text) and re.search(r"[A-Z]", clean_text))
            )
            if is_secret:
                logger.info("Clipboard read contains sensitive credential or secret; suppressed aloud reading.")
                return True, "Your clipboard appears to contain a security token or credential. For your security, I will not speak it aloud, sir.", clean_text

            # If text is very long, summarize for speech synthesis so TTS does not block
            if len(clean_text) > 200:
                speech = f"Your clipboard contains {len(clean_text)} characters. The beginning reads: {clean_text[:140]}..."
            else:
                speech = f"Your clipboard reads: {clean_text}"

            logger.info(f"Read {len(clean_text)} chars from clipboard.")
            return True, speech, clean_text
        except Exception as e:
            logger.error(f"Failed to read clipboard: {e}")
            return False, "I was unable to access the clipboard, sir.", ""

    @staticmethod
    def copy(text: str) -> Tuple[bool, str]:
        """
        Copies specified text into the Windows clipboard.
        :param text: Text string to copy
        :return: (success: bool, spoken_response: str)
        """
        try:
            clean_text = text.strip()
            if not clean_text:
                return False, "There was no text provided to copy, sir."

            pyperclip.copy(clean_text)
            logger.info(f"Copied {len(clean_text)} chars to clipboard.")
            return True, "Copied to clipboard, sir."
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return False, "I encountered an error copying to the clipboard, sir."

    @staticmethod
    def clear() -> Tuple[bool, str]:
        """
        Clears the Windows clipboard.
        :return: (success: bool, spoken_response: str)
        """
        try:
            pyperclip.copy("")
            logger.info("Clipboard cleared.")
            return True, "Clipboard cleared, sir."
        except Exception as e:
            logger.error(f"Failed to clear clipboard: {e}")
            return False, "I could not clear the clipboard, sir."

    @staticmethod
    def type_text(text: str) -> Tuple[bool, str]:
        """
        Injects text directly into the focused field using rapid clipboard injection (Ctrl+V).
        This safely preserves Unicode, emojis, line breaks, and prevents dropped keystrokes.
        :param text: Text string to type / paste
        :return: (success: bool, spoken_response: str)
        """
        try:
            clean_text = text.strip()
            if not clean_text:
                return False, "There was no text provided to type, sir."

            # Save previous clipboard to restore after typing
            try:
                old_clipboard = pyperclip.paste()
            except Exception:
                old_clipboard = ""

            # Load target text into clipboard and trigger Ctrl+V paste
            pyperclip.copy(clean_text)
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            logger.info(f"Injected text ({len(clean_text)} chars) into active field.")

            # Briefly delay then restore previous clipboard in background
            time.sleep(0.2)
            try:
                if old_clipboard:
                    pyperclip.copy(old_clipboard)
            except Exception:
                pass

            preview = clean_text[:40] + ("..." if len(clean_text) > 40 else "")
            return True, f"Typed: {preview}, sir."
        except Exception as e:
            logger.error(f"Failed to auto-type text: {e}")
            return False, "I was unable to type into the active field, sir."


# Global default instance
clipboard_controller = ClipboardController()

