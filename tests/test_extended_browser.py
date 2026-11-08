"""
Unit Tests for Extended Browser & Navigation Automations Module
----------------------------------------------------------------
Validates intent classification, controller functions (page scroll, zoom,
history, downloads, bookmarks, full screen, find in page, direct URL navigation),
domain resolution in AppScanner, and router dispatch with compound commands.
"""

import unittest
from unittest.mock import MagicMock, patch

from automation.app_scanner import app_scanner
from automation.browser import BrowserController
from core.context import ContextManager
from core.router import ActionRouter
from nlp.intent_classifier import IntentClassifier, IntentType


class TestExtendedBrowserIntentClassification(unittest.TestCase):
    """Verifies that voice queries map accurately to extended browser intents."""

    def setUp(self):
        self.classifier = IntentClassifier()

    def test_scroll_queries(self):
        cases = [
            ("scroll down", "scroll_down"),
            ("scroll down the page", "scroll_down"),
            ("page down", "scroll_down"),
            ("scroll up", "scroll_up"),
            ("page up", "scroll_up"),
            ("scroll to top", "scroll_top"),
            ("top of page", "scroll_top"),
            ("scroll to bottom", "scroll_bottom"),
            ("bottom of page", "scroll_bottom"),
        ]
        for q, expected_act in cases:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.BROWSER_TAB)
                self.assertEqual(res.parameters.get("action"), expected_act)

    def test_zoom_queries(self):
        cases = [
            ("zoom in", "zoom_in"),
            ("increase zoom", "zoom_in"),
            ("zoom out", "zoom_out"),
            ("decrease zoom", "zoom_out"),
            ("reset zoom", "zoom_reset"),
            ("normal zoom", "zoom_reset"),
            ("default zoom", "zoom_reset"),
        ]
        for q, expected_act in cases:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.BROWSER_TAB)
                self.assertEqual(res.parameters.get("action"), expected_act)

    def test_browser_utilities_queries(self):
        cases = [
            ("browser history", "history"),
            ("show history", "history"),
            ("open history", "history"),
            ("browser downloads", "downloads"),
            ("show browser downloads", "downloads"),
            ("open bookmarks", "bookmarks"),
            ("browser bookmarks", "bookmarks"),
            ("bookmark this page", "bookmark_page"),
            ("bookmark page", "bookmark_page"),
            ("full screen", "fullscreen"),
            ("browser full screen", "fullscreen"),
            ("toggle full screen", "fullscreen"),
        ]
        for q, expected_act in cases:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.BROWSER_TAB)
                self.assertEqual(res.parameters.get("action"), expected_act)

    def test_find_in_page_queries(self):
        cases = [
            ("find in page machine learning", "machine learning"),
            ("search this page for quantum computing", "quantum computing"),
            ("search page for Python 3.12", "Python 3.12"),
        ]
        for q, expected_query in cases:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.BROWSER_TAB)
                self.assertEqual(res.parameters.get("action"), "find")
                self.assertEqual(res.parameters.get("query"), expected_query)

    def test_direct_navigation_queries(self):
        cases = [
            ("go to github.com", "github.com"),
            ("navigate to reddit.com", "reddit.com"),
            ("open website wikipedia.org", "wikipedia.org"),
            ("open https://openai.com", "https://openai.com"),
        ]
        for q, expected_url in cases:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.BROWSER_TAB)
                self.assertEqual(res.parameters.get("action"), "navigate")
                self.assertEqual(res.parameters.get("url"), expected_url)


class TestAppScannerDomainResolution(unittest.TestCase):
    """Verifies that domains resolve directly to web URLs in AppScanner."""

    def test_domain_resolutions(self):
        cases = [
            ("reddit.com", "https://reddit.com"),
            ("wikipedia.org", "https://wikipedia.org"),
            ("huggingface.co", "https://huggingface.co"),
            ("openai.com", "https://openai.com"),
        ]
        for domain, expected_url in cases:
            with self.subTest(domain=domain):
                resolved, res_type = app_scanner.resolve(domain)
                self.assertEqual(res_type, "web")
                self.assertEqual(resolved, expected_url)


