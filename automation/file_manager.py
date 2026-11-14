"""
File & Folder Automation Module for J.A.R.V.I.S.
------------------------------------------------
Provides voice-activated file system shortcuts:
- Open standard folders (Downloads, Documents, Desktop, Pictures, Videos, Music)
- Open drives (C Drive, D Drive)
- Create new folders on the Desktop
- Empty the Windows Recycle Bin
"""

import ctypes
import os
from pathlib import Path
from typing import Optional, Tuple
from utils.logger import logger


class FileManager:
    """Manages common OS directory navigation, folder creation, and cleanup."""

    STANDARD_FOLDERS = {
        "downloads": "Downloads",
        "documents": "Documents",
        "desktop": "Desktop",
        "pictures": "Pictures",
        "photos": "Pictures",
        "videos": "Videos",
        "movies": "Videos",
        "music": "Music",
    }

    @classmethod
    def open_folder(cls, target: str) -> Tuple[bool, str]:
        """
        Opens a user folder or system drive in Windows File Explorer.

        :param target: Spoken folder name (e.g., 'downloads', 'c drive')
        :return: (success: bool, spoken_response: str)
        """
        norm = target.lower().strip()

        # 1. Drive check
        if norm in ("c drive", "c:"):
            drive_path = "C:\\"
            if os.path.exists(drive_path):
                os.startfile(drive_path)
                return True, "Opening C drive, sir."

        if norm in ("d drive", "d:"):
            drive_path = "D:\\"
            if os.path.exists(drive_path):
                os.startfile(drive_path)
                return True, "Opening D drive, sir."

        # 2. Standard User Folder
        folder_sub = cls.STANDARD_FOLDERS.get(norm)
        if folder_sub:
            folder_path = Path(os.path.expanduser("~")) / folder_sub
            if folder_path.exists():
                os.startfile(str(folder_path))
                logger.info(f"Opened user directory: {folder_path}")
                return True, f"Opening {target}, sir."

        return False, f"I could not locate the {target} folder, sir."

    @classmethod
    def create_folder(cls, folder_name: str) -> Tuple[bool, str]:
        """
        Creates a new directory on the user's Desktop.
        Guarded against path traversal attacks.

        :param folder_name: Name of the folder to create
        :return: (success: bool, spoken_response: str)
        """
        from core.security.file_access_guard import file_access_guard

        clean_name = folder_name.strip()
        if not clean_name:
            return False, "Please specify a name for the new folder, sir."

        desktop_dir = Path(os.path.expanduser("~")) / "Desktop"
        is_valid, canon_path, err = file_access_guard.validate_folder_creation(desktop_dir, clean_name)
        if not is_valid or not canon_path:
            logger.warning(f"Folder creation blocked by FileAccessGuard: {err}")
            return False, f"Folder creation blocked: {err}"

        try:
            canon_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created new folder on Desktop: {canon_path}")
            return True, f"Created folder {clean_name} on your Desktop, sir."
        except Exception as e:
            logger.error(f"Failed to create folder '{folder_name}': {e}")
            return False, f"Could not create folder {folder_name}, sir."

    @staticmethod
    def empty_recycle_bin() -> Tuple[bool, str]:
        """
        Empties the Windows Recycle Bin using the Windows Shell API (SHEmptyRecycleBinW).
        Flag 7 = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        """
        try:
            # Call Windows Shell API
            flags = 7
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
            logger.info(f"SHEmptyRecycleBinW returned code: {result}")
            return True, "Recycle bin emptied successfully, sir."
        except Exception as e:
            logger.error(f"Failed to empty recycle bin: {e}")
            return False, "Could not empty the recycle bin, sir."

    @classmethod
    def open_latest_download(cls) -> Tuple[bool, str, Optional[str]]:
        """
        Locates the most recently downloaded file in Downloads and opens it.
        Guarded against launching dangerous executable or script files.
        :return: (success: bool, spoken_response: str, file_path: Optional[str])
        """
        from core.security.file_access_guard import file_access_guard

        try:
            downloads_dir = Path(os.path.expanduser("~")) / "Downloads"
            if not downloads_dir.exists():
                return False, "Your Downloads directory could not be found, sir.", None

            files = [
                f for f in downloads_dir.iterdir()
                if f.is_file() and not f.name.endswith((".crdownload", ".tmp", ".part"))
            ]
            if not files:
                return True, "Your Downloads folder contains no downloaded files, sir.", None

            latest_file = max(files, key=lambda f: f.stat().st_mtime)

            # Security Guard: Verify file is safe to launch
            is_safe, reason = file_access_guard.validate_file_launch(latest_file)
            if not is_safe:
                logger.warning(f"Blocked automatic execution of latest download: {reason}")
                return False, reason, str(latest_file)

            os.startfile(str(latest_file))
            logger.info(f"Opened latest downloaded file: {latest_file.name}")
            return True, f"Opening your latest download, {latest_file.name}, sir.", str(latest_file)
        except Exception as e:
            logger.error(f"Error opening latest download: {e}")
            return False, "I was unable to open your latest downloaded file, sir.", None


# Global default instance
file_manager = FileManager()

