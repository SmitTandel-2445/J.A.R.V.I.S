"""
Window Controller Module for J.A.R.V.I.S.
-----------------------------------------
Provides voice-activated desktop window management:
- Minimize / Maximize / Restore / Close active window
- Minimize / Maximize / Restore / Close specific application windows by name (e.g. Chrome, Notepad, Spotify)
- Snap window Left / Right (Windows Aero Snap)
- Switch window (Alt+Tab)
- Show Desktop (Win+D)

Uses a combination of PyGetWindow, native Win32 handles, and keyboard fallbacks.
Prevents J.A.R.V.I.S. from accidentally minimizing or closing its own GUI.
"""

from typing import Optional, Tuple
import os
import psutil
import pyautogui
import pygetwindow as gw
import win32process
from utils.logger import logger

pyautogui.FAILSAFE = False


class WindowController:
    """Manages active and application desktop windows using OS APIs and keyboard fallbacks."""

    ALIASES = {
        "vs code": ["code", "visual studio code"],
        "vscode": ["code", "visual studio code"],
        "code": ["visual studio code", "code"],
        "google chrome": ["chrome"],
        "chrome": ["google chrome", "chrome"],
        "browser": ["chrome", "msedge", "firefox", "brave"],
        "edge": ["msedge", "microsoft edge"],
        "notepad": ["notepad"],
        "spotify": ["spotify"],
        "calc": ["calculator", "calculatorapp"],
        "calculator": ["calc", "calculatorapp"],
        "cmd": ["command prompt", "cmd.exe"],
        "terminal": ["powershell", "cmd", "windows terminal"],
        "powershell": ["powershell"],
        "word": ["winword", "microsoft word"],
        "excel": ["excel", "microsoft excel"],
    }

    IGNORE_TITLES = {"", "program manager", "windows input experience"}

    # Synonyms and references for J.A.R.V.I.S. itself
    JARVIS_NAMES = {"jarvis", "j.a.r.v.i.s", "yourself", "your", "own", "self", "jarvis window"}

    @classmethod
    def is_jarvis_name(cls, name: Optional[str]) -> bool:
        """Determines whether a requested application name refers to J.A.R.V.I.S."""
        if not name:
            return False
        clean = cls._clean_app_name(name) or name.lower().strip()
        return clean in cls.JARVIS_NAMES or "jarvis" in clean or "j.a.r.v.i.s" in clean

    @classmethod
    def _clean_app_name(cls, name: Optional[str]) -> Optional[str]:
        """Cleans conversational phrasing from application name."""
        if not name:
            return None
        c = name.lower().strip()
        for prefix in ["the ", "this ", "current ", "active "]:
            if c.startswith(prefix):
                c = c[len(prefix):].strip()
        for suffix in [" window", " app", " application"]:
            if c.endswith(suffix):
                c = c[:-len(suffix)].strip()
        if c in ["window", "the window", "app", "application", ""]:
            return None
        return c

    @classmethod
    def find_target_window(cls, app_name: Optional[str] = None):
        """
        Finds the target window object:
        - If app_name refers to J.A.R.V.I.S., locates J.A.R.V.I.S.'s own window.
        - If app_name is given, locates the window matching title or process name.
        - If app_name is None, finds the active user window (ignoring J.A.R.V.I.S. itself).
        """
        clean_target = cls._clean_app_name(app_name)
        my_pid = os.getpid()

        try:
            all_wins = gw.getAllWindows()
        except Exception as e:
            logger.warning(f"Failed to enumerate windows via pygetwindow: {e}")
            all_wins = []

        # Case 0: Explicitly target J.A.R.V.I.S. itself
        if cls.is_jarvis_name(clean_target or app_name):
            # Prioritize window belonging to current process PID
            for w in all_wins:
                if not (w.title or "").strip():
                    continue
                try:
                    _, pid = win32process.GetWindowThreadProcessId(w._hWnd)
                    if pid == my_pid:
                        return w
                except Exception:
                    pass
            # Fallback to exact or partial window title
            for w in all_wins:
                t = (w.title or "").strip().lower()
                if t in ("j.a.r.v.i.s", "jarvis"):
                    return w
            for w in all_wins:
                t = (w.title or "").strip().lower()
                if "j.a.r.v.i.s" in t or "jarvis" in t:
                    return w
            return None

        valid_windows = []
        for w in all_wins:
            title = (w.title or "").strip()
            if not title or title.lower() in cls.IGNORE_TITLES:
                continue
            try:
                _, pid = win32process.GetWindowThreadProcessId(w._hWnd)
                if pid == my_pid:
                    continue  # Ignore J.A.R.V.I.S. window itself for generic commands
                if "j.a.r.v.i.s" in title.lower() or "jarvis" in title.lower():
                    continue
                pname = psutil.Process(pid).name().lower()
            except Exception:
                pname = ""

            valid_windows.append((w, title, pname))

        # Case 1: Target active / topmost window
        if not clean_target:
            try:
                active = gw.getActiveWindow()
                if active and active.title and active.title.strip().lower() not in cls.IGNORE_TITLES:
                    _, apid = win32process.GetWindowThreadProcessId(active._hWnd)
                    if apid != my_pid and "jarvis" not in active.title.lower():
                        return active
            except Exception:
                pass
            # Topmost non-JARVIS window in Z-order
            return valid_windows[0][0] if valid_windows else None

        # Case 2: Target specific application by name or alias
        candidates = [clean_target] + cls.ALIASES.get(clean_target, [])
        for w, title, pname in valid_windows:
            title_lower = title.lower()
            for cand in candidates:
                if cand in title_lower or cand in pname:
                    return w

        return None

    @staticmethod
    def _activate_window(w) -> None:
        """Safely brings a window to the foreground."""
        try:
            w.activate()
        except Exception:
            try:
                import win32gui
                win32gui.SetForegroundWindow(w._hWnd)
            except Exception:
                pass

    def minimize(self, app_name: Optional[str] = None) -> Tuple[bool, str]:
        """Minimizes the specified application window or active user window."""
        clean_name = self._clean_app_name(app_name)
        target = self.find_target_window(clean_name or app_name)
        is_jarvis = self.is_jarvis_name(clean_name or app_name)
        if target:
            try:
                target.minimize()
                logger.info(f"Minimizing window '{target.title}' (requested: {app_name})")
                app_label = "J.A.R.V.I.S." if is_jarvis else (clean_name if clean_name else "window")
                return True, f"Minimizing {app_label}, sir."
            except Exception as e:
                logger.error(f"Error minimizing window '{target.title}': {e}")
                err_label = "J.A.R.V.I.S." if is_jarvis else (clean_name or "window")
                return False, f"Failed to minimize {err_label}, sir."

        # Fallback for active window
        if not clean_name:
            try:
                pyautogui.hotkey("win", "down")
                pyautogui.hotkey("win", "down")
                logger.info("Executed minimize window shortcut fallback.")
                return True, "Minimizing window, sir."
            except Exception as e:
                logger.error(f"Error minimizing window fallback: {e}")
                return False, "Failed to minimize window, sir."

        err_label = "J.A.R.V.I.S." if is_jarvis else clean_name
        return False, f"I could not find an open window for {err_label}, sir."

    def maximize(self, app_name: Optional[str] = None) -> Tuple[bool, str]:
        """Maximizes the specified application window or active user window."""
        clean_name = self._clean_app_name(app_name)
        target = self.find_target_window(clean_name or app_name)
        is_jarvis = self.is_jarvis_name(clean_name or app_name)
        if target:
            try:
                if target.isMinimized:
                    try:
                        target.restore()
                    except Exception:
                        pass
                target.maximize()
                logger.info(f"Maximizing window '{target.title}' (requested: {app_name})")
                app_label = "J.A.R.V.I.S." if is_jarvis else (clean_name if clean_name else "window")
                return True, f"Maximizing {app_label}, sir."
            except Exception as e:
                logger.error(f"Error maximizing window '{target.title}': {e}")
                err_label = "J.A.R.V.I.S." if is_jarvis else (clean_name or "window")
                return False, f"Failed to maximize {err_label}, sir."

        # Fallback for active window
        if not clean_name:
            try:
                pyautogui.hotkey("win", "up")
                logger.info("Executed maximize window shortcut fallback.")
                return True, "Maximizing window, sir."
            except Exception as e:
                logger.error(f"Error maximizing window fallback: {e}")
                return False, "Failed to maximize window, sir."

        err_label = "J.A.R.V.I.S." if is_jarvis else clean_name
        return False, f"I could not find an open window for {err_label}, sir."

    def restore(self, app_name: Optional[str] = None) -> Tuple[bool, str]:
        """Restores a minimized or maximized window to normal size."""
        clean_name = self._clean_app_name(app_name)
        target = self.find_target_window(clean_name or app_name)
        is_jarvis = self.is_jarvis_name(clean_name or app_name)
        if target:
            try:
                target.restore()
                logger.info(f"Restored window '{target.title}' (requested: {app_name})")
                app_label = "J.A.R.V.I.S." if is_jarvis else (clean_name if clean_name else "window")
                return True, f"Restoring {app_label}, sir."
            except Exception as e:
                logger.error(f"Error restoring window '{target.title}': {e}")
                err_label = "J.A.R.V.I.S." if is_jarvis else (clean_name or "window")
                return False, f"Failed to restore {err_label}, sir."

        if not clean_name:
            try:
                pyautogui.hotkey("win", "down")
                return True, "Restoring window, sir."
            except Exception as e:
                return False, f"Failed to restore window: {e}"

        err_label = "J.A.R.V.I.S." if is_jarvis else clean_name
        return False, f"I could not find an open window for {err_label}, sir."

    def close(self, app_name: Optional[str] = None) -> Tuple[bool, str]:
        """Closes the specified application window or active user window gracefully."""
        clean_name = self._clean_app_name(app_name)
        target = self.find_target_window(clean_name or app_name)
        is_jarvis = self.is_jarvis_name(clean_name or app_name)
        if target:
            try:
                target.close()
                logger.info(f"Closed window '{target.title}' (requested: {app_name})")
                app_label = "J.A.R.V.I.S." if is_jarvis else (clean_name if clean_name else "window")
                return True, f"Closing {app_label}, sir."
            except Exception as e:
                logger.error(f"Error closing window '{target.title}': {e}")
                err_label = "J.A.R.V.I.S." if is_jarvis else (clean_name or "window")
                return False, f"Failed to close {err_label}, sir."

        # Fallback for active window
        if not clean_name:
            try:
                pyautogui.hotkey("alt", "f4")
                logger.info("Executed close active window shortcut fallback.")
                return True, "Closing window, sir."
            except Exception as e:
                logger.error(f"Error closing window fallback: {e}")
                return False, "Failed to close window, sir."

        return False, f"I could not find an open window for {clean_name}, sir."

    def close_active_window(self) -> Tuple[bool, str]:
        """Backward-compatible alias for close(None)."""
        return self.close(None)

    def show_desktop(self) -> Tuple[bool, str]:
        """Toggles show desktop using Win+D."""
        try:
            pyautogui.hotkey("win", "d")
            logger.info("Executed show desktop shortcut.")
            return True, "Showing desktop, sir."
        except Exception as e:
            logger.error(f"Error showing desktop: {e}")
            return False, "Failed to show desktop, sir."

    def switch_window(self) -> Tuple[bool, str]:
        """Switches to the next open window using Alt+Tab."""
        try:
            pyautogui.hotkey("alt", "tab")
            logger.info("Executed switch window shortcut.")
            return True, "Switching window, sir."
        except Exception as e:
            logger.error(f"Error switching window: {e}")
            return False, "Failed to switch window, sir."

    def snap_left(self, app_name: Optional[str] = None) -> Tuple[bool, str]:
        """Snaps the target or active window to the left half of the display."""
        clean_name = self._clean_app_name(app_name)
        target = self.find_target_window(clean_name)
        if target:
            self._activate_window(target)
        try:
            pyautogui.hotkey("win", "left")
            logger.info("Executed snap window left.")
            return True, "Snapping window to the left, sir."
        except Exception as e:
            logger.error(f"Error snapping window: {e}")
            return False, "Failed to snap window, sir."

    def snap_right(self, app_name: Optional[str] = None) -> Tuple[bool, str]:
        """Snaps the target or active window to the right half of the display."""
        clean_name = self._clean_app_name(app_name)
        target = self.find_target_window(clean_name)
        if target:
            self._activate_window(target)
        try:
            pyautogui.hotkey("win", "right")
            logger.info("Executed snap window right.")
            return True, "Snapping window to the right, sir."
        except Exception as e:
            logger.error(f"Error snapping window: {e}")
            return False, "Failed to snap window, sir."


# Global default instance
window_controller = WindowController()
