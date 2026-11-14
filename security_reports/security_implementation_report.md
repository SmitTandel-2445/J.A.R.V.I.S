# J.A.R.V.I.S. Security Implementation Report

**Date:** 2026-11-14  
**Author:** Senior Cybersecurity Engineer & Desktop AI Agent Security Specialist  
**Application:** J.A.R.V.I.S. Desktop AI Voice Assistant  
**Status:** Successfully Implemented & Verified  

---

## 1. Architectural Overview

Prior to implementation, J.A.R.V.I.S. dispatched user intents directly to execution controllers without a centralized security gateway.

We designed and implemented a modular security architecture inside `core/security/` that intercepts all commands before execution:

```
USER VOICE / TEXT INPUT
        │
        ▼
SPEECH RECOGNITION (speech/stt.py)
        │
        ▼
NLP / AI COMMAND CLASSIFIER (nlp/intent_classifier.py)
        │
        ▼
CENTRAL SECURITY MANAGER (core/security/security_manager.py)
        │
        ├── COMMAND VALIDATION (core/security/command_validator.py)
        │     • Blocks shell injection metacharacters
        │     • Protects Windows critical and J.A.R.V.I.S. core processes
        │     • Validates URLs and executable names
        │
        ├── FILE ACCESS GUARD (core/security/file_access_guard.py)
        │     • Sandboxes operations to approved user directories
        │     • Rejects path traversal escapes (../, ..\)
        │     • Blocks auto-execution of risky file extensions (.exe, .bat, .vbs)
        │
        ├── RISK CLASSIFIER (core/security/action_classifier.py)
        │     • Classifies actions into Risk Levels 1 to 4
        │
        ├── PERMISSION MANAGER (core/security/permission_manager.py)
        │     • Evaluates operational policy (Balanced / Strict / Permissive)
        │
        └── CONFIRMATION MANAGER (core/security/confirmation_manager.py)
              • Dynamic authorization challenge-response for High/Critical actions
              • Expiration timers (defeating audio replay attacks)
              • Strict positive/negative confirmation parser
        │
        ▼
AUTHORIZED TOOL EXECUTION (core/router.py)
        │
        ▼
SECURITY AUDIT LOG (core/security/audit_logger.py)
```

---

## 2. Implemented Security Modules

### 2.1 `core/security/action_classifier.py`
- Implements `RiskLevel` enumeration:
  - **LEVEL 1 — LOW RISK:** Read-only queries, general conversation, time, battery, telemetry.
  - **LEVEL 2 — MODERATE RISK:** Launching approved apps, safe browsing, taking screenshots, window navigation.
  - **LEVEL 3 — HIGH RISK:** File creation, process termination, system sleep/lock, text injection.
  - **LEVEL 4 — CRITICAL RISK:** Permanent deletion (Recycle Bin), administrative execution, dangerous utilities.
- Classifies each intent and its parameters dynamically.

