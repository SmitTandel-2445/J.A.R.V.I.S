"""
Application Scanner Module for J.A.R.V.I.S.
-------------------------------------------
Scans and indexes all installed desktop applications, Windows Store (UWP) apps,
shortcuts (.lnk), and popular web services on the user's PC.
Caches discovered apps to disk for instantaneous sub-millisecond retrieval.
"""

import json
import os
import threading
from typing import Dict, List, Optional, Tuple

import config
from utils.logger import logger

CACHE_DIR = config.DATA_DIR if hasattr(config, "DATA_DIR") else config.PROJECT_ROOT / "data"
CACHE_FILE = CACHE_DIR / "apps_cache.json"


class AppScanner:
    """Discovers, indexes, and resolves installed applications across the entire PC."""

    ALIASES: Dict[str, str] = {
        "vs code": "code",
        "visual studio code": "code",
        "code editor": "code",
        "chrome browser": "chrome",
        "google chrome": "chrome",
        "terminal": "windows terminal",
        "cmd": "command prompt",
        "command prompt": "cmd",
        "file manager": "file explorer",
        "explorer": "file explorer",
        "my pc": "file explorer",
        "this pc": "file explorer",
        "files": "file explorer",
        "photoshop": "adobe photoshop",
        "word": "winword",
        "ms word": "winword",
        "excel": "excel",
        "ms excel": "excel",
        "powerpoint": "powerpnt",
        "ms powerpoint": "powerpnt",
        "store": "microsoft store",
        "ms store": "microsoft store",
        "packet tracer": "cisco packet tracer",
    }

    SPECIAL_UWP_APPS: Dict[str, str] = {
        "spotify": "spotify:",
        "whatsapp": "whatsapp:",
        "microsoft store": "ms-windows-store:",
        "settings": "ms-settings:",
        "windows settings": "ms-settings:",
        "calculator": "calculator:",
        "photos": "ms-photos:",
        "camera": "microsoft.windows.camera:",
        "mail": "mailto:",
        "clock": "ms-clock:",
        "alarms": "ms-clock:",
    }

    WEB_SHORTCUTS: Dict[str, str] = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "github": "https://github.com",
        "stackoverflow": "https://stackoverflow.com",
        "reddit": "https://www.reddit.com",
        "twitter": "https://x.com",
        "x": "https://x.com",
        "facebook": "https://facebook.com",
        "instagram": "https://instagram.com",
        "linkedin": "https://linkedin.com",
        "gmail": "https://mail.google.com",
        "drive": "https://drive.google.com",
        "calendar": "https://calendar.google.com",
        "maps": "https://maps.google.com",
        "weather": "https://weather.com",
        "news": "https://news.google.com",
        "amazon": "https://amazon.in",
        "flipkart": "https://flipkart.com",
        "netflix": "https://netflix.com",
        "hotstar": "https://www.hotstar.com",
        "chatgpt": "https://chat.openai.com",
        "gemini": "https://gemini.google.com",
        "w3schools": "https://www.w3schools.com",
        "classroom": "https://classroom.google.com",
        "leetcode": "https://leetcode.com",
        "hackerrank": "https://hackerrank.com",
        "codeforces": "https://codeforces.com",
        "geeksforgeeks": "https://www.geeksforgeeks.org",
        "canva": "https://canva.com",
        "figma": "https://figma.com",
        "notion": "https://notion.so",
        "coursera": "https://coursera.org",
        "udemy": "https://udemy.com",
        "kaggle": "https://kaggle.com",
    }

    def __init__(self):
        self.installed_apps: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._init_cache()

    def _init_cache(self) -> None:
        """Loads cached apps from disk, then starts background refresh."""
        cached = self._load_cache()
        if cached:
            self.installed_apps = cached
            logger.info(f"Loaded {len(self.installed_apps)} applications from cache.")
        else:
            # First-time quick synchronous scan of Start Menu
            self._scan_start_menu_and_desktop()
            self._save_cache()

        # Trigger full scan in background so startup is instantaneous
        threading.Thread(
            target=self._full_background_scan,
            name="JARVIS-AppScanner",
            daemon=True,
        ).start()

    def _load_cache(self) -> Optional[Dict[str, str]]:
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            logger.warning("Failed to read application cache.")
        return None

    def _save_cache(self) -> None:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.installed_apps, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist application cache: {e}")

    def _scan_shortcuts(self, folder: str, target_dict: Dict[str, str]) -> None:
        if not os.path.exists(folder):
            return
        try:
            for root, _, files in os.walk(folder):
                for file in files:
                    ext = file.lower()
                    if ext.endswith((".lnk", ".url")):
                        name = os.path.splitext(file)[0].lower().strip()
                        target_dict[name] = os.path.join(root, file)
        except Exception:
            pass

    def _scan_exe_files(self, folder: str, target_dict: Dict[str, str], max_depth: int = 4) -> None:
        if not os.path.exists(folder):
            return
        try:
            for root, dirs, files in os.walk(folder):
                depth = root.count(os.sep)
                if depth > max_depth + 2:
                    dirs.clear()
                    continue

                for file in files:
                    if file.lower().endswith(".exe"):
                        name = os.path.splitext(file)[0].lower().strip()
                        target_dict.setdefault(name, os.path.join(root, file))
        except Exception:
            pass

    def _scan_start_menu_and_desktop(self) -> None:
        apps: Dict[str, str] = {}
        paths = [
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%USERPROFILE%\Desktop"),
            r"C:\Users\Public\Desktop",
        ]
        for p in paths:
            self._scan_shortcuts(p, apps)

        with self._lock:
            self.installed_apps.update(apps)

    def _full_background_scan(self) -> None:
        logger.info("Starting background scan of all installed applications...")
        apps: Dict[str, str] = {}

        # 1. Start Menu & Desktops
        paths = [
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%USERPROFILE%\Desktop"),
            r"C:\Users\Public\Desktop",
        ]
        for p in paths:
            self._scan_shortcuts(p, apps)

        # 2. Installed Program Directories
        program_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
            r"C:\Program Files",
            r"C:\Program Files (x86)",
        ]
        for p in program_paths:
            self._scan_exe_files(p, apps)

        with self._lock:
            self.installed_apps.update(apps)
            self._save_cache()

        logger.info(f"App scanner completed. Total indexed applications: {len(self.installed_apps)}")

    def resolve(self, query: str) -> Tuple[Optional[str], str]:
        """
        Resolves a spoken name into an executable path, UWP URI, or Web URL.

        :param query: Name spoken by user (e.g. 'chrome', 'whatsapp', 'github')
        :return: (resolved_path_or_uri: Optional[str], resolution_type: str)
                 types: 'uwp', 'web', 'file', 'unknown'
        """
        raw_name = query.lower().strip()
        for prefix in ("the ", "a "):
            if raw_name.startswith(prefix):
                raw_name = raw_name[len(prefix):].strip()

        # 1. Check Aliases
        app_name = self.ALIASES.get(raw_name, raw_name)

        # 2. Check UWP / Special Apps
        if app_name in self.SPECIAL_UWP_APPS:
            return self.SPECIAL_UWP_APPS[app_name], "uwp"

        # 3. Check Web Shortcuts
        if app_name in self.WEB_SHORTCUTS:
            return self.WEB_SHORTCUTS[app_name], "web"

        # 3.1 Check Domain or URL formats (e.g. 'reddit.com', 'wikipedia.org', 'https://...')
        import re
        if re.search(r"\.(?:com|org|net|edu|gov|io|ai|co|dev|app|in|uk|de|xyz)(?:/.*)?$", app_name) or app_name.startswith(("http://", "https://", "www.")):
            url = app_name if app_name.startswith(("http://", "https://")) else f"https://{app_name}"
            return url, "web"

        with self._lock:
            apps = dict(self.installed_apps)

        # 4. Exact match in indexed applications
        if app_name in apps:
            return apps[app_name], "file"

        # 5. Check direct PATH command (e.g. 'code', 'python', 'notepad', 'git')
        import shutil
        which_path = shutil.which(app_name)
        if which_path:
            return which_path, "file"

        # 6. Check with .exe extension
        if f"{app_name}.exe" in apps:
            return apps[f"{app_name}.exe"], "file"

        # 7. Word boundary match (e.g. 'code' in 'visual studio code', but NOT in 'codec')
        import re
        word_pattern = re.compile(rf"\b{re.escape(app_name)}\b", re.IGNORECASE)
        for name, path in apps.items():
            if word_pattern.search(name):
                return path, "file"

        # 8. Substring match (e.g. 'chrome' inside 'google chrome')
        for name, path in apps.items():
            if app_name in name:
                return path, "file"

        # 9. Ignore-spaces match ('packettracer' -> 'packet tracer')
        clean_target = app_name.replace(" ", "")
        for name, path in apps.items():
            if clean_target in name.replace(" ", ""):
                return path, "file"

        return None, "unknown"


# Global default instance
app_scanner = AppScanner()
