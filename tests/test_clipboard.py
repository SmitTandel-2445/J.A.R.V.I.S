"""
Unit Tests for Clipboard & Text Automation Module
--------------------------------------------------
Validates intent classification, controller functions (read, copy, clear, type),
and router dispatch including compound multi-command sequences.
"""

import unittest
from unittest.mock import MagicMock, patch
import pyperclip

from automation.clipboard_controller import ClipboardController
from core.context import ContextManager
from core.router import ActionRouter
from nlp.intent_classifier import IntentClassifier, IntentType


class TestClipboardIntentClassification(unittest.TestCase):
    """Verifies that voice queries map accurately to clipboard automation intents."""

    def setUp(self):
        self.classifier = IntentClassifier()

    def test_read_clipboard_queries(self):
        queries = [
            "read clipboard",
            "read my clipboard",
            "what's on my clipboard",
            "what is on the clipboard",
            "check clipboard",
            "check my clipboard",
            "clipboard contents",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.CLIPBOARD)
                self.assertEqual(res.parameters.get("action"), "read")

    def test_copy_last_response_queries(self):
        queries = [
            "copy that",
            "copy that to clipboard",
            "copy this to my clipboard",
            "copy the last answer",
            "copy the last response to clipboard",
            "copy to clipboard",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.CLIPBOARD)
                self.assertEqual(res.parameters.get("action"), "copy_last")

    def test_copy_explicit_text_queries(self):
        queries = [
            ("copy hello world to clipboard", "hello world"),
            ("copy stark industries to my clipboard", "stark industries"),
            ("copy 192.168.1.1 to the clipboard", "192.168.1.1"),
        ]
        for q, expected_text in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.CLIPBOARD)
                self.assertEqual(res.parameters.get("action"), "copy")
                self.assertEqual(res.parameters.get("text"), expected_text)

    def test_clear_clipboard_queries(self):
        queries = [
            "clear clipboard",
            "clear my clipboard",
            "empty clipboard",
            "clean clipboard",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.CLIPBOARD)
                self.assertEqual(res.parameters.get("action"), "clear")

    def test_voice_type_queries(self):
        queries = [
            ("type hello world", "hello world"),
            ("type this out: test message", "test message"),
            ("write this down: meeting at 3 PM", "meeting at 3 PM"),
            ("write Welcome to JARVIS", "Welcome to JARVIS"),
        ]
        for q, expected_text in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.CLIPBOARD)
                self.assertEqual(res.parameters.get("action"), "type")
                self.assertEqual(res.parameters.get("text"), expected_text)


class TestClipboardController(unittest.TestCase):
    """Tests the standalone functionality of ClipboardController."""

    def setUp(self):
        self.controller = ClipboardController()
        # Save real clipboard content to restore after tests
        try:
            self._original_clip = pyperclip.paste()
        except Exception:
            self._original_clip = ""

    def tearDown(self):
        try:
            pyperclip.copy(self._original_clip)
        except Exception:
            pass

    def test_copy_and_read(self):
        success, speech = self.controller.copy("JARVIS Protocol Alpha")
        self.assertTrue(success)
        self.assertIn("Copied", speech)

        read_success, read_speech, text = self.controller.read()
        self.assertTrue(read_success)
        self.assertEqual(text, "JARVIS Protocol Alpha")
        self.assertIn("JARVIS Protocol Alpha", read_speech)

    def test_clear_clipboard(self):
        self.controller.copy("Temporary text")
        clear_success, clear_speech = self.controller.clear()
        self.assertTrue(clear_success)

        read_success, read_speech, text = self.controller.read()
        self.assertTrue(read_success)
        self.assertEqual(text, "")
        self.assertIn("empty", read_speech.lower())

    def test_read_long_text_summarization(self):
        long_text = "A" * 300
        self.controller.copy(long_text)
        read_success, read_speech, text = self.controller.read()
        self.assertTrue(read_success)
        self.assertEqual(len(text), 300)
        self.assertIn("contains 300 characters", read_speech)

    @patch("pyautogui.hotkey")
    def test_type_text(self, mock_hotkey):
        success, speech = self.controller.type_text("Automated keystroke test")
        self.assertTrue(success)
        self.assertIn("Typed:", speech)
        mock_hotkey.assert_called_with("ctrl", "v")


class TestActionRouterClipboard(unittest.TestCase):
    """Tests ActionRouter routing for clipboard actions."""

    def setUp(self):
        self.context = ContextManager()
        self.router = ActionRouter(context_manager=self.context)

    def test_route_copy_and_read(self):
        res_copy = self.router.route("copy Quantum Computing to clipboard")
        self.assertEqual(res_copy.intent, IntentType.CLIPBOARD)
        self.assertTrue(res_copy.success)

        res_read = self.router.route("read clipboard")
        self.assertEqual(res_read.intent, IntentType.CLIPBOARD)
        self.assertTrue(res_read.success)
        self.assertIn("Quantum Computing", res_read.spoken_response)

    def test_route_copy_last_response(self):
        # Set simulated previous response in context
        self.context.set("last_ai_reply", "Paris is the capital of France.")
        res = self.router.route("copy that to clipboard")
        self.assertEqual(res.intent, IntentType.CLIPBOARD)
        self.assertTrue(res.success)

        # Verify clipboard has Paris
        _, _, text = self.router.clipboard_controller.read()
        self.assertEqual(text, "Paris is the capital of France.")

    def test_route_copy_last_when_empty(self):
        # Empty context
        self.context.clear()
        res = self.router.route("copy that to clipboard")
        self.assertEqual(res.intent, IntentType.CLIPBOARD)
        self.assertFalse(res.success)
        self.assertIn("recent response", res.spoken_response.lower())

    def test_compound_command_with_clipboard(self):
        # Test split and sequential execution of compound command
        intents = self.router.classifier.classify_multi("copy test string to clipboard and then read clipboard")
        self.assertEqual(len(intents), 2)
        self.assertEqual(intents[0].intent, IntentType.CLIPBOARD)
        self.assertEqual(intents[0].parameters.get("action"), "copy")
        self.assertEqual(intents[1].intent, IntentType.CLIPBOARD)
        self.assertEqual(intents[1].parameters.get("action"), "read")

        # Execute compound route
        res = self.router.route("copy hello compound to clipboard and read clipboard")
        self.assertTrue(res.success)
        self.assertIn("Copied to clipboard", res.spoken_response)
        self.assertIn("hello compound", res.spoken_response)


if __name__ == "__main__":
    unittest.main()
