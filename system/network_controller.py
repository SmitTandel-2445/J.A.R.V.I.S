"""
Network & Wi-Fi Diagnostics Controller Module for J.A.R.V.I.S.
---------------------------------------------------------------
Provides real-time OS-level network telemetry and Wi-Fi diagnostics on Windows:
- Wi-Fi connection info (SSID, signal strength, transmission rate, radio type)
- Internet connectivity and latency / ping measurement
- Local and public IP address lookup
- Complete network diagnostic health checks
- DNS cache flushing and Wi-Fi disconnection
"""

import os
import re
import socket
import subprocess
import urllib.request
from typing import Dict, Optional, Tuple

from utils.logger import logger


class NetworkController:
    """Manages Windows network diagnostics, Wi-Fi queries, and IP telemetry."""

    @staticmethod
    def check_wifi() -> Tuple[bool, str, Dict[str, Optional[str]]]:
        """
        Queries Windows WLAN interface for active Wi-Fi connection details.
        :return: (success: bool, spoken_response: str, details: dict)
        """
        try:
            cmd = ["netsh", "wlan", "show", "interfaces"]
            output = subprocess.check_output(cmd, text=True, errors="ignore")

            ssid_match = re.search(r"^\s*SSID\s*:\s*(.+)$", output, re.MULTILINE)
            state_match = re.search(r"^\s*State\s*:\s*(.+)$", output, re.MULTILINE)
            signal_match = re.search(r"^\s*Signal\s*:\s*(.+)$", output, re.MULTILINE)
            rate_match = re.search(r"^\s*Receive rate \(Mbps\)\s*:\s*(.+)$", output, re.MULTILINE)
            radio_match = re.search(r"^\s*Radio type\s*:\s*(.+)$", output, re.MULTILINE)

            data = {
                "ssid": ssid_match.group(1).strip() if ssid_match else None,
                "state": state_match.group(1).strip() if state_match else "unknown",
                "signal": signal_match.group(1).strip() if signal_match else None,
                "rate": rate_match.group(1).strip() if rate_match else None,
                "radio": radio_match.group(1).strip() if radio_match else None,
            }

            if "There is no wireless interface" in output or "no interface" in output.lower():
                return False, "No wireless interface was found on this system, sir.", data

            if data["state"].lower() != "connected":
                return True, "Wi-Fi is currently disconnected, sir.", data

            ssid = data["ssid"] or "Unknown Network"
            signal = data["signal"] or "nominal"
            rate = data["rate"]

            if rate:
                speech = f"You are connected to {ssid} with {signal} signal strength at {rate} megabits per second, sir."
            else:
                speech = f"You are connected to {ssid} with {signal} signal strength, sir."

            logger.info(f"Wi-Fi status: SSID='{ssid}', Signal={signal}, Rate={rate} Mbps")
            return True, speech, data

        except Exception as e:
            logger.error(f"Error querying Wi-Fi status: {e}")
            return False, "I was unable to retrieve Wi-Fi status, sir.", {}

    @staticmethod
    def test_internet(host: str = "1.1.1.1") -> Tuple[bool, str, Dict[str, Optional[str]]]:
        """
        Tests internet connectivity and measures round-trip latency via ping.
        :param host: Reliable DNS address to ping (default: Cloudflare DNS 1.1.1.1)
        :return: (success: bool, spoken_response: str, details: dict)
        """
        try:
            # Ping with 1 packet and 2000ms timeout
            res = subprocess.run(
                ["ping", "-n", "1", "-w", "2000", host],
                capture_output=True,
                text=True,
                errors="ignore",
            )
            output = res.stdout

            latency_match = re.search(r"time[=<](\d+)\s*ms", output, re.IGNORECASE)
            if res.returncode == 0 and latency_match:
                latency = latency_match.group(1)
                speech = f"Internet connection is online with an average ping of {latency} milliseconds, sir."
                logger.info(f"Internet ping: {latency} ms (Host: {host})")
                return True, speech, {"status": "online", "latency_ms": latency, "host": host}
            elif res.returncode == 0:
                speech = "Internet connection is online and responding, sir."
                return True, speech, {"status": "online", "latency_ms": None, "host": host}
            else:
                speech = "The internet appears to be offline or unreachable, sir."
                logger.warning("Internet ping failed: host unreachable.")
                return False, speech, {"status": "offline", "latency_ms": None, "host": host}

        except Exception as e:
            logger.error(f"Error testing internet connectivity: {e}")
            return False, "I could not complete the internet connectivity test, sir.", {}

    @staticmethod
    def get_ip_address(scope: str = "all") -> Tuple[bool, str, Dict[str, str]]:
        """
        Retrieves local and/or public IP addresses.
        :param scope: 'local', 'public', or 'all'
        :return: (success: bool, spoken_response: str, details: dict)
        """
        local_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("1.1.1.1", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            try:
                local_ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                local_ip = "Unavailable"

        public_ip = "Unavailable"
        if scope in ("public", "all"):
            for endpoint in ["https://api.ipify.org", "https://icanhazip.com"]:
                try:
                    req = urllib.request.Request(endpoint, headers={"User-Agent": "JARVIS-Assistant"})
                    with urllib.request.urlopen(req, timeout=2.0) as resp:
                        public_ip = resp.read().decode().strip()
                        if public_ip:
                            break
                except Exception:
                    continue

        data = {"local_ip": local_ip, "public_ip": public_ip}

        if scope == "local":
            speech = f"Your local IP address is {local_ip}, sir."
        elif scope == "public":
            if public_ip != "Unavailable":
                speech = f"Your public IP address is {public_ip}, sir."
            else:
                speech = "Your public IP address is currently unreachable, sir."
        else:
            if public_ip != "Unavailable":
                speech = f"Your local IP is {local_ip}, and your public IP is {public_ip}, sir."
            else:
                speech = f"Your local IP address is {local_ip}, sir. Public IP is currently unavailable."

        logger.info(f"IP resolution: Local={local_ip}, Public={public_ip}")
        return True, speech, data

    @staticmethod
    def get_diagnostics() -> Tuple[bool, str, Dict[str, any]]:
        """
        Performs a full combined network diagnostic check (Wi-Fi, Latency, Local IP).
        :return: (success: bool, spoken_response: str, details: dict)
        """
        try:
            # 1. Wi-Fi
            wifi_ok, _, wifi_data = NetworkController.check_wifi()
            # 2. Internet
            net_ok, _, net_data = NetworkController.test_internet()
            # 3. IP
            _, _, ip_data = NetworkController.get_ip_address(scope="local")

            ssid = wifi_data.get("ssid") or "an ethernet connection"
            signal = wifi_data.get("signal")
            latency = net_data.get("latency_ms")
            local_ip = ip_data.get("local_ip", "unknown")

            parts = ["Network diagnostics complete, sir."]
            if wifi_ok and wifi_data.get("state", "").lower() == "connected":
                if signal:
                    parts.append(f"Connected to {ssid} with {signal} signal.")
                else:
                    parts.append(f"Connected to {ssid}.")
            elif not net_ok:
                parts.append("Network adapter is active, but internet is currently unreachable.")

            if latency:
                parts.append(f"Internet latency is {latency} milliseconds.")
            elif net_ok:
                parts.append("Internet is online.")

            parts.append(f"Local IP is {local_ip}.")

            speech = " ".join(parts)
            logger.info("Full network diagnostics performed successfully.")
            return True, speech, {
                "wifi": wifi_data,
                "internet": net_data,
                "ip": ip_data,
            }

        except Exception as e:
            logger.error(f"Error running network diagnostics: {e}")
            return False, "Failed to complete full network diagnostics, sir.", {}

    @staticmethod
    def flush_dns() -> Tuple[bool, str]:
        """
        Flushes the Windows DNS Resolver Cache via 'ipconfig /flushdns'.
        :return: (success: bool, spoken_response: str)
        """
        try:
            res = subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                text=True,
                errors="ignore",
            )
            output = res.stdout + res.stderr
            if "Successfully flushed" in output:
                logger.info("DNS Resolver Cache successfully flushed.")
                return True, "Successfully flushed the DNS Resolver Cache, sir."
            elif "requires elevation" in output.lower():
                logger.warning("DNS flush failed: elevation required.")
                return False, "Flushing the DNS cache requires administrator privileges, sir."
            else:
                logger.info(f"DNS flush output: {output.strip()}")
                return True, "DNS cache flush command executed, sir."
        except Exception as e:
            logger.error(f"Error flushing DNS cache: {e}")
            return False, "I was unable to flush the DNS cache, sir."

    @staticmethod
    def disconnect_wifi() -> Tuple[bool, str]:
        """
        Disconnects the active Wi-Fi interface.
        :return: (success: bool, spoken_response: str)
        """
        try:
            res = subprocess.run(
                ["netsh", "wlan", "disconnect"],
                capture_output=True,
                text=True,
                errors="ignore",
            )
            if res.returncode == 0:
                logger.info("Disconnected from Wi-Fi.")
                return True, "Disconnected from Wi-Fi, sir."
            else:
                return False, "Failed to disconnect from Wi-Fi, sir."
        except Exception as e:
            logger.error(f"Error disconnecting Wi-Fi: {e}")
            return False, "I encountered an error disconnecting Wi-Fi, sir."

    @staticmethod
    def connect_wifi(ssid: Optional[str] = None) -> Tuple[bool, str]:
        """
        Reconnects to Wi-Fi. If ssid is specified, connects to that profile;
        otherwise connects to the available wireless network.
        :return: (success: bool, spoken_response: str)
        """
        try:
            cmd = ["netsh", "wlan", "connect"]
            if ssid:
                cmd.extend(["name=" + ssid.strip()])
            res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
            output = res.stdout + res.stderr
            if res.returncode == 0 or "completed" in output.lower() or "successfully" in output.lower():
                logger.info("Wi-Fi connection command completed successfully.")
                return True, "Reconnecting to Wi-Fi now, sir."
            else:
                logger.info(f"Wi-Fi connect output: {output.strip()}")
                return True, "Connection command sent to Wi-Fi adapter, sir."
        except Exception as e:
            logger.error(f"Error connecting Wi-Fi: {e}")
            return False, "I was unable to connect to Wi-Fi, sir."


# Global default instance
network_controller = NetworkController()

