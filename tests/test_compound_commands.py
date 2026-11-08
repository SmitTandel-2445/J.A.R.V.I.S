"""
Tests for Compound / Multi-Command Execution in J.A.R.V.I.S.
------------------------------------------------------------
Verifies:
1. IntentClassifier splits compound sentences into discrete sub-commands.
2. IntentClassifier preserves 'and' inside search queries, song titles, and folder names.
3. ActionRouter executes multiple commands sequentially one by one.
4. ActionRouter synthesizes cohesive combined spoken responses.
"""

import unittest
from nlp.intent_classifier import IntentClassifier, IntentType
from core.router import ActionRouter


class TestCompoundCommands(unittest.TestCase):
    def setUp(self):
        self.classifier = IntentClassifier()
        self.router = ActionRouter()

    def test_compound_command_splitting(self):
        """Tests that complex multi-command queries are correctly split into sub-commands."""
        query = "jarvis open the youtube and then open the spotify and play song unstobable in spotify"
        sub_commands = self.classifier.split_compound_commands(query)
        self.assertEqual(len(sub_commands), 3)
        self.assertEqual(sub_commands[0], "open the youtube")
        self.assertEqual(sub_commands[1], "open the spotify")
        self.assertEqual(sub_commands[2], "play song unstobable in spotify")

    def test_classify_multi(self):
        """Tests that classify_multi returns appropriate IntentResult objects in sequence."""
        query = "open notepad and maximize window"
        intents = self.classifier.classify_multi(query)
        self.assertEqual(len(intents), 2)
        self.assertEqual(intents[0].intent, IntentType.OPEN_APP)
        self.assertEqual(intents[0].parameters.get("app_name"), "notepad")
        self.assertEqual(intents[1].intent, IntentType.WINDOW_CONTROL)
        self.assertEqual(intents[1].parameters.get("action"), "maximize")

    def test_three_step_compound_classification(self):
        """Tests the user's exact example: open youtube, open spotify, play song on spotify."""
        query = "open the youtube and then open the spotify and play song unstobable in spotify"
        intents = self.classifier.classify_multi(query)
        self.assertEqual(len(intents), 3)
        self.assertEqual(intents[0].intent, IntentType.OPEN_APP)
        self.assertEqual(intents[1].intent, IntentType.OPEN_APP)
        self.assertEqual(intents[2].intent, IntentType.SPOTIFY_PLAY)
        self.assertEqual(intents[2].parameters.get("query"), "unstobable")

    def test_preservation_of_and_in_parameters(self):
        """Verifies that queries with 'and' inside names/titles are NOT split."""
        single_cases = [
            "play beauty and the beast",
            "search tom and jerry",
            "create folder movies and pictures",
            "play guns and roses on spotify",
        ]
        for phrase in single_cases:
            with self.subTest(phrase=phrase):
                subs = self.classifier.split_compound_commands(phrase)
                self.assertEqual(
                    len(subs),
                    1,
                    f"Phrase '{phrase}' should not be split, but got: {subs}",
                )

    def test_spoken_response_combiner(self):
        """Tests that individual action responses combine into a natural sentence."""
        responses = [
            "Opening YouTube, sir.",
            "Opening Spotify, sir.",
            "Playing unstoppable on Spotify, sir.",
        ]
        combined = ActionRouter._combine_spoken_responses(responses)
        self.assertEqual(
            combined,
            "Opening YouTube, opening spotify, and playing unstoppable on spotify, sir.",
        )

        two_responses = ["Opening Notepad, sir.", "Maximizing window, sir."]
        combined_two = ActionRouter._combine_spoken_responses(two_responses)
        self.assertEqual(
            combined_two,
            "Opening Notepad, and maximizing window, sir.",
        )

    def test_sequential_execution_and_on_step_callback(self):
        """Tests router sequential execution and on_step notification."""
        query = "set volume to 80 and what time is it"
        steps_recorded = []

        def on_step(res, step_idx, total):
            steps_recorded.append((step_idx, total, res.intent))

        result = self.router.route(query, on_step=on_step)
        self.assertTrue(result.success)
        self.assertTrue(result.data.get("compound"))
        self.assertEqual(result.data.get("count"), 2)
        self.assertEqual(len(steps_recorded), 2)
        self.assertEqual(steps_recorded[0], (1, 2, IntentType.SYSTEM_VOLUME))
        self.assertEqual(steps_recorded[1], (2, 2, IntentType.TIME_DATE))


if __name__ == "__main__":
    unittest.main()

