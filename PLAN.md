# J.A.R.V.I.S. Master Development Plan

A step-by-step, phase-by-phase roadmap for building the complete J.A.R.V.I.S. AI desktop assistant together.

---

## Current Status & Overview

- [x] **Phase 1: Core Foundation & UI Architecture** (Completed & Tested)
- [x] **Phase 2: Speech & Audio Subsystem** (Completed & Tested)
- [x] **Phase 3: AI Brain & LLM Integration** (Completed & Tested)
- [x] **Phase 4: Intent Recognition & Action Routing** (Completed & Tested)
- [x] **Phase 5: Desktop Automation & System Control** (Completed & Tested)
- [ ] **Phase 6: Memory, Persistence & Context** (Next Priority)
- [ ] **Phase 7: Modular Skills & Vision**
- [ ] **Phase 8: Polish, Visual Reactivity & Packaging**

---

## Phase 1: Core Foundation & UI Architecture
> **Status: COMPLETED (Verified with Module 19 Integration Suite)**

- [x] **Project Scaffolding**: Setup virtual environment, dependencies (`requirements.txt`), and `.env`.
- [x] **Futuristic GUI Layout**: CustomTkinter 3-column layout (System Telemetry, Arc Reactor Center, Control Panel).
- [x] **Smooth Arc Reactor Animation**: Pre-rendered 192 transparent frames running at 24 FPS via non-blocking `after()` callbacks.
- [x] **System Telemetry**: Real-time circular meters for CPU, RAM, and Battery with safe missing-sensor fallbacks.
- [x] **Reliable Path Management (`config.py`)**: Centralized `pathlib.Path` configuration independent of terminal CWD.
- [x] **Logging System (`utils/logger.py`)**: Dual-output logging (Terminal + `logs/app.log`) with automatic folder creation.
- [x] **Safe Shutdown Lifecycle**: Clean `on_close` handler, re-entrancy protection, timer cancellation, and Ctrl+C trapping.

---

## Phase 2: Speech & Audio Subsystem
> **Goal:** Enable J.A.R.V.I.S. to hear user commands through the microphone and speak responses with natural audio output.

- [x] **2.1. Modular Text-to-Speech (`speech/tts.py`)**:
  - Encapsulate `pyttsx3` into a dedicated `TTSEngine` class.
  - Implement non-blocking speech playback using background worker threads so the GUI never freezes.
  - Add voice selection (male/female), speech rate, and volume controls bound to `config.py`.
- [x] **2.2. Robust Speech Recognition (`speech/stt.py`)**:
  - Build `SpeechRecognizer` using `speech_recognition` with automatic ambient noise calibration.
  - Support microphone device selection with automatic fallback to system default.
  - Implement phrase timeout and energy threshold tuning for reliable voice capture.
- [ ] **2.3. Audio Visualizer Link (`speech/audio_stream.py`)**:
  - Capture real-time audio amplitude using `sounddevice` or `PyAudio`.
  - Feed RMS energy levels into the center panel's `input_wave` and `output_wave` canvas elements.
- [x] **2.4. GUI Integration**:
  - Wire the Right Panel **Start / Stop** buttons and **Microphone** button to start and stop the listener.
  - Sync runtime states (`LISTENING`, `SPEAKING`, `READY`) with the status label and UI badges.

---

## Phase 3: AI Brain & LLM Integration
> **Goal:** Give J.A.R.V.I.S. natural intelligence, reasoning, and conversational ability powered by Google Gemini.

- [x] **3.1. Gemini API Client (`ai/gemini_client.py`)**:
  - Configure the modern Google GenAI SDK (`google-genai`).
  - Read `GEMINI_API_KEY` securely from `.env`.
  - Implement streaming response generation for rapid response times.
- [x] **3.2. J.A.R.V.I.S. Persona & System Prompts (`ai/prompts.py`)**:
  - Craft a polite, witty, concise, and helpful AI assistant personality inspired by Tony Stark's J.A.R.V.I.S.
  - Enforce response length constraints suitable for voice read-back (avoiding walls of text).
- [x] **3.3. Offline & Network Resilience**:
  - Add timeout and network retry policies.
  - Provide graceful spoken fallbacks if the internet connection is offline or API limits are reached.

---

