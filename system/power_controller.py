"""
System Power & Security Controller Module for J.A.R.V.I.S.
-----------------------------------------------------------
Provides OS-level power management, workstation locking, and battery diagnostics
using Windows API functions and psutil.
"""

import ctypes
import os
import subprocess
from typing import Optional, Tuple

import psutil

from utils.logger import logger


class PowerController:
    """Manages system lock, sleep, and battery telemetry on Windows."""

    @staticmethod
    def lock_workstation() -> Tuple[bool, str]:
        """
        Immediately locks the Windows workstation screen using the user32 API.

        :return: (success: bool, spoken_response: str)
        """
        try:
            logger.info("Locking Windows workstation via user32.LockWorkStation...")
            success = bool(ctypes.windll.user32.LockWorkStation())
            if success:
                return True, "Locking your workstation now, sir."
            else:
                return False, "Failed to lock the workstation, sir."
        except Exception as e:
            logger.error(f"Error locking workstation: {e}")
            return False, "I was unable to lock your screen, sir."

    @staticmethod
    def sleep() -> Tuple[bool, str]:
        """
        Puts the computer into sleep mode.

        :return: (success: bool, spoken_response: str)
        """
        try:
            logger.info("Putting computer to sleep via powrprof.dll...")
            subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return True, "Entering sleep mode, sir. Goodnight."
        except Exception as e:
            logger.error(f"Error initiating sleep state: {e}")
            return False, "Unable to initiate sleep mode, sir."

    @staticmethod
    def get_battery_report() -> str:
        """
        Generates a detailed natural-language battery report.
        """
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return "The system is running on continuous AC power, sir. No battery sensor is present."

            percent = int(battery.percent)
            plugged = battery.power_plugged

            if plugged:
                state = "plugged in and charging" if percent < 100 else "plugged in and fully charged"
            else:
                state = "running on battery power"

            secs_left = battery.secsleft
            if not plugged and secs_left > 0 and secs_left != psutil.POWER_TIME_UNLIMITED:
                hours = secs_left // 3600
                mins = (secs_left % 3600) // 60
                time_str = f" approximately {hours} hours and {mins} minutes of runtime remaining"
            else:
                time_str = ""

            report = f"The battery is currently at {percent} percent, {state}.{time_str}"
            return report
        except Exception as e:
            logger.error(f"Error reading battery status: {e}")
            return "Unable to retrieve battery diagnostics at this time, sir."


# Global default instance
power_controller = PowerController()

