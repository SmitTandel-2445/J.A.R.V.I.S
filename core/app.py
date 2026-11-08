from utils.logger import logger
import config
from ui.main_window import MainWindow
from core.app_state import AppState
from speech.tts import tts
from speech.stt import stt
from ai.gemini_client import brain
from core.router import ActionRouter, ActionResult
from nlp.intent_classifier import IntentType


class JarvisApp:

    def __init__(self):

        self.name = config.APP_NAME
        self.state = AppState.STARTING
        logger.info(f"Starting {self.name} startup sequence...")

        # Create the main window
        try:
            self.window = MainWindow(
                on_close_callback=self.shutdown,
                on_start_callback=self.start_listening,
                on_stop_callback=self.stop_listening,
            )
        except Exception:
            self.state = AppState.ERROR
            logger.exception("Failed to initialize main window during startup.")
            raise

    def initialize(self):

        self.state = AppState.INITIALIZING
        logger.info("Initializing J.A.R.V.I.S.")

        try:
            # 1. Initialize Text-to-Speech (TTS)
            self.tts = tts

            # 2. Initialize Speech-to-Text (STT)
            self.stt = stt

            # Mutual coordination: Pause mic when speaking to avoid hearing laptop speakers!
            def _on_tts_start(text):
                self.stt.pause()
                self.window.update_status("SPEAKING")

            def _on_tts_end(text):
                if not self.stt.is_running:
                    # Listener was explicitly stopped (e.g. user said "bye jarvis" or clicked STOP)
                    self.window.update_status("SYSTEM IDLE")
                else:
                    # Normal response completed: unpause mic and resume continuous listening!
                    self.stt.resume()
                    self.window.update_status("LISTENING")

            self.tts.on_start = _on_tts_start
            self.tts.on_end = _on_tts_end

            # Connect STT callbacks to UI
            self.stt.on_status = lambda status: self.window.update_status(status)
            self.stt.on_text = self.on_speech_recognized
            self.stt.on_error = lambda err: self.window.add_command_log(f"AUDIO ERROR: {err}", highlight=True)

            # 3. Initialize Gemini AI Brain & Action Router
            self.brain = brain
            self.router = ActionRouter(brain=self.brain)

            self.state = AppState.READY
            logger.info("J.A.R.V.I.S. is ready.")

            # Initial startup greeting
            self.tts.speak("All systems operational. Jarvis is online.")
        except Exception:
            self.state = AppState.ERROR
            logger.exception("Error during J.A.R.V.I.S. initialization.")
            raise

    def start_listening(self):
        """Starts the speech recognition listener in the background."""
        if hasattr(self, "stt") and self.stt:
            self.stt.start()

    def stop_listening(self):
        """Stops both speech recognition and any active speech synthesis."""
        if hasattr(self, "stt") and self.stt:
            self.stt.stop()
        if hasattr(self, "tts") and self.tts:
            self.tts.stop()

    def on_speech_recognized(self, text: str):
        """Dispatches recognized speech to UI and conversational handlers."""
        self.window.add_command_log(f"USER: {text}")
        logger.info(f"User Spoke: '{text}'")

        # Indicate AI processing
        self.window.update_status("THINKING")

        def _on_step(step_res: ActionResult, step_num: int, total: int):
            if total > 1:
                self.window.update_status(f"EXECUTING ({step_num}/{total})")
                if step_res.log_message:
                    self.window.add_command_log(step_res.log_message)

        def _on_result(res: ActionResult):
            if not res.spoken_response:
                self.window.update_status("LISTENING" if self.stt.is_running else "READY")
                return
            logger.info(f"Router action executed ({res.intent.value}): '{res.spoken_response}'")
            self.tts.speak(res.spoken_response)

            # Single commands are logged here (compound commands log each step via _on_step)
            if not res.data.get("compound") and res.log_message:
                self.window.add_command_log(res.log_message)

            # Voice command to go offline (e.g. "bye jarvis", "good bye jarvis", "go offline")
            if res.intent == IntentType.GO_OFFLINE:
                logger.info("Voice command to go offline received. Stopping STT listener.")
                self.stt.stop()
                self.window.add_command_log("SYSTEM HALTED", highlight=True)
                self.window.update_status("SYSTEM IDLE")

        def _on_error(err: str):
            logger.error(f"Action router error: {err}")
            self.tts.speak("I encountered a problem processing your request, sir.")
            self.window.add_command_log(f"ROUTER ERROR: {err}", highlight=True)

        # Route query through ActionRouter asynchronously (Fast-path local or Gemini AI)
        self.router.route_async(text, on_result=_on_result, on_error=_on_error, on_step=_on_step)

    def shutdown(self):

        if self.state in (AppState.SHUTTING_DOWN, AppState.OFFLINE):
            return

        self.state = AppState.SHUTTING_DOWN

        logger.info("Shutting down J.A.R.V.I.S.")

        if hasattr(self, "stt") and self.stt:
            self.stt.stop()

        if hasattr(self, "tts") and self.tts:
            self.tts.stop()
            self.tts.shutdown()

        self.state = AppState.OFFLINE

        logger.info("J.A.R.V.I.S. offline.")

    def run(self):
        logger.info("Launching GUI...")
        try:
            self.window.run()
        except KeyboardInterrupt:
            self.shutdown()
