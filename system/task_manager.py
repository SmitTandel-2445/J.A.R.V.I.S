"""
Advanced Task Manager & Resource Monitoring Module for J.A.R.V.I.S.
---------------------------------------------------------------------
Provides detailed system telemetry, per-process CPU & RAM analytics,
storage/disk analytics, unresponsive app detection, and process termination.
"""

import ctypes
import os
import re
import time
from typing import Dict, List, Optional, Tuple

import psutil

from utils.logger import logger

# Friendly name mapping for common processes
FRIENDLY_NAMES = {
    "chrome.exe": "Google Chrome",
    "msedge.exe": "Microsoft Edge",
    "firefox.exe": "Firefox",
    "code.exe": "VS Code",
    "spotify.exe": "Spotify",
    "discord.exe": "Discord",
    "slack.exe": "Slack",
    "notepad.exe": "Notepad",
    "python.exe": "Python",
    "antigravity ide.exe": "Antigravity IDE",
    "explorer.exe": "Windows Explorer",
    "taskmgr.exe": "Task Manager",
    "teams.exe": "Microsoft Teams",
}

# Processes to exclude from top consumer calculations
EXCLUDED_PROCESSES = {
    "system idle process",
    "idle",
    "system",
    "registry",
    "memcompression",
}


def _format_bytes(bytes_val: int) -> str:
    """Formats raw byte count into human-friendly string (MB or GB)."""
    mb = bytes_val / (1024 ** 2)
    if mb >= 1024:
        gb = mb / 1024
        return f"{gb:.1f} gigabytes"
    return f"{int(mb)} megabytes"


