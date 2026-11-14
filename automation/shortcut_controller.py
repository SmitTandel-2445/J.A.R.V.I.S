"""
Global Keyboard & Workflow Shortcuts Module for J.A.R.V.I.S.
--------------------------------------------------------------
Provides hands-free voice execution of universal editor and document hotkeys:
- Save File (Ctrl + S)
- Select All (Ctrl + A)
- Undo (Ctrl + Z)
- Redo (Ctrl + Y)
- Copy (Ctrl + C)
- Cut (Ctrl + X)
- Paste (Ctrl + V)
"""

import time
from typing import Tuple

import pyautogui

from utils.logger import logger

pyautogui.FAILSAFE = True


class ShortcutController:
    """Dispatches universal keyboard workflow shortcuts."""

    SHORTCUT_MAP = {
        "save": (["ctrl", "s"], "File saved, sir."),
        "select_all": (["ctrl", "a"], "Selected all, sir."),
        "undo": (["ctrl", "z"], "Undone, sir."),
        "redo": (["ctrl", "y"], "Redone, sir."),
        "cut": (["ctrl", "x"], "Cut to clipboard, sir."),
        "copy": (["ctrl", "c"], "Copied, sir."),
        "paste": (["ctrl", "v"], "Pasted, sir."),
    }

    @classmethod
    def execute_shortcut(cls, action: str) -> Tuple[bool, str]:
        """
        Executes a keyboard shortcut in the active window.
        :param action: Shortcut key ('save', 'select_all', 'undo', 'redo', 'cut', 'copy', 'paste')
        :return: (success: bool, spoken_response: str)
        """
        norm = action.lower().strip()
        if norm not in cls.SHORTCUT_MAP:
            return False, f"Unrecognized keyboard shortcut '{action}', sir."

        keys, speech = cls.SHORTCUT_MAP[norm]
        try:
            pyautogui.hotkey(*keys)
            logger.info(f"Dispatched global shortcut: {'+'.join(keys)} ({norm})")
            return True, speech
        except Exception as e:
            logger.error(f"Error executing shortcut '{norm}': {e}")
            return False, "I was unable to execute that shortcut, sir."


# Global default instance
shortcut_controller = ShortcutController()

