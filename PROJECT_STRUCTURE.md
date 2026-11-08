# J.A.R.V.I.S. Project Structure & Architecture Guide

This document explains the purpose, role, and responsibilities of every folder and file in the J.A.R.V.I.S. workspace.

---

## Workspace Directory Overview

```text
J.A.R.V.I.S/
├── .vscode/               # IDE configuration & environment settings
├── ai/                    # LLM engines, prompts, and AI reasoning pipelines
├── assets/                # Multimedia assets (animations, icons, fonts, sounds, images)
├── automation/            # OS automations, desktop scripts, and system tasks
├── cache/                 # Temporary cached data, models, and session audio
├── core/                  # Core application orchestration and state machine
├── data/                  # Static data, user configurations, and reference tables
├── database/              # SQLite database schemas, migrations, and local storage
├── docs/                  # Project documentation, guides, and API specs
├── logs/                  # Application runtime logs
├── memory/                # Context management, short-term memory, and long-term memory
├── models/                # Local offline AI/ML weights (wake word, offline STT/VAD)
├── nlp/                   # Natural language processing, entity extraction, intent parsers
├── plugins/               # External modular integrations and third-party tools
├── skills/                # Specific command capabilities (weather, news, media, system)
├── speech/                # Speech-to-Text (STT), Text-to-Speech (TTS), and audio streams
├── system/                # Hardware metrics, volume, brightness, OS controls
├── tests/                 # Unit, integration, and subsystem test suites
├── ui/                    # CustomTkinter GUI layout, widgets, themes, and canvas graphics
├── utils/                 # General utility helpers (logger, path helpers, decorators)
├── vision/                # Webcam, screen analysis, OCR, and vision AI processing
├── .env                   # Environment secrets and API keys (ignored by git)
├── .gitignore             # Git ignore definitions
├── config.py              # Central application configuration & reliable paths
├── main.py                # Main application entry point
├── plan.md                # Phase-by-phase implementation roadmap
├── PROJECT_STRUCTURE.md   # This documentation file
└── requirements.txt       # Python package dependencies
```

---

## Detailed Directory Breakdown

### 1. `core/` (Application Engine & State Machine)
The central nervous system of J.A.R.V.I.S. Orchestrates all subsystems and coordinates background threads with the main UI loop.
- **`app.py`**: Initializes the main application, instantiates the UI, manages the subsystem startup/shutdown sequence, and handles safe signal interrupts (Ctrl+C).
- **`app_state.py`**: Defines standard runtime states (`STARTING`, `INITIALIZING`, `READY`, `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`, `SHUTTING_DOWN`, `OFFLINE`).

### 2. `ui/` (Graphical User Interface)
Built with **CustomTkinter**, designed with a futuristic Iron Man / sci-fi holographic theme.
- **`main_window.py`**: The primary GUI window containing:
  - Header with system title and real-time status banner.
  - Left panel: Circular system telemetry meters (CPU, RAM, Battery) with real-time updates.
  - Center panel: Smooth 192-frame animated Arc Reactor, dynamic audio waveform visuals, and date/time displays.
  - Right panel: Controls, microphone toggle, audio status, and terminal log window.
  - Clean shutdown hooks (`on_close`, timer cancellations).
- **`theme.py`**: Centralized UI color palette, fonts, padding, and UI element sizing.

### 3. `assets/` (Static Multimedia)
Holds all static files loaded by the interface and audio systems.
- **`animation/frames/`** & **`animations/frames/`**: Pre-rendered 192 high-resolution, transparent PNG frames of the animated Arc Reactor.
- **`icons/`**: Control and telemetry icons (`start.png`, `stop.png`, `microphone.png`, `volume.png`, `battery.png`, `cpu.png`, `ram.png`, `wifi.png`, `settings.png`).
- **`fonts/`**: Custom fonts (e.g. Chakra Petch, Horizon).
- **`images/`**: Logos and static graphics (`logo.png`, `ironman.jpeg`).
- **`sound/`**: Audio cues (startup chimes, wake sound, confirmation beeps).