class TestBrowserControllerExtended(unittest.TestCase):
    """Tests the standalone functionality of BrowserController extended actions."""

    def setUp(self):
        self.browser = BrowserController()

    @patch("pyautogui.press")
    def test_scroll_actions(self, mock_press):
        success, speech = self.browser.execute_tab_command("scroll_down")
        self.assertTrue(success)
        mock_press.assert_called_with("pagedown")

        success, speech = self.browser.execute_tab_command("scroll_top")
        self.assertTrue(success)
        mock_press.assert_called_with("home")

    @patch("pyautogui.hotkey")
    def test_zoom_actions(self, mock_hotkey):
        success, speech = self.browser.execute_tab_command("zoom_in")
        self.assertTrue(success)
        mock_hotkey.assert_called_with("ctrl", "+")

        success, speech = self.browser.execute_tab_command("zoom_reset")
        self.assertTrue(success)
        mock_hotkey.assert_called_with("ctrl", "0")

    @patch("pyautogui.hotkey")
    def test_history_and_downloads(self, mock_hotkey):
        success, speech = self.browser.execute_tab_command("history")
        self.assertTrue(success)
        mock_hotkey.assert_called_with("ctrl", "h")

        success, speech = self.browser.execute_tab_command("downloads")
        self.assertTrue(success)
        mock_hotkey.assert_called_with("ctrl", "j")

    @patch("pyautogui.hotkey")
    @patch("pyautogui.press")
    def test_find_in_page(self, mock_press, mock_hotkey):
        success, speech = self.browser.find_in_page("neural network")
        self.assertTrue(success)
        self.assertIn("neural network", speech)
        mock_press.assert_called_with("enter")

    @patch("webbrowser.open")
    def test_navigate_url(self, mock_web_open):
        with patch.object(self.browser, "is_browser_focused", return_value=False), \
             patch.object(self.browser, "focus_browser", return_value=False):
            success, speech = self.browser.navigate_url("github.com")
            self.assertTrue(success)
            self.assertIn("github.com", speech)
            mock_web_open.assert_called_with("https://github.com")


class TestActionRouterExtendedBrowser(unittest.TestCase):
    """Tests ActionRouter routing for extended browser actions."""

    def setUp(self):
        self.context = ContextManager()
        self.router = ActionRouter(context_manager=self.context)

    @patch("pyautogui.press")
    def test_route_scroll(self, mock_press):
        res = self.router.route("scroll down")
        self.assertEqual(res.intent, IntentType.BROWSER_TAB)
        self.assertTrue(res.success)
        self.assertIn("Scrolling down", res.spoken_response)

    @patch("pyautogui.hotkey")
    def test_route_zoom(self, mock_hotkey):
        res = self.router.route("zoom in")
        self.assertEqual(res.intent, IntentType.BROWSER_TAB)
        self.assertTrue(res.success)
        self.assertIn("Zooming in", res.spoken_response)

    @patch("webbrowser.open")
    def test_route_navigate_url(self, mock_web_open):
        with patch.object(self.router.browser_controller, "is_browser_focused", return_value=False), \
             patch.object(self.router.browser_controller, "focus_browser", return_value=False):
            res = self.router.route("go to github.com")
            self.assertEqual(res.intent, IntentType.BROWSER_TAB)
            self.assertTrue(res.success)
            self.assertIn("github.com", res.spoken_response)

    @patch("pyautogui.press")
    @patch("pyautogui.hotkey")
    def test_compound_browser_command(self, mock_hotkey, mock_press):
        intents = self.router.classifier.classify_multi("scroll down and zoom in")
        self.assertEqual(len(intents), 2)
        self.assertEqual(intents[0].intent, IntentType.BROWSER_TAB)
        self.assertEqual(intents[0].parameters.get("action"), "scroll_down")
        self.assertEqual(intents[1].intent, IntentType.BROWSER_TAB)
        self.assertEqual(intents[1].parameters.get("action"), "zoom_in")

        res = self.router.route("scroll down and zoom in")
        self.assertTrue(res.success)
        self.assertIn("Scrolling down", res.spoken_response)
        self.assertIn("zooming in", res.spoken_response.lower())


if __name__ == "__main__":
    unittest.main()

