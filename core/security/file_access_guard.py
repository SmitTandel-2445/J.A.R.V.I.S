"""
File Access & System Guard Module for J.A.R.V.I.S.
---------------------------------------------------
Enforces file system boundaries, prevents path traversal attacks, restricts
operations to approved user folders, and blocks execution of dangerous downloaded files.
"""

import os
from pathlib import Path
from typing import List, Optional, Set, Tuple


class FileAccessGuard:
    """Guards file system operations, directory boundaries, and file extensions."""

    # Prohibited executable / script extensions for automatic opening
    DANGEROUS_EXTENSIONS: Set[str] = {
        ".exe", ".bat", ".cmd", ".vbs", ".vbe", ".ps1", ".psm1", ".psd1",
        ".scr", ".msi", ".msp", ".reg", ".dll", ".com", ".hta", ".cpl",
        ".jar", ".wsf", ".wsh", ".pif", ".lnk",
    }

    # Safe document and media extensions allowed for automatic launch
    SAFE_OPEN_EXTENSIONS: Set[str] = {
        ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
        ".txt", ".csv", ".json", ".xml", ".md",
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg",
        ".mp3", ".wav", ".m4a", ".flac", ".mp4", ".mkv", ".avi", ".mov",
    }

    def __init__(self, user_home: Optional[str] = None):
        """Initializes approved directory roots for the user profile."""
        self.user_home = Path(user_home or os.path.expanduser("~")).resolve()

        # Approved user working directories
        self.approved_roots: List[Path] = [
            (self.user_home / "Desktop").resolve(),
            (self.user_home / "Downloads").resolve(),
            (self.user_home / "Documents").resolve(),
            (self.user_home / "Pictures").resolve(),
            (self.user_home / "Videos").resolve(),
            (self.user_home / "Music").resolve(),
        ]

        # Also support OneDrive redirection if present
        onedrive_desktop = (self.user_home / "OneDrive" / "Desktop").resolve()
        if onedrive_desktop.exists():
            self.approved_roots.append(onedrive_desktop)

        onedrive_docs = (self.user_home / "OneDrive" / "Documents").resolve()
        if onedrive_docs.exists():
            self.approved_roots.append(onedrive_docs)

        # Critical OS directories that are strictly write-protected
        self.protected_system_dirs: List[Path] = [
            Path(os.environ.get("SystemRoot", r"C:\Windows")).resolve(),
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")).resolve(),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")).resolve(),
            Path(r"C:\ProgramData").resolve(),
        ]

    def is_within_approved_directory(self, target_path: Path) -> bool:
        """Checks if target_path resides within one of the approved user roots."""
        try:
            resolved = target_path.resolve()
            return any(
                resolved == root or root in resolved.parents
                for root in self.approved_roots
            )
        except Exception:
            return False

    def is_in_system_directory(self, target_path: Path) -> bool:
        """Checks if target_path resides within protected Windows system folders."""
        try:
            resolved = target_path.resolve()
            return any(
                resolved == sys_dir or sys_dir in resolved.parents
                for sys_dir in self.protected_system_dirs
            )
        except Exception:
            return True

    def validate_folder_creation(self, base_dir: Path, requested_name: str) -> Tuple[bool, Optional[Path], str]:
        """
        Validates folder creation, ensuring no path traversal escapes base_dir.

        :param base_dir: Approved parent directory (e.g. Desktop)
        :param requested_name: Folder name supplied by user
        :return: (is_valid: bool, canonical_path: Optional[Path], error_message: str)
        """
        clean_name = requested_name.strip()
        if not clean_name:
            return False, None, "Folder name cannot be empty."

        # Reject explicit traversal characters
        if ".." in clean_name or "/" in clean_name or "\\" in clean_name:
            return False, None, f"Directory traversal pattern detected in folder name '{clean_name}'."

        try:
            target = (base_dir / clean_name).resolve()
            # Verify target parent is strictly base_dir
            if target.parent != base_dir.resolve():
                return False, None, f"Resolved target escapes approved base directory: '{target}'."

            # Verify target is in approved directory
            if not self.is_within_approved_directory(target):
                return False, None, f"Target directory is outside approved user folders: '{target}'."

            return True, target, ""
        except Exception as e:
            return False, None, f"Failed to resolve target path: {e}"

    def validate_file_launch(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validates that a file is safe to launch via os.startfile.
        Blocks automatic launching of dangerous executables and scripts.

        :param file_path: Full path to target file
        :return: (is_safe: bool, reason: str)
        """
        try:
            resolved = file_path.resolve()
            if not resolved.exists():
                return False, f"File does not exist: {resolved.name}"

            ext = resolved.suffix.lower()

            # Block executable scripts and binaries
            if ext in self.DANGEROUS_EXTENSIONS:
                return False, (
                    f"Execution blocked: '{resolved.name}' has a high-risk executable extension ({ext}). "
                    "Automatic opening of executable files is disabled for your protection."
                )

            # Check if within approved user roots
            if not self.is_within_approved_directory(resolved):
                return False, f"File '{resolved.name}' is located outside approved user directories."

            return True, ""
        except Exception as e:
            return False, f"Error validating file launch: {e}"


# Global default instance
file_access_guard = FileAccessGuard()

