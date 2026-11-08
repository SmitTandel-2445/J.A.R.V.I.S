"""
J.A.R.V.I.S. Desktop Shortcut Generator
----------------------------------------
This utility script creates a Windows Desktop shortcut (.lnk) that launches
J.A.R.V.I.S. with the project virtual environment in 'Developer Mode' (GUI + Console).

Educational Overview:
1. TargetPath: Points to the virtual environment Python interpreter (venv\\Scripts\\python.exe).
   - Using 'python.exe' attaches a standard console window for live terminal logs.
   - Using 'pythonw.exe' would run the script silently without a console window.
2. Arguments: Specifies 'main.py' as the script to execute.
3. WorkingDirectory: Sets the project root folder so relative paths (assets/, .env) work.
4. IconLocation: Points to a multi-resolution Windows icon (.ico) file.
"""

import os
import sys
from PIL import Image
import win32com.client


def ensure_icon(project_root: str) -> str:
    """
    Ensures that a Windows .ico file exists for the shortcut.
    Prioritizes 'assets/jarvis_ironman.ico' (the custom Iron Man helmet icon).
    """
    ironman_ico = os.path.join(project_root, "assets", "jarvis_ironman.ico")
    if os.path.exists(ironman_ico):
        return ironman_ico

    icon_path = os.path.join(project_root, "assets", "jarvis.ico")
    logo_path = os.path.join(project_root, "assets", "images", "ironman_icon.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(project_root, "assets", "images", "logo.png")

    if not os.path.exists(icon_path) and os.path.exists(logo_path):
        img = Image.open(logo_path)
        icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        img.save(icon_path, format="ICO", sizes=icon_sizes)
        print(f"[ICON] Generated multi-resolution icon at: {icon_path}")
    return icon_path


def create_desktop_shortcut(mode: str = "dev") -> str:
    """
    Creates a desktop shortcut for J.A.R.V.I.S.
    
    :param mode: 'dev' for GUI + Console (python.exe), 'app' for GUI only (pythonw.exe)
    :return: Full path to the created .lnk shortcut file
    """
    # 1. Resolve Project Root and Active Desktop Path (handling OneDrive Desktop)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    shell = win32com.client.Dispatch("WScript.Shell")
    active_desktop = shell.SpecialFolders("Desktop")
    local_desktop = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop")

    desktop_dirs = list(dict.fromkeys([d for d in [active_desktop, local_desktop] if os.path.exists(d)]))

    # 2. Select Interpreter based on mode
    interpreter_name = "python.exe" if mode == "dev" else "pythonw.exe"
    python_exe = os.path.join(project_root, "venv", "Scripts", interpreter_name)

    if not os.path.exists(python_exe):
        # Fallback to current running Python if venv path is different
        python_exe = sys.executable

    # 3. Ensure Icon Exists
    icon_path = ensure_icon(project_root)

    # 4. Shortcut File Name & Description
    shortcut_name = "J.A.R.V.I.S.lnk"
    description = "J.A.R.V.I.S. AI Assistant (GUI + Live Diagnostic Console)"

    created_paths = []
    for d_dir in desktop_dirs:
        shortcut_path = os.path.join(d_dir, shortcut_name)
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = python_exe
        shortcut.Arguments = "main.py"
        shortcut.WorkingDirectory = project_root
        shortcut.Description = description

        if os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"

        shortcut.save()
        created_paths.append(shortcut_path)
        print(f"[SHORTCUT] Successfully created: {shortcut_path}")

    # 5. Notify Windows Explorer shell to refresh icons immediately
    try:
        import ctypes
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
    except Exception:
        pass

    return created_paths[0] if created_paths else ""


if __name__ == "__main__":
    create_desktop_shortcut(mode="dev")

