"""
Browser Automation Module for J.A.R.V.I.S.
------------------------------------------
Provides web search, active tab navigation, YouTube playback, and tab management
using PyAutoGUI and the system's default browser.
"""

import time
import urllib.parse
import webbrowser
from typing import Tuple

import pyautogui
import pygetwindow as gw
import pyperclip

from utils.logger import logger

pyautogui.FAILSAFE = False


class BrowserController:
    """Manages web browsing, active tab searching, and tab shortcuts."""

    GOOGLE_SEARCH_URL = "https://www.google.com/search?q="
    YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query="

    BROWSER_TITLES = ["chrome", "firefox", "edge", "brave", "opera", "vivaldi"]

    @classmethod
    def is_browser_focused(cls) -> bool:
        """Checks if a browser window is currently focused on the desktop."""
        try:
            active = gw.getActiveWindowTitle()
            if active:
                title_lower = active.lower()
                return any(b in title_lower for b in cls.BROWSER_TITLES)
        except Exception:
            pass
        return False

    @classmethod
    def focus_browser(cls) -> bool:
        """Attempts to bring an already-open browser window to the foreground."""
        try:
            for win in gw.getAllWindows():
                if win.title:
                    title_lower = win.title.lower()
                    if any(b in title_lower for b in cls.BROWSER_TITLES):
                        if not win.isActive:
                            win.activate()
                            time.sleep(0.2)
                        return True
        except Exception as e:
            logger.warning(f"Could not focus browser window: {e}")
        return False

    @classmethod
    def open_in_active_tab(cls, url: str) -> bool:
        """
        Navigates to a URL inside the currently active browser tab using Ctrl+L.
        Utilizes clipboard paste for instantaneous speed and special character support.
        """
        try:
            # Ensure browser is in the foreground
            cls.focus_browser()

            # Focus the address bar
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.2)

            # Paste URL instantly via clipboard
            pyperclip.copy(url)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.1)

            # Press Enter to execute search/navigate
            pyautogui.press("enter")
            return True
        except Exception as e:
            logger.warning(f"Failed to navigate active tab via hotkey ({e}). Falling back to webbrowser.open().")
            return False

    @classmethod
    def search_google(cls, query: str) -> Tuple[bool, str]:
        """
        Executes a Google search. Targets the currently active browser tab if open,
        otherwise opens a new browser window.

        :param query: Search terms or question
        :return: (success: bool, spoken_response: str)
        """
        query = query.strip()
        if not query:
            return False, "What would you like me to search for, sir?"

        encoded = urllib.parse.quote_plus(query)
        search_url = f"{cls.GOOGLE_SEARCH_URL}{encoded}"

        # If a browser is currently open or focused, use the active tab!
        if cls.is_browser_focused() or cls.focus_browser():
            logger.info(f"Searching in active browser tab: '{query}'")
            success = cls.open_in_active_tab(search_url)
            if success:
                return True, f"Searching for {query}, sir."

        # Fallback to standard webbrowser launch
        try:
            webbrowser.open(search_url)
            logger.info(f"Opened Google search in new browser window: '{query}'")
            return True, f"Searching Google for {query}, sir."
        except Exception as e:
            logger.error(f"Failed to open Google search for '{query}': {e}")
            return False, "I was unable to launch your web browser, sir."

    @classmethod
    def search_youtube(cls, query: str) -> Tuple[bool, str]:
        """
        Searches specifically on YouTube (sets session context to YouTube).
        """
        from core.context import context_manager
        context_manager.set("app", "youtube")
        return cls.play_youtube(query)

    @classmethod
    def play_youtube(cls, query: str) -> Tuple[bool, str]:
        """
        Searches and plays a video/song on YouTube in the active tab or browser.

        :param query: Name of song, artist, or video
        :return: (success: bool, spoken_response: str)
        """
        query = query.strip()
        if not query:
            return False, "What would you like to play on YouTube, sir?"

        encoded = urllib.parse.quote_plus(query)
        yt_url = f"{cls.YOUTUBE_SEARCH_URL}{encoded}"

        if cls.is_browser_focused() or cls.focus_browser():
            logger.info(f"Playing YouTube query in active tab: '{query}'")
            if cls.open_in_active_tab(yt_url):
                return True, f"Playing {query} on YouTube, sir."

        try:
            webbrowser.open(yt_url)
            return True, f"Playing {query} on YouTube, sir."
        except Exception as e:
            logger.error(f"Failed to open YouTube query for '{query}': {e}")
            return False, "I was unable to open YouTube, sir."

    @classmethod
    def execute_tab_command(cls, action: str) -> Tuple[bool, str]:
        """
        Executes browser shortcut controls (new tab, close tab, refresh, etc.).
        """
        cls.focus_browser()
        time.sleep(0.1)

        try:
            if action == "new_tab":
                pyautogui.hotkey("ctrl", "t")
                return True, "Opening a new tab, sir."
            elif action == "close_tab":
                pyautogui.hotkey("ctrl", "w")
                return True, "Closing tab, sir."
            elif action == "reopen_tab":
                pyautogui.hotkey("ctrl", "shift", "t")
                return True, "Reopening closed tab, sir."
            elif action == "next_tab":
                pyautogui.hotkey("ctrl", "tab")
                return True, "Next tab, sir."
            elif action == "prev_tab":
                pyautogui.hotkey("ctrl", "shift", "tab")
                return True, "Previous tab, sir."
            elif action == "refresh":
                pyautogui.press("f5")
                return True, "Refreshing page, sir."
            elif action == "back":
                pyautogui.hotkey("alt", "left")
                return True, "Going back, sir."
            elif action == "forward":
                pyautogui.hotkey("alt", "right")
                return True, "Going forward, sir."
            elif action == "new_window":
                pyautogui.hotkey("ctrl", "n")
                return True, "Opening new window, sir."
            elif action == "incognito":
                pyautogui.hotkey("ctrl", "shift", "n")
                return True, "Opening incognito window, sir."
            elif action == "scroll_down":
                pyautogui.press("pagedown")
                return True, "Scrolling down, sir."
            elif action == "scroll_up":
                pyautogui.press("pageup")
                return True, "Scrolling up, sir."
            elif action == "scroll_top":
                pyautogui.press("home")
                return True, "Scrolled to top of page, sir."
            elif action == "scroll_bottom":
                pyautogui.press("end")
                return True, "Scrolled to bottom of page, sir."
            elif action == "zoom_in":
                pyautogui.hotkey("ctrl", "+")
                return True, "Zooming in, sir."
            elif action == "zoom_out":
                pyautogui.hotkey("ctrl", "-")
                return True, "Zooming out, sir."
            elif action == "zoom_reset":
                pyautogui.hotkey("ctrl", "0")
                return True, "Reset zoom to normal, sir."
            elif action == "history":
                pyautogui.hotkey("ctrl", "h")
                return True, "Opening browser history, sir."
            elif action == "downloads":
                pyautogui.hotkey("ctrl", "j")
                return True, "Opening browser downloads, sir."
            elif action == "bookmarks":
                pyautogui.hotkey("ctrl", "shift", "o")
                return True, "Opening bookmarks, sir."
            elif action == "bookmark_page":
                pyautogui.hotkey("ctrl", "d")
                return True, "Bookmarking page, sir."
            elif action == "fullscreen":
                pyautogui.press("f11")
                return True, "Toggling full screen, sir."
            else:
                return False, "Unrecognized browser tab command, sir."
        except Exception as e:
            logger.error(f"Error executing browser shortcut '{action}': {e}")
            return False, "Failed to execute browser shortcut, sir."

    @classmethod
    def navigate_url(cls, url: str) -> Tuple[bool, str]:
        """
        Navigates directly to a target website or URL.
        :param url: Domain or URL string (e.g. 'github.com', 'https://openai.com')
        :return: (success: bool, spoken_response: str)
        """
        clean_url = url.strip()
        if not clean_url:
            return False, "No URL provided to navigate, sir."

        full_url = clean_url if clean_url.startswith(("http://", "https://")) else f"https://{clean_url}"

        # Extract domain name for speech
        domain = clean_url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

        if cls.is_browser_focused() or cls.focus_browser():
            logger.info(f"Navigating active tab to: {full_url}")
            if cls.open_in_active_tab(full_url):
                return True, f"Navigating to {domain}, sir."

        try:
            webbrowser.open(full_url)
            logger.info(f"Opened URL in new browser window: {full_url}")
            return True, f"Navigating to {domain}, sir."
        except Exception as e:
            logger.error(f"Failed to open URL '{full_url}': {e}")
            return False, f"I was unable to navigate to {domain}, sir."

    @classmethod
    def find_in_page(cls, query: str) -> Tuple[bool, str]:
        """
        Triggers Find in Page (Ctrl+F) and searches for text.
        :param query: Search terms to locate on current page
        :return: (success: bool, spoken_response: str)
        """
        clean_query = query.strip()
        if not clean_query:
            return False, "No search term provided for the page, sir."

        try:
            cls.focus_browser()
            time.sleep(0.1)
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.15)
            pyperclip.copy(clean_query)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.05)
            pyautogui.press("enter")
            logger.info(f"Find in page executed for: '{clean_query}'")
            return True, f"Searching page for {clean_query}, sir."
        except Exception as e:
            logger.error(f"Failed to execute find in page for '{clean_query}': {e}")
            return False, "Could not execute page search, sir."


# Global default instance
browser_controller = BrowserController()
