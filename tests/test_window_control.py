"""
Tests for Window Management Automation in J.A.R.V.I.S.
------------------------------------------------------
Verifies:
1. Intent Classifier correctly classifies active window commands (minimize, maximize, close).
2. Intent Classifier correctly extracts target application names for specific window controls.
3. Router dispatches window commands properly.
4. WindowController accurately locates, minimizes, maximizes, and closes target application windows.
"""

import os
import subprocess
import time
import unittest

from nlp.intent_classifier import IntentClassifier, IntentType
from automation.window_controller import WindowController
from core.router import ActionRouter


class TestWindowControl(unittest.TestCase):
    def setUp(self):
        self.classifier = IntentClassifier()
        self.window_controller = WindowController()
        self.router = ActionRouter()

    def test_active_window_intent_classification(self):
        """Tests that active window commands correctly map to WINDOW_CONTROL with no app_name."""
        test_cases = [
            ("minimize window", "minimize"),
            ("minimize the window", "minimize"),
            ("minimize this window", "minimize"),
            ("minimize active window", "minimize"),
            ("minimize", "minimize"),
            ("maximize window", "maximize"),
            ("maximize the window", "maximize"),
            ("maximize this window", "maximize"),
            ("maximize", "maximize"),
            ("restore window", "restore"),
            ("close window", "close"),
            ("close the window", "close"),
            ("close this window", "close"),
            ("close active window", "close"),
            ("show desktop", "desktop"),
            ("switch window", "switch"),
            ("snap left", "snap_left"),
            ("snap window left", "snap_left"),
            ("snap right", "snap_right"),
            ("snap window right", "snap_right"),
        ]

        for phrase, expected_action in test_cases:
            with self.subTest(phrase=phrase):
                res = self.classifier.classify(phrase)
                self.assertEqual(res.intent, IntentType.WINDOW_CONTROL, f"Failed for '{phrase}': got {res.intent}")
                self.assertEqual(res.parameters.get("action"), expected_action)
                self.assertIsNone(res.parameters.get("app_name"))

    def test_specific_application_window_intent_classification(self):
        """Tests that specific named app window commands extract the app_name parameter."""
        test_cases = [
            ("minimize chrome", "minimize", "chrome"),
            ("minimize vs code", "minimize", "vs code"),
            ("minimize notepad", "minimize", "notepad"),
            ("minimize spotify", "minimize", "spotify"),
            ("maximize chrome", "maximize", "chrome"),
            ("maximize vs code", "maximize", "vs code"),
            ("maximize spotify", "maximize", "spotify"),
            ("restore chrome", "restore", "chrome"),
            ("close notepad window", "close", "notepad"),
            ("close chrome window", "close", "chrome"),
        ]

        for phrase, expected_action, expected_app in test_cases:
            with self.subTest(phrase=phrase):
                res = self.classifier.classify(phrase)
                self.assertEqual(res.intent, IntentType.WINDOW_CONTROL, f"Failed for '{phrase}': got {res.intent}")
                self.assertEqual(res.parameters.get("action"), expected_action)
                self.assertEqual(res.parameters.get("app_name"), expected_app)

    def test_close_app_intent_classification(self):
        """Tests that 'close <app>' maps to CLOSE_APP and preserves app_name."""
        test_cases = [
            ("close chrome", "chrome"),
            ("close notepad", "notepad"),
            ("exit spotify", "spotify"),
            ("terminate vs code", "vs code"),
        ]

        for phrase, expected_app in test_cases:
            with self.subTest(phrase=phrase):
                res = self.classifier.classify(phrase)
                self.assertEqual(res.intent, IntentType.CLOSE_APP, f"Failed for '{phrase}': got {res.intent}")
                self.assertEqual(res.parameters.get("app_name"), expected_app)

    def test_real_window_lifecycle_with_notepad(self):
        """Spawns Notepad and verifies find, maximize, minimize, restore, and close."""
        proc = subprocess.Popen(["notepad.exe"])
        time.sleep(1.0)
        try:
            # 1. Locate window by app name
            target = self.window_controller.find_target_window("notepad")
            self.assertIsNotNone(target, "Failed to find Notepad window by name")

            # 2. Maximize
            success, msg = self.window_controller.maximize("notepad")
            self.assertTrue(success)
            self.assertIn("Maximizing notepad", msg)

            # 3. Minimize
            success, msg = self.window_controller.minimize("notepad")
            self.assertTrue(success)
            self.assertIn("Minimizing notepad", msg)

            # 4. Restore
            success, msg = self.window_controller.restore("notepad")
            self.assertTrue(success)
            self.assertIn("Restoring notepad", msg)

            # 5. Router dispatch test for close
            action_res = self.router.route("close notepad window")
            self.assertTrue(action_res.success)
            self.assertIn("Closing notepad", action_res.spoken_response)

            time.sleep(0.5)
            # Process should be closed now
            self.assertIsNotNone(proc.poll(), "Notepad process should have terminated after close")

        finally:
            if proc.poll() is None:
                proc.terminate()

    def test_jarvis_self_window_control(self):
        """Verifies that J.A.R.V.I.S. can identify and manipulate its own application window."""
        import tkinter as tk

        # 1. Test name identification helper
        self.assertTrue(self.window_controller.is_jarvis_name("jarvis"))
        self.assertTrue(self.window_controller.is_jarvis_name("yourself"))
        self.assertTrue(self.window_controller.is_jarvis_name("your window"))
        self.assertTrue(self.window_controller.is_jarvis_name("own window"))
        self.assertTrue(self.window_controller.is_jarvis_name("self"))
        self.assertFalse(self.window_controller.is_jarvis_name("chrome"))
        self.assertFalse(self.window_controller.is_jarvis_name("notepad"))
        self.assertFalse(self.window_controller.is_jarvis_name(None))

        # 2. Create a mock J.A.R.V.I.S. window in the current process
        root = tk.Tk()
        root.title("J.A.R.V.I.S")
        root.update()

        try:
            # 3. Locate window explicitly referencing JARVIS
            target = self.window_controller.find_target_window("jarvis")
            self.assertIsNotNone(target, "Failed to find J.A.R.V.I.S. window by name 'jarvis'")
            self.assertEqual(target.title, "J.A.R.V.I.S")

            target_self = self.window_controller.find_target_window("yourself")
            self.assertIsNotNone(target_self, "Failed to find J.A.R.V.I.S. window by alias 'yourself'")

            target_your = self.window_controller.find_target_window("your window")
            self.assertIsNotNone(target_your, "Failed to find J.A.R.V.I.S. window by alias 'your window'")

            # 4. Minimize J.A.R.V.I.S. window
            ok, speech = self.window_controller.minimize("jarvis")
            root.update()
            self.assertTrue(ok)
            self.assertEqual(speech, "Minimizing J.A.R.V.I.S., sir.")
            self.assertTrue(target.isMinimized)

            # 5. Restore J.A.R.V.I.S. window
            ok, speech = self.window_controller.restore("yourself")
            root.update()
            self.assertTrue(ok)
            self.assertEqual(speech, "Restoring J.A.R.V.I.S., sir.")
            self.assertFalse(target.isMinimized)

            # 6. Maximize J.A.R.V.I.S. window
            ok, speech = self.window_controller.maximize("your window")
            root.update()
            self.assertTrue(ok)
            self.assertEqual(speech, "Maximizing J.A.R.V.I.S., sir.")
            self.assertTrue(target.isMaximized)

            # 7. Restore again
            ok, speech = self.window_controller.restore("own window")
            root.update()
            self.assertTrue(ok)
            self.assertEqual(speech, "Restoring J.A.R.V.I.S., sir.")
            self.assertFalse(target.isMaximized)

        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
