"""
Comprehensive Unit Tests for All Remaining Phase 5 Features
------------------------------------------------------------
Validates:
1. Network: Connect Wi-Fi
2. Task Manager: System Uptime
3. File Manager: Open Latest Download
4. Productivity: Timers, Alarms, Reminders, and Focus Sessions
5. Multi-Monitor & Theme Display Controls
6. Global Shortcuts & Microphone Mute
7. Compound Command Execution across new features
"""

import unittest
from unittest.mock import MagicMock, patch

from automation.file_manager import FileManager
from automation.shortcut_controller import ShortcutController
from automation.timer_manager import TimerManager
from core.context import ContextManager
from core.router import ActionRouter
from nlp.intent_classifier import IntentClassifier, IntentType
from system.display_controller import DisplayController
from system.network_controller import NetworkController
from system.task_manager import TaskManager


class TestRemainingIntentClassification(unittest.TestCase):
    """Verifies intent recognition for all newly added features."""

    def setUp(self):
        self.classifier = IntentClassifier()

    def test_connect_wifi_queries(self):
        queries = [
            "turn on wifi",
            "turn wifi back on",
            "connect to wifi",
            "reconnect wifi",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.NETWORK)
                self.assertEqual(res.parameters.get("action"), "connect_wifi")

    def test_uptime_queries(self):
        queries = [
            "how long has my pc been on",
            "how long has my pc been running",
            "check system uptime",
            "system uptime",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.TASK_MANAGER)
                self.assertEqual(res.parameters.get("action"), "uptime")

    def test_latest_download_queries(self):
        queries = [
            "open my latest download",
            "open latest downloaded file",
            "what did i just download",
            "open last download",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.FILE_FOLDER)
                self.assertEqual(res.parameters.get("action"), "latest_download")

    def test_timer_queries(self):
        res1 = self.classifier.classify("set a timer for 10 minutes")
        self.assertEqual(res1.intent, IntentType.TIMER)
        self.assertEqual(res1.parameters.get("action"), "set_timer")
        self.assertEqual(res1.parameters.get("seconds"), 600)

        res2 = self.classifier.classify("how much time is left on my timer")
        self.assertEqual(res2.intent, IntentType.TIMER)
        self.assertEqual(res2.parameters.get("action"), "status")

        res3 = self.classifier.classify("cancel timer")
        self.assertEqual(res3.intent, IntentType.TIMER)
        self.assertEqual(res3.parameters.get("action"), "cancel")

    def test_reminder_queries(self):
        res = self.classifier.classify("remind me in 30 minutes to take a break")
        self.assertEqual(res.intent, IntentType.TIMER)
        self.assertEqual(res.parameters.get("action"), "set_reminder")
        self.assertEqual(res.parameters.get("seconds"), 1800)
        self.assertEqual(res.parameters.get("message"), "take a break")

    def test_focus_session_queries(self):
        res1 = self.classifier.classify("start a 25-minute focus session")
        self.assertEqual(res1.intent, IntentType.TIMER)
        self.assertEqual(res1.parameters.get("action"), "focus_session")
        self.assertEqual(res1.parameters.get("minutes"), 25)

        res2 = self.classifier.classify("focus session")
        self.assertEqual(res2.intent, IntentType.TIMER)
        self.assertEqual(res2.parameters.get("action"), "focus_session")

    def test_display_queries(self):
        res1 = self.classifier.classify("move window to the second monitor")
        self.assertEqual(res1.intent, IntentType.DISPLAY)
        self.assertEqual(res1.parameters.get("action"), "move_monitor")

        res2 = self.classifier.classify("switch to dark mode")
        self.assertEqual(res2.intent, IntentType.DISPLAY)
        self.assertEqual(res2.parameters.get("action"), "theme")
        self.assertEqual(res2.parameters.get("mode"), "dark")

        res3 = self.classifier.classify("switch to light mode")
        self.assertEqual(res3.intent, IntentType.DISPLAY)
        self.assertEqual(res3.parameters.get("action"), "theme")
        self.assertEqual(res3.parameters.get("mode"), "light")

        res4 = self.classifier.classify("turn on night light")
        self.assertEqual(res4.intent, IntentType.DISPLAY)
        self.assertEqual(res4.parameters.get("action"), "night_light")

    def test_shortcut_queries(self):
        cases = [
            ("save file", "save"),
            ("select all", "select_all"),
            ("undo", "undo"),
            ("redo", "redo"),
        ]
        for q, expected_act in cases:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.SHORTCUT)
                self.assertEqual(res.parameters.get("action"), expected_act)

    def test_mic_mute_queries(self):
        res1 = self.classifier.classify("mute my microphone")
        self.assertEqual(res1.intent, IntentType.SHORTCUT)
        self.assertEqual(res1.parameters.get("action"), "mute_mic")

        res2 = self.classifier.classify("unmute mic")
        self.assertEqual(res2.intent, IntentType.SHORTCUT)
        self.assertEqual(res2.parameters.get("action"), "unmute_mic")


