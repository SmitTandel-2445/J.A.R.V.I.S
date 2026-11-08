# J.A.R.V.I.S. — Just A Rather Very Intelligent System

<p align="center">
  <img src="assets/images/ironman_icon.png" alt="J.A.R.V.I.S. Logo" width="180"/>
</p>

<p align="center">
  <b>A voice-controlled Iron Man Mark VII AI Desktop Assistant built with Python, CustomTkinter, and Google Gemini AI.</b>
</p>

---

## 🌟 Features

### 1. Cybernetic Iron Man HUD Interface
- **Animated Arc Reactor:** Central spinning core with rotating HUD reticle, cardinal measurement rings (000°, 090°, 180°, 270°), and tactical crosshairs.
- **Dynamic Acoustic Sound Waves:** Dual harmonic sound waves for input (listening) and output (speaking) that animate with vocal activity.
- **Top HUD & Live Telemetry Marquee:** Glowing energy chevrons, real-time AI latency monitor, and continuous telemetry ticker streaming CPU, RAM, Wi-Fi, and Uptime.
- **Synchronized Breathing Neon Borders:** Cyber cyan borders pulsing smoothly across all HUD panels.

### 2. Conversational AI Brain
- Powered by **Google Gemini AI** for intelligent reasoning, multi-turn conversations, contextual awareness, and conversational personality.
- Speech Recognition (STT) and dynamic Text-to-Speech (TTS) integration.

### 3. Desktop & System Automations
- **Window Management:** Minimize, maximize, restore, snap, and close applications hands-free. Includes self-window control (*"Jarvis, minimize yourself"*).
- **System Telemetry:** Real-time query of CPU, RAM, battery status, disk space, Wi-Fi network, and uptime.
- **Hardware Controls:** System volume and screen brightness control.
- **Media & Browser Controls:** Web searches, YouTube playback, Spotify playback, and browser tab navigation.
- **Productivity & Shortcuts:** Focus timers, clipboard copy/paste automation, and global shortcuts.

---

## 🚀 Getting Started

### Prerequisites
- Windows 10 or 11
- Python 3.10+ (tested with Python 3.13)
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SmitTandel-2445/J.A.R.V.I.S.git
   cd J.A.R.V.I.S
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy `.env.example` to `.env` and insert your Gemini API key:
   ```bash
   copy .env.example .env
   ```
   Edit `.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DEBUG=False
   APP_MODE=production
   ```

---

## 🖥️ Running J.A.R.V.I.S.

### Option A: From Terminal
```bash
python main.py
```

### Option B: Create Desktop Shortcut
Generate a Windows Desktop shortcut with the custom Iron Man icon:
```bash
python utils/create_desktop_shortcut.py
```
This adds a **J.A.R.V.I.S.** shortcut to your Desktop that launches with one click!

---

## 📁 Project Structure

```
J.A.R.V.I.S/
├── ai/                 # Gemini Brain and LLM integration
├── assets/             # Icons, sounds, animations, and reactor frames
├── automation/         # Window, browser, shortcut, and spotify controllers
├── core/               # Application lifecycle, routing, and context manager
├── data/               # Persistent application cache and state
├── nlp/                # Intent classifier and regex patterns
├── speech/             # Speech-to-Text and Text-to-Speech engines
├── system/             # Telemetry, battery, brightness, and audio controllers
├── tests/              # Test suites and regression verifications
├── ui/                 # CustomTkinter Mark VII HUD and widgets
├── utils/              # Shortcut generator and logging utilities
├── config.py           # Centralized configuration
├── main.py             # Application entry point
├── requirements.txt    # Project dependencies
└── .env.example        # Environment variable template
```

---

## 🛡️ License & Acknowledgments
Created by **Smit Tandel**. Inspired by Marvel's Iron Man and Stark Industries.