class TaskManager:
    """Manages process inspection, resource bottlenecks, and disk analytics."""

    @staticmethod
    def get_top_processes(sort_by: str = "memory", count: int = 3) -> Tuple[bool, str, List[Dict[str, any]]]:
        """
        Aggregates and returns the top resource-consuming processes.
        :param sort_by: 'memory' or 'cpu'
        :param count: Number of top processes to return (default: 3)
        :return: (success: bool, spoken_response: str, process_list: list)
        """
        try:
            aggregated: Dict[str, Dict[str, any]] = {}

            if sort_by == "cpu":
                # Sample CPU over all processes
                procs = list(psutil.process_iter(["pid", "name"]))
                for p in procs:
                    try:
                        p.cpu_percent(interval=None)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                import time
                time.sleep(0.12)

                for p in procs:
                    try:
                        name = p.info["name"]
                        if not name or name.lower() in EXCLUDED_PROCESSES:
                            continue
                        cpu = p.cpu_percent(interval=None)
                        if name not in aggregated:
                            aggregated[name] = {"name": name, "cpu": 0.0, "memory": 0, "count": 0}
                        aggregated[name]["cpu"] += cpu
                        aggregated[name]["count"] += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                sorted_items = sorted(aggregated.values(), key=lambda x: x["cpu"], reverse=True)[:count]
                if not sorted_items or sorted_items[0]["cpu"] == 0:
                    return True, "CPU usage across active processes is currently minimal, sir.", []

                parts = []
                for item in sorted_items:
                    friendly = FRIENDLY_NAMES.get(item["name"].lower(), item["name"].replace(".exe", ""))
                    parts.append(f"{friendly} at {int(item['cpu'])} percent")

                speech = f"The top CPU consumers are {', '.join(parts[:-1]) + ', and ' + parts[-1] if len(parts) > 1 else parts[0]}, sir."
                logger.info(f"Top CPU processes: {[i['name'] for i in sorted_items]}")
                return True, speech, sorted_items

            else:
                # Default: Memory consumption
                for p in psutil.process_iter(["pid", "name", "memory_info"]):
                    try:
                        name = p.info["name"]
                        if not name or name.lower() in EXCLUDED_PROCESSES:
                            continue
                        mem = p.info["memory_info"].rss
                        if name not in aggregated:
                            aggregated[name] = {"name": name, "memory": 0, "count": 0}
                        aggregated[name]["memory"] += mem
                        aggregated[name]["count"] += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                sorted_items = sorted(aggregated.values(), key=lambda x: x["memory"], reverse=True)[:count]
                if not sorted_items:
                    return True, "No high-memory processes detected, sir.", []

                parts = []
                for item in sorted_items:
                    friendly = FRIENDLY_NAMES.get(item["name"].lower(), item["name"].replace(".exe", ""))
                    mem_str = _format_bytes(item["memory"])
                    parts.append(f"{friendly} utilizing {mem_str}")

                lead = ", ".join(parts[:-1]) + ", and " + parts[-1] if len(parts) > 1 else parts[0]
                speech = f"The top processes using memory are {lead}, sir."
                logger.info(f"Top memory processes: {[i['name'] for i in sorted_items]}")
                return True, speech, sorted_items

        except Exception as e:
            logger.error(f"Error querying top processes: {e}")
            return False, "I was unable to retrieve process resource usage, sir.", []

    @staticmethod
    def get_process_info(target_name: str) -> Tuple[bool, str, Dict[str, any]]:
        """
        Inspects whether a specific app/process is running and its resource usage.
        :param target_name: App or process name to inspect (e.g. 'chrome', 'spotify')
        :return: (success: bool, spoken_response: str, details: dict)
        """
        try:
            clean_target = target_name.strip().lower()
            matching_procs = []
            total_mem = 0
            total_cpu = 0.0

            for p in psutil.process_iter(["pid", "name", "memory_info"]):
                try:
                    pname = p.info["name"].lower()
                    if clean_target in pname or pname.startswith(clean_target):
                        matching_procs.append(p)
                        total_mem += p.info["memory_info"].rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if not matching_procs:
                return True, f"{target_name} is not currently running, sir.", {"running": False, "count": 0}

            # Optional quick CPU sample
            for p in matching_procs:
                try:
                    p.cpu_percent(interval=None)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            import time
            time.sleep(0.08)

            for p in matching_procs:
                try:
                    total_cpu += p.cpu_percent(interval=None)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            first_name = matching_procs[0].info["name"]
            friendly = FRIENDLY_NAMES.get(first_name.lower(), target_name.title())
            mem_str = _format_bytes(total_mem)
            count = len(matching_procs)

            proc_word = "process" if count == 1 else "processes"
            speech = f"{friendly} is currently running across {count} {proc_word}, utilizing {mem_str} of RAM and {int(total_cpu)} percent CPU, sir."

            logger.info(f"Process query '{target_name}': Count={count}, Mem={mem_str}, CPU={total_cpu}%")
            return True, speech, {
                "running": True,
                "name": friendly,
                "count": count,
                "memory_bytes": total_mem,
                "memory_formatted": mem_str,
                "cpu_percent": total_cpu,
            }

        except Exception as e:
            logger.error(f"Error inspecting process '{target_name}': {e}")
            return False, f"Could not inspect process {target_name}, sir.", {}

    @staticmethod
    def get_disk_space(drive: Optional[str] = None) -> Tuple[bool, str, Dict[str, any]]:
        """
        Retrieves disk storage usage and remaining free space.
        :param drive: Target drive letter (e.g. 'C:', 'D:'). Default: system drive.
        :return: (success: bool, spoken_response: str, details: dict)
        """
        try:
            target_drive = drive.upper() if drive else "C:"
            if not target_drive.endswith(":") and not target_drive.endswith(":\\"):
                target_drive = f"{target_drive}:"
            if not target_drive.endswith("\\"):
                target_drive = f"{target_drive}\\"

            usage = psutil.disk_usage(target_drive)
            total_gb = usage.total / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            used_percent = usage.percent

            drive_label = target_drive.replace("\\", "")
            speech = f"Drive {drive_label} has {free_gb:.1f} gigabytes free out of {int(total_gb)} gigabytes, which is {int(used_percent)} percent utilized, sir."
            logger.info(f"Disk check ({drive_label}): Free={free_gb:.1f}GB, Total={total_gb:.1f}GB, Used={used_percent}%")

            return True, speech, {
                "drive": drive_label,
                "free_gb": free_gb,
                "total_gb": total_gb,
                "used_percent": used_percent,
            }

        except Exception as e:
            logger.error(f"Error checking disk space for drive '{drive}': {e}")
            return False, "I was unable to retrieve disk space metrics, sir.", {}

    @staticmethod
    def get_memory_breakdown() -> Tuple[bool, str, Dict[str, any]]:
        """
        Retrieves virtual RAM memory breakdown.
        :return: (success: bool, spoken_response: str, details: dict)
        """
        try:
            vm = psutil.virtual_memory()
            total_gb = vm.total / (1024 ** 3)
            avail_gb = vm.available / (1024 ** 3)
            used_percent = vm.percent

            speech = f"System memory is {int(used_percent)} percent utilized. You have {avail_gb:.1f} gigabytes available out of {total_gb:.1f} gigabytes total, sir."
            logger.info(f"Memory check: {avail_gb:.1f}GB avail / {total_gb:.1f}GB total ({used_percent}%)")

            return True, speech, {
                "total_gb": total_gb,
                "available_gb": avail_gb,
                "used_percent": used_percent,
            }

        except Exception as e:
            logger.error(f"Error checking memory breakdown: {e}")
            return False, "I could not retrieve memory telemetry, sir.", {}

    @staticmethod
    def check_unresponsive_processes() -> Tuple[bool, str, List[str]]:
        """
        Uses Windows User32 API (IsHungAppWindow) to detect frozen top-level application windows.
        :return: (success: bool, spoken_response: str, hung_apps: list)
        """
        hung_titles: List[str] = []
        try:
            user32 = ctypes.windll.user32

            def enum_proc(hwnd, lParam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        if user32.IsHungAppWindow(hwnd):
                            hung_titles.append(buff.value)
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            user32.EnumWindows(WNDENUMPROC(enum_proc), 0)

            if hung_titles:
                speech = f"I detected {len(hung_titles)} unresponsive application: {', '.join(hung_titles)}, sir."
                return True, speech, hung_titles
            else:
                return True, "All running applications are responsive, sir. No frozen windows detected.", []

        except Exception as e:
            logger.error(f"Error checking for unresponsive processes: {e}")
            return False, "I was unable to verify application responsiveness, sir.", []

    @staticmethod
    def get_system_uptime() -> Tuple[bool, str, Dict[str, any]]:
        """
        Calculates system uptime from Windows boot timestamp.
        :return: (success: bool, spoken_response: str, details: dict)
        """
        try:
            boot_time = psutil.boot_time()
            elapsed_seconds = int(time.time() - boot_time)
            days = elapsed_seconds // 86400
            hours = (elapsed_seconds % 86400) // 3600
            minutes = (elapsed_seconds % 3600) // 60

            parts = []
            if days > 0:
                parts.append(f"{days} {'day' if days == 1 else 'days'}")
            if hours > 0:
                parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
            if minutes > 0 or not parts:
                parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")

            uptime_str = ", ".join(parts[:-1]) + ", and " + parts[-1] if len(parts) > 1 else parts[0]
            speech = f"Your PC has been running continuously for {uptime_str}, sir."
            logger.info(f"System uptime: {uptime_str} ({elapsed_seconds}s)")
            return True, speech, {"days": days, "hours": hours, "minutes": minutes, "total_seconds": elapsed_seconds}
        except Exception as e:
            logger.error(f"Error calculating system uptime: {e}")
            return False, "I was unable to retrieve system uptime, sir.", {}

    @staticmethod
    def end_process(target_name: str) -> Tuple[bool, str]:
        """
        Forcefully terminates all processes matching target_name.
        Guarded against terminating protected Windows and J.A.R.V.I.S. processes.
        :param target_name: Name of process or application
        :return: (success: bool, spoken_response: str)
        """
        from core.security.command_validator import CommandValidator

        try:
            clean_target = target_name.strip().lower()
            is_valid, canon_name, err = CommandValidator.validate_process_target(clean_target)
            if not is_valid:
                logger.warning(f"Task manager termination blocked by CommandValidator: {err}")
                return False, err

            terminated_count = 0
            target_exe = f"{clean_target}.exe" if not clean_target.endswith(".exe") else clean_target

            for p in psutil.process_iter(["pid", "name"]):
                try:
                    pname = (p.info.get("name") or "").lower()
                    if pname and (pname == target_exe or pname == clean_target):
                        p.terminate()
                        terminated_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if terminated_count > 0:
                speech = f"Terminated {terminated_count} {'process' if terminated_count == 1 else 'processes'} for {target_name}, sir."
                logger.info(f"Terminated {terminated_count} processes for '{target_name}'")
                return True, speech
            else:
                return False, f"I could not find any active processes for {target_name}, sir."

        except Exception as e:
            logger.error(f"Error ending process '{target_name}': {e}")
            return False, f"Failed to end process {target_name}, sir."


# Global default instance
task_manager = TaskManager()