class TestControllers(unittest.TestCase):
    """Direct method tests for controllers."""

    def test_system_uptime(self):
        success, speech, data = TaskManager.get_system_uptime()
        self.assertTrue(success)
        self.assertIn("running continuously", speech)
        self.assertIn("total_seconds", data)

    @patch("subprocess.run")
    def test_connect_wifi(self, mock_run):
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Connection request was completed successfully."
        mock_res.stderr = ""
        mock_run.return_value = mock_res

        success, speech = NetworkController.connect_wifi()
        self.assertTrue(success)
        self.assertIn("Reconnecting to Wi-Fi", speech)

    def test_timer_manager_cycle(self):
        tm = TimerManager()
        # Set a 60 second timer
        success, speech = tm.set_timer(60, "study")
        self.assertTrue(success)
        self.assertIn("Timer set for", speech)

        # Check status
        st_success, st_speech = tm.get_timer_status()
        self.assertTrue(st_success)
        self.assertIn("remaining on your study", st_speech)

        # Cancel timer
        c_success, c_speech = tm.cancel_timer()
        self.assertTrue(c_success)
        self.assertIn("cancelled", c_speech)

    def test_focus_session(self):
        tm = TimerManager()
        success, speech = tm.start_focus_session(25)
        self.assertTrue(success)
        self.assertIn("25-minute focus session", speech)
        tm.cancel_timer()

    @patch("pyautogui.hotkey")
    def test_display_move(self, mock_hotkey):
        success, speech = DisplayController.move_window_to_monitor("right")
        self.assertTrue(success)
        mock_hotkey.assert_called_with("win", "shift", "right")

    @patch("pyautogui.hotkey")
    def test_shortcut_dispatch(self, mock_hotkey):
        success, speech = ShortcutController.execute_shortcut("save")
        self.assertTrue(success)
        mock_hotkey.assert_called_with("ctrl", "s")
        self.assertIn("saved", speech.lower())


class TestRouterIntegration(unittest.TestCase):
    """End-to-end router testing for all remaining features."""

    def setUp(self):
        self.context = ContextManager()
        self.router = ActionRouter(context_manager=self.context)

    def test_route_uptime(self):
        res = self.router.route("check system uptime")
        self.assertEqual(res.intent, IntentType.TASK_MANAGER)
        self.assertTrue(res.success)
        self.assertIn("running continuously", res.spoken_response)

    def test_route_timer_and_status(self):
        res1 = self.router.route("set a timer for 5 minutes")
        self.assertEqual(res1.intent, IntentType.TIMER)
        self.assertTrue(res1.success)

        res2 = self.router.route("how much time is left on my timer")
        self.assertEqual(res2.intent, IntentType.TIMER)
        self.assertTrue(res2.success)
        self.assertIn("remaining", res2.spoken_response)

        res3 = self.router.route("cancel timer")
        self.assertEqual(res3.intent, IntentType.TIMER)
        self.assertTrue(res3.success)

    @patch("pyautogui.hotkey")
    def test_route_save_file(self, mock_hotkey):
        res = self.router.route("save file")
        self.assertEqual(res.intent, IntentType.SHORTCUT)
        self.assertTrue(res.success)
        self.assertIn("File saved", res.spoken_response)

    @patch("pyautogui.hotkey")
    def test_compound_remaining_features(self, mock_hotkey):
        intents = self.router.classifier.classify_multi("save file and check system uptime")
        self.assertEqual(len(intents), 2)
        self.assertEqual(intents[0].intent, IntentType.SHORTCUT)
        self.assertEqual(intents[1].intent, IntentType.TASK_MANAGER)

        res = self.router.route("save file and check system uptime")
        self.assertTrue(res.success)
        self.assertIn("File saved", res.spoken_response)
        self.assertIn("running continuously", res.spoken_response)


if __name__ == "__main__":
    unittest.main()

