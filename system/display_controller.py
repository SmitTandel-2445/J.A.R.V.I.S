"""
Multi-Monitor & Display Management Module for J.A.R.V.I.S.
------------------------------------------------------------
Provides display controls:
- Move active window to adjacent / second monitor (Win + Shift + Right/Left)
- Windows Theme toggle: Light Mode vs. Dark Mode via Windows Registry
- Night Light display toggle via Windows Settings URI
"""

import ctypes
import os
import subprocess
from typing import Optional, Tuple
import winreg

import pyautogui

from utils.logger import logger

pyautogui.FAILSAFE = False

# Broadcast message constant for settings change
HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002


class DisplayController:
    """Manages multi-monitor window positioning and Windows display theme."""

    THEME_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"

    @staticmethod
    def move_window_to_monitor(direction: str = "right") -> Tuple[bool, str]:
        """
        Moves the currently focused window to the next monitor using Win + Shift + Arrow.
        :param direction: 'right' or 'left'
        :return: (success: bool, spoken_response: str)
        """
        try:
            arrow = "right" if direction.lower() == "right" else "left"
            pyautogui.hotkey("win", "shift", arrow)
            logger.info(f"Moved active window to {direction} monitor.")
            return True, f"Moved window to the next display, sir."
        except Exception as e:
            logger.error(f"Failed to move window to monitor: {e}")
            return False, "I was unable to move the window to the other display, sir."

    @classmethod
    def set_theme(cls, mode: str = "dark") -> Tuple[bool, str]:
        """
        Switches Windows between Dark Mode and Light Mode.
        :param mode: 'dark', 'light', or 'toggle'
        :return: (success: bool, spoken_response: str)
        """
        try:
            target_mode = mode.lower().strip()

            # Query current value
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.THEME_KEY_PATH, 0, winreg.KEY_READ) as key:
                current_apps, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")

            if target_mode == "toggle":
                new_val = 1 if current_apps == 0 else 0
            elif target_mode == "light":
                new_val = 1
            else:
                new_val = 0

            # Write updated values for both Apps and System
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cls.THEME_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, new_val)
                winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, new_val)

            # Broadcast settings change so Windows updates in real-time
            try:
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST,
                    WM_SETTINGCHANGE,
                    0,
                    "ImmersiveColorSet",
                    SMTO_ABORTIFHUNG,
                    100,
                    None,
                )
            except Exception:
                pass

            theme_name = "light" if new_val == 1 else "dark"
            logger.info(f"Windows theme changed to: {theme_name} mode.")
            return True, f"Switched Windows to {theme_name} mode, sir."

        except Exception as e:
            logger.error(f"Error modifying Windows theme: {e}")
            return False, "I was unable to change the Windows theme, sir."

    @staticmethod
    def toggle_night_light() -> Tuple[bool, str]:
        """
        Opens the Windows Night Light display configuration.
        :return: (success: bool, spoken_response: str)
        """
        try:
            os.startfile("ms-settings:nightlight")
            logger.info("Opened Windows Night Light display settings.")
            return True, "Opening Night Light display settings, sir."
        except Exception as e:
            logger.error(f"Failed to open Night Light settings: {e}")
            return False, "Could not access Night Light settings, sir."


# Global default instance
display_controller = DisplayController()

