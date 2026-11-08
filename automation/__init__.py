"""Desktop Automation Package for J.A.R.V.I.S."""
from automation.app_launcher import AppLauncher, app_launcher
from automation.app_scanner import AppScanner, app_scanner
from automation.browser import BrowserController, browser_controller
from automation.clipboard_controller import ClipboardController, clipboard_controller
from automation.file_manager import FileManager, file_manager
from automation.media_controller import MediaController, media_controller
from automation.screenshot_controller import ScreenshotController, screenshot_controller
from automation.shortcut_controller import ShortcutController, shortcut_controller
from automation.spotify_controller import SpotifyController, spotify_controller
from automation.timer_manager import TimerManager, timer_manager
from automation.window_controller import WindowController, window_controller

__all__ = [
    "AppLauncher",
    "app_launcher",
    "AppScanner",
    "app_scanner",
    "BrowserController",
    "browser_controller",
    "ClipboardController",
    "clipboard_controller",
    "FileManager",
    "file_manager",
    "MediaController",
    "media_controller",
    "ScreenshotController",
    "screenshot_controller",
    "ShortcutController",
    "shortcut_controller",
    "SpotifyController",
    "spotify_controller",
    "TimerManager",
    "timer_manager",
    "WindowController",
    "window_controller",
]
