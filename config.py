"""
Global Configuration File
-------------------------
This file stores all application settings.
Other modules will import values from here.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# =====================================
# Project Directories & Paths
# =====================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR
DATA_DIR = BASE_DIR / "data"

load_dotenv(dotenv_path=BASE_DIR / ".env")

ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
ANIMATIONS_DIR = ASSETS_DIR / "animations"
ANIMATION_DIR = ASSETS_DIR / "animation"
FONTS_DIR = ASSETS_DIR / "fonts"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "app.log"

# =====================================
# Application Information
# =====================================

APP_NAME = "J.A.R.V.I.S"

APP_VERSION = "1.0.0"

AUTHOR = "Smit Tandel"

# =====================================
# Window Settings
# =====================================

WINDOW_WIDTH = 1600

WINDOW_HEIGHT = 900

WINDOW_TITLE = "J.A.R.V.I.S AI Assistant"

# =====================================
# Theme
# =====================================

THEME = "dark"

ACCENT_COLOR = "#00D4FF"

TEXT_COLOR = "#FFFFFF"

BACKGROUND_COLOR = "#0A0A0A"

# =====================================
# Voice & Language
# =====================================

WAKE_WORD = "jarvis"

# Default Speech-to-Text Language:
# "en-IN" enables fluent bilingual recognition (English, Indian accents, & Hinglish).
# Other options: "hi-IN" (Hindi), "en-US" (US English).
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en-IN")
STT_LANGUAGE = os.getenv("STT_LANGUAGE", DEFAULT_LANGUAGE)

VOICE_RATE = 180

# =====================================
# Secret values
# =====================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

APP_MODE = os.getenv("APP_MODE")

DEBUG = os.getenv("DEBUG")