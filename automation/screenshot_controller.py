"""
Screenshot Controller Module for J.A.R.V.I.S.
----------------------------------------------
Captures full-screen screenshots, saves them to the user's Pictures/Screenshots
folder with formatted timestamps, and provides optional file path returns.
"""

from datetime import datetime
import os
from pathlib import Path
from typing import Optional, Tuple
import pyautogui
from utils.logger import logger

pyautogui.FAILSAFE = True


class ScreenshotController:
    """Manages taking and storing desktop screenshots."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the ScreenshotController.

        :param output_dir: Destination directory (defaults to ~/Pictures/Screenshots)
        """
        if output_dir:
            self.output_dir = output_dir
        else:
            pictures_path = Path(os.path.expanduser("~")) / "Pictures" / "Screenshots"
            self.output_dir = pictures_path

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(self) -> Tuple[bool, str, Optional[str]]:
        """
        Captures the primary monitor and saves as a PNG.

        :return: (success: bool, spoken_response: str, saved_path: Optional[str])
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"JARVIS_Screenshot_{timestamp}.png"
            file_path = self.output_dir / filename

            image = pyautogui.screenshot()
            image.save(file_path)

            logger.info(f"Captured screenshot: {file_path}")
            return True, "Screenshot captured and saved to your Pictures folder, sir.", str(file_path)
        except Exception as e:
            logger.warning(f"Screenshot capture unavailable (desktop may be locked or non-interactive): {e}")
            return False, "Unable to capture screen. Please ensure your desktop is active and unlocked, sir.", None


# Global default instance
screenshot_controller = ScreenshotController()
