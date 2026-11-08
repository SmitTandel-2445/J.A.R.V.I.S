"""
Screen Brightness Controller Module for J.A.R.V.I.S.
-----------------------------------------------------
Provides programmatic adjustment of primary display brightness
using screen_brightness_control (WMI / VCP / DDC/CI on Windows).
"""

from typing import Optional, Tuple
import screen_brightness_control as sbc
from utils.logger import logger


class BrightnessController:
    """Manages display brightness percentage and incremental adjustments."""

    @staticmethod
    def get_brightness() -> int:
        """
        Returns the primary display's current brightness as an integer (0 to 100).
        """
        try:
            val = sbc.get_brightness()
            if isinstance(val, list) and val:
                return int(val[0])
            elif isinstance(val, (int, float)):
                return int(val)
        except Exception as e:
            logger.error(f"Failed to read display brightness: {e}")
        return 75

    @classmethod
    def set_brightness(cls, level: int) -> Tuple[bool, int, str]:
        """
        Sets screen brightness to an absolute percentage between 0 and 100.

        :param level: Target percentage (0 - 100)
        :return: (success: bool, actual_level: int, spoken_response: str)
        """
        clamped = max(0, min(100, int(level)))
        try:
            sbc.set_brightness(clamped)
            logger.info(f"Screen brightness set to {clamped}%.")
            return True, clamped, f"Setting brightness to {clamped} percent, sir."
        except Exception as e:
            logger.error(f"Failed to set brightness to {level}%: {e}")
            return False, cls.get_brightness(), "Unable to adjust display brightness on this monitor, sir."

    @classmethod
    def change_brightness(cls, delta: int) -> Tuple[bool, int, str]:
        """
        Adjusts screen brightness relatively by delta (+10, -10, etc.).

        :param delta: Incremental step
        :return: (success: bool, actual_level: int, spoken_response: str)
        """
        current = cls.get_brightness()
        target = current + delta
        success, final_val, _ = cls.set_brightness(target)
        direction = "increased" if delta > 0 else "decreased"
        if success:
            speech = f"Brightness {direction} to {final_val} percent, sir."
        else:
            speech = f"Could not adjust brightness, sir."
        return success, final_val, speech


# Global default instance
brightness_controller = BrightnessController()