### 4. `speech/` (Speech & Audio Subsystem)
Handles human voice interaction, speech synthesis, and microphone listening.
- **`speech_recognition.py` (Planned)**: Listens to the microphone, handles noise calibration, and converts speech to text using Google STT / Whisper.
- **`tts.py` (Planned)**: Text-to-Speech synthesis converting J.A.R.V.I.S. textual responses into spoken audio using `pyttsx3` or neural voices (`edge-tts`).
- **`wake_word.py` (Planned)**: Lightweight background listener detecting the trigger phrase *"Jarvis"*.
- **`audio_stream.py` (Planned)**: PyAudio / SoundDevice input capture feeding real-time audio amplitude into UI waveform graphics.

### 5. `ai/` (Intelligence & Reasoning Engine)
Houses the AI logic, LLM API connectors, and prompt management.
- **`gemini_client.py` (Planned)**: Direct API client for Google Gemini (using the official Google GenAI SDK), processing complex user queries.
- **`prompts.py` (Planned)**: System personas, tone instructions, and few-shot examples for J.A.R.V.I.S. personality.
- **`decision_engine.py` (Planned)**: Decides whether a user command is a local system action (e.g. "open notepad") or an AI conversation question (e.g. "explain quantum mechanics").

### 6. `nlp/` (Natural Language Processing)
Interprets user intent and extracts parameters without always needing heavy cloud calls.
- **`intent_classifier.py` (Planned)**: Identifies user intents (`open_app`, `system_control`, `web_search`, `general_query`, `media_control`).
- **`entity_extractor.py` (Planned)**: Extracts target names, apps, search queries, or parameters from spoken input.

### 7. `memory/` (Context & Memory Storage)
Maintains conversational context and personal knowledge about the user.
- **`short_term_memory.py` (Planned)**: Tracks current session chat history and multi-turn conversational context.
- **`long_term_memory.py` (Planned)**: Persistent memory (user name, preferences, favorite apps, custom facts) stored across restarts.

### 8. `automation/` & `system/` (OS Control & Desktop Automation)
Enables J.A.R.V.I.S. to interact with Windows.
- **`app_launcher.py` (Planned)**: Opens and closes Windows applications and games.
- **`system_controller.py` (Planned)**: Controls system volume, mute, brightness, Wi-Fi, battery status, and lock/sleep commands.
- **`media_player.py` (Planned)**: Controls playback (play/pause/next/prev) via Windows media APIs or keyboard hooks.
- **`browser_controller.py` (Planned)**: Opens URLs, performs Google/YouTube searches, and handles browser tabs.

### 9. `skills/` (Modular Commands & Tools)
Independent feature plugins that J.A.R.V.I.S. can execute on demand.
- **`weather_skill.py` (Planned)**: Fetches real-time weather and forecast.
- **`news_skill.py` (Planned)**: Retrieves top headlines and topic summaries.
- **`time_skill.py` (Planned)**: Alarms, timers, world clocks, and date inquiries.
- **`notes_skill.py` (Planned)**: Quick notepad drafting and note retrieval.

### 10. `vision/` (Multimodal & Visual Capabilities)
Allows J.A.R.V.I.S. to "see" what is on screen or in front of the camera.
- **`screen_capture.py` (Planned)**: Captures screenshot of current display for multimodal AI inspection.
- **`webcam.py` (Planned)**: Optional camera feed for face recognition or object analysis with Gemini Vision.

### 11. `database/` & `data/` (Storage & Schemas)
- **`database/`**: SQLite database management, storing conversation history, custom commands, and reminders.
- **`data/`**: Static JSON/YAML files (e.g., standard app paths on Windows, preset commands).

### 12. `utils/` (Cross-Cutting Helpers)
- **`logger.py`**: Configured logging system writing timestamps, log levels, and messages simultaneously to the terminal and `logs/app.log`.
- **`helpers.py` (Planned)**: String sanitizers, time formatters, and OS helper utilities.

### 13. Root Level Files
- **`config.py`**: Global configuration module. Contains app metadata, window geometry, color schemes, reliable `pathlib.Path` references (`BASE_DIR`, `ASSETS_DIR`, `LOGS_DIR`), and `.env` loading.
- **`main.py`**: Entry point that bootstraps `JarvisApp`, registers signal traps, and starts the event loop.
- **`requirements.txt`**: Specifies all required Python packages.
- **`.env`**: Stores sensitive API credentials (e.g. `GEMINI_API_KEY`).
- **`plan.md`**: Master roadmap detailing phases, deliverables, and progress tracking.
- **`test_*.py`**: Standalone test scripts used to verify microphone, speaker, and speech recognition hardware.

