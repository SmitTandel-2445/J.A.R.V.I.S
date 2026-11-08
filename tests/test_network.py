"""
Unit Tests for Network, Wi-Fi & Internet Diagnostics Module
------------------------------------------------------------
Validates intent classification, controller functions (Wi-Fi, Internet latency, IP,
diagnostics, DNS flush, Wi-Fi disconnect), and router dispatch with compound support.
"""

import unittest
from unittest.mock import MagicMock, patch

from core.context import ContextManager
from core.router import ActionRouter
from nlp.intent_classifier import IntentClassifier, IntentType
from system.network_controller import NetworkController


class TestNetworkIntentClassification(unittest.TestCase):
    """Verifies that voice queries map accurately to network diagnostics intents."""

    def setUp(self):
        self.classifier = IntentClassifier()

    def test_wifi_queries(self):
        queries = [
            "check wifi",
            "check my wifi",
            "wifi status",
            "wifi signal",
            "what wifi am i connected to",
            "what is my wifi",
            "wireless status",
            "get wifi signal",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.NETWORK)
                self.assertEqual(res.parameters.get("action"), "wifi")

    def test_internet_queries(self):
        queries = [
            "check internet",
            "is internet working",
            "test internet connection",
            "test connection",
            "ping test",
            "check network latency",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.NETWORK)
                self.assertEqual(res.parameters.get("action"), "internet")

    def test_ip_address_queries(self):
        cases = [
            ("what is my ip", "all"),
            ("what is my ip address", "all"),
            ("check my ip", "all"),
            ("what is my local ip", "local"),
            ("what is my private ip", "local"),
            ("what is my public ip", "public"),
            ("what is my external ip", "public"),
        ]
        for q, expected_scope in cases:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.NETWORK)
                self.assertEqual(res.parameters.get("action"), "ip")
                self.assertEqual(res.parameters.get("scope"), expected_scope)

    def test_diagnostics_queries(self):
        queries = [
            "network diagnostics",
            "run network diagnostics",
            "diagnose network",
            "network status",
            "network health",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.NETWORK)
                self.assertEqual(res.parameters.get("action"), "diagnostics")

    def test_flush_dns_queries(self):
        queries = [
            "flush dns",
            "flush dns cache",
            "clear dns cache",
            "empty dns",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.NETWORK)
                self.assertEqual(res.parameters.get("action"), "flush_dns")

    def test_disconnect_wifi_queries(self):
        queries = [
            "disconnect wifi",
            "disconnect from wifi",
            "turn off wifi",
            "disconnect wireless",
        ]
        for q in queries:
            with self.subTest(query=q):
                res = self.classifier.classify(q)
                self.assertEqual(res.intent, IntentType.NETWORK)
                self.assertEqual(res.parameters.get("action"), "disconnect_wifi")


class TestNetworkController(unittest.TestCase):
    """Tests the standalone functionality of NetworkController."""

    def setUp(self):
        self.controller = NetworkController()

    @patch("subprocess.check_output")
    def test_check_wifi_connected(self, mock_output):
        mock_output.return_value = (
            "There is 1 interface on the system:\n"
            "    State                  : connected\n"
            "    SSID                   : Stark_Tower_Guest\n"
            "    Signal                 : 94%\n"
            "    Receive rate (Mbps)    : 300\n"
            "    Radio type             : 802.11ax\n"
        )
        success, speech, data = self.controller.check_wifi()
        self.assertTrue(success)
        self.assertEqual(data["ssid"], "Stark_Tower_Guest")
        self.assertEqual(data["signal"], "94%")
        self.assertEqual(data["rate"], "300")
        self.assertIn("Stark_Tower_Guest", speech)
        self.assertIn("94%", speech)

    @patch("subprocess.check_output")
    def test_check_wifi_disconnected(self, mock_output):
        mock_output.return_value = (
            "There is 1 interface on the system:\n"
            "    State                  : disconnected\n"
        )
        success, speech, data = self.controller.check_wifi()
        self.assertTrue(success)
        self.assertIn("disconnected", speech.lower())

    @patch("subprocess.run")
    def test_test_internet_online(self, mock_run):
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Reply from 1.1.1.1: bytes=32 time=24ms TTL=56\n"
        mock_run.return_value = mock_res

        success, speech, data = self.controller.test_internet()
        self.assertTrue(success)
        self.assertEqual(data["latency_ms"], "24")
        self.assertIn("24 milliseconds", speech)

    @patch("subprocess.run")
    def test_test_internet_offline(self, mock_run):
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = "Request timed out.\n"
        mock_run.return_value = mock_res

        success, speech, data = self.controller.test_internet()
        self.assertFalse(success)
        self.assertIn("offline", speech.lower())

    def test_get_ip_address_local(self):
        success, speech, data = self.controller.get_ip_address(scope="local")
        self.assertTrue(success)
        self.assertIn("local_ip", data)
        self.assertIn("Your local IP", speech)

    @patch("subprocess.run")
    def test_flush_dns_success(self, mock_run):
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Successfully flushed the DNS Resolver Cache."
        mock_res.stderr = ""
        mock_run.return_value = mock_res

        success, speech = self.controller.flush_dns()
        self.assertTrue(success)
        self.assertIn("Successfully flushed", speech)

    @patch("subprocess.run")
    def test_flush_dns_requires_elevation(self, mock_run):
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = ""
        mock_res.stderr = "The requested operation requires elevation."
        mock_run.return_value = mock_res

        success, speech = self.controller.flush_dns()
        self.assertFalse(success)
        self.assertIn("administrator privileges", speech)

    @patch("subprocess.run")
    def test_disconnect_wifi(self, mock_run):
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_run.return_value = mock_res

        success, speech = self.controller.disconnect_wifi()
        self.assertTrue(success)
        self.assertIn("Disconnected from Wi-Fi", speech)


class TestActionRouterNetwork(unittest.TestCase):
    """Tests ActionRouter routing for network actions."""

    def setUp(self):
        self.context = ContextManager()
        self.router = ActionRouter(context_manager=self.context)

    def test_route_wifi_status(self):
        res = self.router.route("check wifi")
        self.assertEqual(res.intent, IntentType.NETWORK)
        self.assertTrue(res.success)
        self.assertIn("sir", res.spoken_response)

    def test_route_internet_test(self):
        res = self.router.route("check internet")
        self.assertEqual(res.intent, IntentType.NETWORK)
        self.assertIn("sir", res.spoken_response)

    def test_route_local_ip(self):
        res = self.router.route("what is my local ip")
        self.assertEqual(res.intent, IntentType.NETWORK)
        self.assertTrue(res.success)
        self.assertIn("local IP", res.spoken_response)

    def test_compound_command_with_network(self):
        intents = self.router.classifier.classify_multi("check wifi and what time is it")
        self.assertEqual(len(intents), 2)
        self.assertEqual(intents[0].intent, IntentType.NETWORK)
        self.assertEqual(intents[1].intent, IntentType.TIME_DATE)

        res = self.router.route("check wifi and what time is it")
        self.assertTrue(res.success)
        self.assertIn("sir", res.spoken_response)


if __name__ == "__main__":
    unittest.main()