### 2.2 `core/security/command_validator.py`
- Enforces sanitization of null bytes and non-printable control characters.
- Detects and rejects shell metacharacters (`&`, `|`, `;`, `>`, `<`, `` ` ``, `$`).
- Protects critical Windows system processes (`System`, `Registry`, `smss.exe`, `csrss.exe`, `wininit.exe`, `services.exe`, `lsass.exe`, `svchost.exe`, `fontdrvhost.exe`, `winlogon.exe`, `dwm.exe`, `explorer.exe`, `spoolsv.exe`, `taskhostw.exe`).
- Protects J.A.R.V.I.S. from self-termination via process kill (`python.exe`, `pythonw.exe`).
- Disallows ambiguous single-character process termination targets (`len(name) < 2`).
- Enforces safe URL schemes (`https://`, `http://`) and blocks prohibited schemes (`file://`, `javascript:`, `data:`).

### 2.3 `core/security/file_access_guard.py`
- Establishes approved directory boundaries:
  - `~/Desktop` (and OneDrive Desktop)
  - `~/Downloads`
  - `~/Documents` (and OneDrive Documents)
  - `~/Pictures`
  - `~/Videos`
  - `~/Music`
- Rejects directory traversal attempts (`..`, `/`, `\`) in folder creation.
- Enforces safe extension allowlist for downloaded files, blocking automatic execution of `.exe`, `.bat`, `.cmd`, `.vbs`, `.ps1`, `.scr`, `.msi`, `.reg`, `.dll`.

### 2.4 `core/security/confirmation_manager.py`
- Provides thread-safe holding of pending high-risk actions.
- Assigns unique dynamic action IDs.
- Implements a 30-second sliding timeout window to prevent replay attacks.
- Supports explicit positive confirmations (`yes`, `confirm`, `proceed`, `affirmative`) and negative cancellations (`no`, `cancel`, `abort`, `nevermind`).
- Automatically cancels pending requests upon receiving unrelated commands to prevent confirmation hijacking.

### 2.5 `core/security/permission_manager.py`
- Configurable operational policy modes (`BALANCED`, `STRICT`, `PERMISSIVE`).
- Automatically routes Level 4 (Critical) and destructive Level 3 actions to the confirmation gate.

### 2.6 `core/security/tool_registry.py`
- Centralized registry of all application tools and capabilities.
- Categorizes tools into `READ_ONLY`, `WRITE`, `SYSTEM_CONTROL`, and `DESTRUCTIVE`.
- Prevents arbitrary tool invocation and verifies required parameter schemas.

### 2.7 `core/security/audit_logger.py`
- Dedicated security audit log (`logs/security_audit.log`).
- Backed by `RotatingFileHandler` (5MB max size, 5 backup archives).
- Automatic regex-based redaction of API keys, tokens, and authorization headers (`***REDACTED***`).
- Structured audit event tracking (`ACTION_EVALUATED`, `CONFIRMATION_REQUESTED`, `CONFIRMATION_OUTCOME`, `ACTION_BLOCKED`).

### 2.8 `core/security/security_manager.py`
- Unifies all security guards and serves as the single point of contact for `ActionRouter`.

---

## 3. Integration with Existing Application Core

1. **`core/router.py`**:
   - `ActionRouter.__init__` now accepts and instantiates `SecurityManager`.
   - `route()` checks for pending confirmation responses first before parsing new intents.
   - `_execute_single_intent()` passes every intent through `self.security.evaluate()`.
   - Blocked actions return polite spoken security explanations.
   - Actions requiring confirmation pause execution and prompt the user.

2. **`automation/app_launcher.py`**:
   - Removed direct `os.startfile(clean_name)` fallback.
   - Replaced loose substring matching in `close()` with exact process name matching.
   - Validates all process termination requests through `CommandValidator`.

3. **`system/task_manager.py`**:
   - `end_process()` now verifies target with `CommandValidator` and blocks terminating protected OS processes.
   - Removed broad substring termination (`pname.startswith` / `in pname`).

4. **`automation/file_manager.py`**:
   - `create_folder()` enforces `FileAccessGuard` directory confinement.
   - `open_latest_download()` validates file extension safety before opening.

5. **`utils/logger.py`**:
   - Upgraded to `RotatingFileHandler` with 5MB limit.
   - Added `RedactingFormatter` to automatically mask credentials.

6. **Controllers Safety**:
   - Re-enabled `pyautogui.FAILSAFE = True` across `shortcut_controller.py`, `clipboard_controller.py`, and `screenshot_controller.py`.
   - `clipboard_controller.py` now detects credentials on the clipboard and suppresses reading them aloud.

7. **`ai/prompts.py`**:
   - Added Section 4: Security & System Integrity Boundaries to `JARVIS_SYSTEM_INSTRUCTION`.

8. **`requirements.txt`**:
   - Pinned all dependencies to exact, verified stable versions.