## Phase 4: Intent Recognition & Action Routing
> **Goal:** Distinguish between general conversation ("How far is Mars?") and direct computer actions ("Open Chrome", "Mute volume").
> **Status: COMPLETED (Verified with Unit & Integration Tests)**

- [x] **4.1. Fast Pattern Matching (`nlp/intent_classifier.py`)**:
  - High-speed regex / keyword matching for common local commands without consuming API tokens.
- [x] **4.2. Action Router (`core/router.py`)**:
  - Direct matched commands to the appropriate handler:
    - *System Commands* $\rightarrow$ `system/`
    - *App Automation* $\rightarrow$ `automation/`
    - *Skills* $\rightarrow$ `skills/`
    - *General Queries* $\rightarrow$ `ai/gemini_client.py`
- [x] **4.3. UI Activity Log Feed**:
  - Stream recognized queries and J.A.R.V.I.S. replies into the Right Panel terminal text box.

---

## Phase 5: Desktop Automation & System Control
> **Goal:** Enable hands-free voice control over Windows applications, volume, and browsing.
> **Status: COMPLETED (Verified with Unit & Integration Tests)**

- [x] **5.1. Windows Application Launcher (`automation/app_launcher.py`)**:
  - Open and close installed applications (Notepad, Chrome, VS Code, Spotify, Calculator, Command Prompt, etc.).
  - Intelligent alias resolution mapping spoken names to executables and URI protocols.
- [x] **5.2. System Audio & Telemetry Control (`system/audio_controller.py`)**:
  - Increase, decrease, set, or mute system audio volume via `pycaw`.
  - Check detailed battery diagnostics and runtime telemetry.
- [x] **5.3. Web & Media Automation (`automation/browser.py`)**:
  - "Search Google for [query]" $\rightarrow$ Opens formatted search in default browser.
  - "Play [song/artist] on YouTube" $\rightarrow$ Auto-opens YouTube search result.
- [x] **5.4. OS Power Management (`system/power_controller.py`)**:
  - Voice-triggered Lock Screen (`user32.LockWorkStation`) and Sleep mode.

---

## Phase 6: Memory, Persistence & Context
> **Goal:** Enable J.A.R.V.I.S. to remember previous conversations, user preferences, and custom notes.

- [ ] **6.1. Short-Term Session Context (`memory/short_term.py`)**:
  - Maintain a rolling multi-turn message history for coherent follow-up questions.
- [ ] **6.2. Local SQLite Storage (`database/db_manager.py`)**:
  - Store user profile details (user name, preferences, location).
  - Store conversation logs with timestamps for past recall.
- [ ] **6.3. User Preference Commands**:
  - "Remember that my favorite music genre is Synthwave" $\rightarrow$ Stores to database.
  - "What is my favorite music genre?" $\rightarrow$ Recalls from memory.

---

## Phase 7: Modular Skills & Vision
> **Goal:** Add specialized capabilities like real-time weather, reminders, and vision analysis.

- [ ] **7.1. Weather & News Skills (`skills/weather.py`, `skills/news.py`)**:
  - Real-time weather lookup via Open-Meteo (free, no API key required).
  - Top news headlines summary.
- [ ] **7.2. Timers, Alarms & Reminders (`skills/reminders.py`)**:
  - Spoken timers ("Set a timer for 10 minutes").
  - Background scheduler triggering voice alerts when time expires.
- [ ] **7.3. Multimodal Vision (`vision/screen_capture.py`)**:
  - "Jarvis, what's on my screen?" $\rightarrow$ Captures active display, sends to Gemini Vision, and speaks an intelligent description or summary.

---

## Phase 8: Final Polish, Audio Reactivity & Packaging
> **Goal:** Refine visuals, optimize performance, and create a standalone Windows executable.

- [ ] **8.1. Audio-Reactive UI Glow**:
  - Modulate the Arc Reactor glow intensity or pulse speed based on microphone input or voice output volume.
  - Update status banner and meter accent colors dynamically based on system state.
- [ ] **8.2. Wake Word Engine (`speech/wake_word.py`)**:
  - Optional hands-free wake word detection ("Hey Jarvis" / "Jarvis") using OpenWakeWord or Porcupine.
- [ ] **8.3. Packaging (`build/`)**:
  - Create a clean PyInstaller build specification (`jarvis.spec`) bundling all assets, frames, fonts, and icons into a standalone `.exe`.

