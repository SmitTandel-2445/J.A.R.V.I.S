"""
Desktop Application Launcher Module for J.A.R.V.I.S.
----------------------------------------------------
Provides intelligent resolution, execution, and termination of any installed
desktop applications, Windows Store apps, and popular web platforms.
Equipped with fuzzy searching and automatic web search fallback.
"""

import os
import shutil
import subprocess
import urllib.parse
import webbrowser
from typing import Optional, Tuple

import psutil

from automation.app_scanner import AppScanner, app_scanner as default_scanner
from utils.logger import logger


class AppLauncher:
    """Manages launching and closing any desktop application or web platform."""

    def __init__(self, scanner: Optional[AppScanner] = None):
        """
        Initialize the AppLauncher.

        :param scanner: AppScanner instance for discovering PC applications
        """
        self.scanner = scanner or default_scanner

    def resolve_target(self, app_name: str) -> str:
        """Helper to resolve target path or URI for an application name."""
        target, _ = self.scanner.resolve(app_name)
        return target or app_name

    def launch(self, app_name: str) -> Tuple[bool, str]:
        """
        Launches an application or service asynchronously.

        :param app_name: Spoken or text name of the application.
        :return: (success: bool, status_message: str)
        """
        clean_name = app_name.strip()
        if not clean_name:
            return False, "Which application would you like me to open, sir?"

        logger.info(f"Resolving application target for: '{clean_name}'")
        target, res_type = self.scanner.resolve(clean_name)

        # 1. Web Service Match (e.g. YouTube, GitHub, LeetCode, ChatGPT, Canva)
        if res_type == "web" and target:
            try:
                webbrowser.open(target)
                logger.info(f"Opened web shortcut: '{clean_name}' -> {target}")
                return True, f"Opening {clean_name}, sir."
            except Exception as e:
                logger.error(f"Failed to open web shortcut '{target}': {e}")

        # 2. Microsoft Store UWP App (e.g. 'spotify:', 'whatsapp:', 'ms-settings:')
        if res_type == "uwp" and target:
            try:
                os.startfile(target)
                logger.info(f"Opened UWP protocol: '{clean_name}' -> {target}")
                return True, f"Opening {clean_name}, sir."
            except Exception as e:
                logger.error(f"Failed to open UWP protocol '{target}': {e}")

        # 3. Discovered Local Application (.lnk, .exe, or executable in PATH)
        if res_type == "file" and target:
            try:
                os.startfile(target)
                logger.info(f"Opened local application: '{clean_name}' -> {target}")
                return True, f"Opening {clean_name}, sir."
            except Exception as e:
                logger.error(f"os.startfile failed for '{target}': {e}")
                # Try Popen fallback
                try:
                    subprocess.Popen(
                        [target],
                        shell=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True, f"Opening {clean_name}, sir."
                except Exception:
                    pass

        # 4. Safe Web Search Fallback: If not found on PC, search Google for it automatically
        search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_name)}"
        try:
            webbrowser.open(search_url)
            logger.info(f"App not found locally, launched Google search for: '{clean_name}'")
            return True, f"I could not find {clean_name} locally, sir. Searching Google for it."
        except Exception as e:
            logger.error(f"Web search fallback failed for '{clean_name}': {e}")
            return False, f"I could not locate or open {clean_name}, sir."

    def close(self, app_name: str) -> Tuple[bool, str]:
        """
        Terminates running instances of an application safely.
        Enforces exact process name matching and protects Windows critical processes.

        :param app_name: Spoken or text name of the application.
        :return: (success: bool, status_message: str)
        """
        from core.security.command_validator import CommandValidator

        clean_name = app_name.strip().lower()
        is_valid, canon_name, err = CommandValidator.validate_process_target(clean_name)
        if not is_valid:
            logger.warning(f"Process termination blocked by CommandValidator: {err}")
            return False, err

        target, _ = self.scanner.resolve(clean_name)

        # Extract target process base name
        if target and os.path.exists(target):
            target_exe = os.path.basename(target).lower()
        else:
            target_exe = f"{clean_name}.exe" if not clean_name.endswith(".exe") else clean_name

        killed_count = 0
        try:
            for proc in psutil.process_iter(["name", "pid"]):
                try:
                    proc_name = (proc.info.get("name") or "").lower()
                    # Enforce exact match on executable name to prevent broad substring kills
                    if proc_name and (proc_name == target_exe or proc_name == f"{clean_name}.exe" or proc_name == clean_name):
                        proc.terminate()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed_count > 0:
                logger.info(f"Terminated {killed_count} process(es) matching '{clean_name}'.")
                return True, f"Closed {clean_name}, sir."
            else:
                return False, f"{clean_name} does not appear to be running, sir."

        except Exception as e:
            logger.error(f"Error terminating process for '{clean_name}': {e}")
            return False, f"I encountered an error trying to close {clean_name}, sir."


# Global default instance
app_launcher = AppLauncher()
