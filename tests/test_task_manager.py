"""
Unit Tests for Advanced Task Manager & Resource Monitoring Module
-------------------------------------------------------------------
Validates intent classification, controller functions (CPU/memory bottlenecks,
process info, disk storage, RAM telemetry, unresponsive apps, process termination),
and router dispatch with compound multi-command sequences.
"""

import unittest
from unittest.mock import MagicMock, patch

from core.context import ContextManager
from core.router import ActionRouter
from nlp.intent_classifier import IntentClassifier, IntentType
from system.task_manager import TaskManager


class TestTaskManagerIntentClassification(unittest.TestCase):
    """Verifies that user queries map accurately to task manager intents."""

    def setUp(self):
        self.classifier = IntentClassifier()

    def test_top_cpu_queries(self):
        queries = [
            "what is using my cpu",
            "what's consuming my cpu",
            "top cpu processes",
            "cpu usage by process",
            "cpu consumers",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.TASK_MANAGER)
                self.assertEqual(res.parameters.get("action"), "top_cpu")

    def test_top_memory_queries(self):
        queries = [
            "what is using my memory",
            "what's consuming memory",
            "what is taking up ram",
            "what's slowing down my pc",
            "what is slowing down my computer",
            "top memory processes",
            "top ram processes",
            "heavy processes",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.TASK_MANAGER)
                self.assertEqual(res.parameters.get("action"), "top_memory")

    def test_process_info_queries(self):
        cases = [
            ("is chrome running", "chrome"),
            ("is Spotify running", "Spotify"),
            ("check process discord", "discord"),
            ("process status notepad", "notepad"),
            ("how much ram is vs code using", "vs code"),
            ("how much memory is chrome using", "chrome"),
        ]
        for q, expected_app in cases:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.TASK_MANAGER)
                self.assertEqual(res.parameters.get("action"), "process_info")
                self.assertEqual(res.parameters.get("app_name"), expected_app)

    def test_disk_space_queries(self):
        queries = [
            ("check disk space", "C"),
            ("how much storage do i have left", "C"),
            ("storage status", "C"),
            ("check storage space on d drive", "d"),
        ]
        for q, expected_drive in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.TASK_MANAGER)
                self.assertEqual(res.parameters.get("action"), "disk_space")
                self.assertEqual(res.parameters.get("drive").upper(), expected_drive.upper())

    def test_memory_breakdown_queries(self):
        queries = [
            "memory usage",
            "ram usage",
            "memory breakdown",
            "how much ram is free",
            "check my ram",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.TASK_MANAGER)
                self.assertEqual(res.parameters.get("action"), "memory_breakdown")

    def test_unresponsive_process_queries(self):
        queries = [
            "check for unresponsive apps",
            "check frozen apps",
            "is any app frozen",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.TASK_MANAGER)
                self.assertEqual(res.parameters.get("action"), "check_frozen")

    def test_end_process_queries(self):
        cases = [
            ("end task discord", "discord"),
            ("kill process notepad", "notepad"),
            ("terminate process spotify", "spotify"),
            ("force close chrome", "chrome"),
        ]
        for q, expected_app in cases:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.TASK_MANAGER)
                self.assertEqual(res.parameters.get("action"), "end_process")
                self.assertEqual(res.parameters.get("app_name"), expected_app)


class TestTaskManagerController(unittest.TestCase):
    """Tests the standalone functionality of TaskManager."""

    def setUp(self):
        self.tm = TaskManager()

    def test_get_top_processes_memory(self):
        success, speech, data = self.tm.get_top_processes(sort_by="memory", count=3)
        self.assertTrue(success)
        self.assertIn("sir", speech)
        self.assertTrue(len(data) > 0)

    def test_get_top_processes_cpu(self):
        success, speech, data = self.tm.get_top_processes(sort_by="cpu", count=3)
        self.assertTrue(success)
        self.assertIn("sir", speech)

    def test_get_process_info_running(self):
        # 'python' is running since unit test is active
        success, speech, data = self.tm.get_process_info("python")
        self.assertTrue(success)
        self.assertTrue(data["running"])
        self.assertIn("Python", speech)
        self.assertIn("utilizing", speech)

    def test_get_process_info_not_running(self):
        success, speech, data = self.tm.get_process_info("non_existent_fake_app_99999")
        self.assertTrue(success)
        self.assertFalse(data["running"])
        self.assertIn("not currently running", speech)

    def test_get_disk_space(self):
        success, speech, data = self.tm.get_disk_space("C")
        self.assertTrue(success)
        self.assertIn("Drive C", speech)
        self.assertIn("free", speech)
        self.assertIn("total_gb", data)

    def test_get_memory_breakdown(self):
        success, speech, data = self.tm.get_memory_breakdown()
        self.assertTrue(success)
        self.assertIn("System memory", speech)
        self.assertIn("available", speech)
        self.assertIn("total_gb", data)

    def test_check_unresponsive_processes(self):
        success, speech, hung = self.tm.check_unresponsive_processes()
        self.assertTrue(success)
        self.assertIn("sir", speech)

    @patch("psutil.process_iter")
    def test_end_process_mocked(self, mock_iter):
        mock_p = MagicMock()
        mock_p.info = {"name": "test_dummy.exe", "pid": 1234}
        mock_iter.return_value = [mock_p]

        success, speech = self.tm.end_process("test_dummy")
        self.assertTrue(success)
        mock_p.terminate.assert_called_once()
        self.assertIn("Terminated 1 process", speech)


class TestActionRouterTaskManager(unittest.TestCase):
    """Tests ActionRouter routing for task manager actions."""

    def setUp(self):
        self.context = ContextManager()
        self.router = ActionRouter(context_manager=self.context)

    def test_route_top_memory(self):
        res = self.router.route("what is using my memory")
        self.assertEqual(res.intent, IntentType.TASK_MANAGER)
        self.assertTrue(res.success)
        self.assertIn("sir", res.spoken_response)

    def test_route_disk_space(self):
        res = self.router.route("check disk space")
        self.assertEqual(res.intent, IntentType.TASK_MANAGER)
        self.assertTrue(res.success)
        self.assertIn("Drive C", res.spoken_response)

    def test_route_process_status(self):
        res = self.router.route("is python running")
        self.assertEqual(res.intent, IntentType.TASK_MANAGER)
        self.assertTrue(res.success)
        self.assertIn("Python", res.spoken_response)

    def test_compound_task_manager_command(self):
        intents = self.router.classifier.classify_multi("check disk space and what time is it")
        self.assertEqual(len(intents), 2)
        self.assertEqual(intents[0].intent, IntentType.TASK_MANAGER)
        self.assertEqual(intents[1].intent, IntentType.TIME_DATE)

        res = self.router.route("check disk space and what time is it")
        self.assertTrue(res.success)
        self.assertIn("Drive C", res.spoken_response)
        self.assertIn("currently", res.spoken_response)


if __name__ == "__main__":
    unittest.main()

