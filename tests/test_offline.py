"""
Tests for Voice-Activated 'Go Offline' / Farewell Automation in J.A.R.V.I.S.
----------------------------------------------------------------------------
Verifies:
1. "bye jarvis", "good bye jarvis", "go offline", etc. map to IntentType.GO_OFFLINE.
2. Negative commands like "stop music", "close chrome", "play bye" do not collide.
3. ActionRouter handles GO_OFFLINE and produces a polite spoken farewell.
"""

import unittest
from nlp.intent_classifier import IntentClassifier, IntentType
from core.router import ActionRouter


class TestOfflineAutomation(unittest.TestCase):
    def setUp(self):
        self.classifier = IntentClassifier()
        self.router = ActionRouter()

    def test_offline_intent_classification(self):
        """Tests that various farewell and offline voice commands classify as GO_OFFLINE."""
        phrases = [
            "bye jarvis",
            "good bye jarvis",
            "goodbye jarvis",
            "bye",
            "goodbye",
            "good bye",
            "bye bye",
            "bye bye jarvis",
            "go offline",
            "go to offline",
            "go into offline",
            "go offline now",
            "offline mode",
            "go offline jarvis",
            "jarvis go offline",
            "offline",
            "system offline",
            "jarvis offline",
            "halt",
            "system halt",
            "jarvis halt",
            "shut down",
            "shutdown",
            "turn off",
            "turn off jarvis",
            "power down",
            "power down jarvis",
            "power off",
            "power off jarvis",
            "offline jarvis",
            "see you jarvis",
            "see you later jarvis",
            "stop listening",
            "stop listening jarvis",
            "jarvis stop listening",
            "shut down jarvis",
            "shutdown jarvis",
            "jarvis shutdown",
            "sleep jarvis",
            "go to sleep jarvis",
            "exit jarvis",
            "quit jarvis",
        ]

        for phrase in phrases:
            with self.subTest(phrase=phrase):
                res = self.classifier.classify(phrase)
                self.assertEqual(
                    res.intent,
                    IntentType.GO_OFFLINE,
                    f"Expected GO_OFFLINE for '{phrase}', got '{res.intent}'",
                )
                self.assertEqual(res.parameters.get("action"), "offline")

    def test_offline_negative_cases(self):
        """Tests that normal commands containing words like 'stop' or 'bye' do not trigger offline."""
        negative_cases = [
            ("stop music", IntentType.MEDIA_CONTROL),
            ("close chrome", IntentType.CLOSE_APP),
            ("play bye bye bye", IntentType.PLAY_MEDIA),
            ("search good bye messages", IntentType.WEB_SEARCH),
            ("lock screen", IntentType.SYSTEM_POWER),
            ("sleep", IntentType.SYSTEM_POWER),
            ("go to sleep", IntentType.SYSTEM_POWER),
        ]

        for phrase, expected_intent in negative_cases:
            with self.subTest(phrase=phrase):
                res = self.classifier.classify(phrase)
                self.assertEqual(
                    res.intent,
                    expected_intent,
                    f"Phrase '{phrase}' incorrectly triggered '{res.intent}' instead of '{expected_intent}'",
                )

    def test_router_go_offline_handling(self):
        """Tests that ActionRouter dispatches GO_OFFLINE with a spoken farewell."""
        res = self.router.route("bye jarvis")
        self.assertEqual(res.intent, IntentType.GO_OFFLINE)
        self.assertTrue(res.success)
        self.assertIn("Going offline", res.spoken_response)
        self.assertEqual(res.data.get("action"), "offline")


if __name__ == "__main__":
    unittest.main()
