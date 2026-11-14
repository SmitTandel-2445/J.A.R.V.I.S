"""
Speech-to-Text (STT) Module for J.A.R.V.I.S.
--------------------------------------------
Provides continuous, non-blocking microphone listening and speech recognition
in a background thread. Features:
- Ambient noise calibration
- Automatic pause during TTS speech (preventing echo loop)
- Graceful network & timeout error handling
- Callback-driven architecture for UI integration
"""

import threading
import time
from typing import Callable, Optional
import speech_recognition as sr

import config
from utils.logger import logger


class SpeechRecognizer:
    """Manages microphone input and speech recognition on a background thread."""

    def __init__(
        self,
        device_index: Optional[int] = None,
        language: Optional[str] = None,
        pause_threshold: float = 0.8,
        on_text: Optional[Callable[[str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the speech recognizer.

        :param device_index: Index of audio input device (None uses system default)
        :param language: Language code for recognition (defaults to config.STT_LANGUAGE or 'en-IN')
        :param pause_threshold: Seconds of non-speaking audio before phrase is complete
        :param on_text: Callback triggered when speech is recognized: on_text(text)
        :param on_status: Callback triggered when listener status changes (e.g. LISTENING, TRANSCRIBING)
        :param on_error: Callback triggered on recognition or hardware error
        """
        self.device_index = device_index
        self.language = language or getattr(config, "STT_LANGUAGE", getattr(config, "DEFAULT_LANGUAGE", "en-IN"))
        self.pause_threshold = pause_threshold

        self.on_text = on_text
        self.on_status = on_status
        self.on_error = on_error

        self._recognizer = sr.Recognizer()
        self._recognizer.pause_threshold = self.pause_threshold
        self._recognizer.dynamic_energy_threshold = True

        self._is_running = False
        self._is_paused = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Try to resolve a working microphone source
        self._mic = self._get_microphone()

    def _get_microphone(self) -> Optional[sr.Microphone]:
        """Tries to create a Microphone instance, falling back to system default if index fails."""
        # Try specified device_index first
        if self.device_index is not None:
            try:
                mic = sr.Microphone(device_index=self.device_index)
                logger.info(f"Initialized microphone on device index {self.device_index}.")
                return mic
            except Exception as e:
                logger.warning(
                    f"Could not use microphone device index {self.device_index} ({e}). "
                    "Falling back to system default."
                )

        # Fallback to default
        try:
            mic = sr.Microphone()
            logger.info("Initialized microphone using system default input device.")
            return mic
        except Exception:
            logger.exception("No working audio input device / microphone could be found.")
            return None

    def calibrate(self, duration: float = 1.0) -> None:
        """Calibrates energy threshold based on ambient background noise."""
        if not self._mic:
            return

        try:
            logger.info("Calibrating microphone for ambient room noise...")
            if self.on_status:
                self.on_status("CALIBRATING MIC...")

            with self._mic as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=duration)

            logger.info(
                f"Microphone calibrated. Energy threshold set to: {self._recognizer.energy_threshold:.1f}"
            )
        except Exception:
            logger.exception("Failed during ambient noise calibration.")

    def _listen_loop(self) -> None:
        """Continuous background listening loop."""
        if not self._mic:
            logger.error("Cannot start speech recognition listener: no microphone available.")
            if self.on_error:
                self.on_error("No microphone device available.")
            return

        # Perform initial noise adjustment
        self.calibrate(duration=1.0)

        while self._is_running:
            # Check if paused (e.g. while J.A.R.V.I.S. is speaking aloud)
            if self._is_paused:
                time.sleep(0.1)
                continue

            try:
                if self.on_status:
                    self.on_status("LISTENING")

                with self._mic as source:
                    # Listen for audio chunk with a 5 second phrase timeout
                    audio = self._recognizer.listen(
                        source,
                        timeout=5.0,
                        phrase_time_limit=10.0,
                    )

                if not self._is_running or self._is_paused:
                    continue

                # Audio captured, now transcribing
                if self.on_status:
                    self.on_status("TRANSCRIBING...")

                text = self._recognizer.recognize_google(
                    audio,
                    language=self.language,
                )

                text = text.strip()
                if text:
                    logger.info(f"Speech Recognized: '{text}'")
                    if self.on_text:
                        self.on_text(text)

            except sr.WaitTimeoutError:
                # Normal: user didn't speak within the 5s window
                continue
            except sr.UnknownValueError:
                # Audio heard, but words could not be deciphered
                continue
            except sr.RequestError as e:
                logger.warning(f"Google Speech Recognition service unreachable: {e}")
                if self.on_error:
                    self.on_error("Speech recognition network error.")
                time.sleep(1.0)
            except OSError as e:
                logger.error(f"Microphone stream error: {e}")
                if self.on_error:
                    self.on_error("Microphone hardware error.")
                time.sleep(1.0)
            except Exception:
                logger.exception("Unexpected error in speech recognition loop.")
                time.sleep(0.5)

        logger.info("Speech recognition listener loop exited.")

    def start(self) -> None:
        """Starts the background listening thread."""
        with self._lock:
            if self._is_running:
                logger.info("Speech recognizer is already running.")
                return

            self._is_running = True
            self._is_paused = False

            self._thread = threading.Thread(
                target=self._listen_loop,
                name="JARVIS-STT-Worker",
                daemon=True,
            )
            self._thread.start()
            logger.info("Speech recognizer background thread started.")

    def stop(self) -> None:
        """Stops the listening thread cleanly."""
        with self._lock:
            self._is_running = False
            self._is_paused = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("Speech recognizer stopped.")

    def pause(self) -> None:
        """Temporarily pauses listening (used when J.A.R.V.I.S. is speaking)."""
        self._is_paused = True

    def resume(self) -> None:
        """Resumes listening after pause."""
        self._is_paused = False

    def set_language(self, language_code: str) -> None:
        """Dynamically sets or updates speech recognition language (e.g. 'en-IN', 'hi-IN', 'en-US')."""
        self.language = language_code
        logger.info(f"Speech recognition language switched to: {language_code}")

    @property
    def is_running(self) -> bool:
        """Returns True if the recognizer thread is running."""
        return self._is_running

    @property
    def is_listening(self) -> bool:
        """Returns True if the recognizer is running and actively listening."""
        return self._is_running and not self._is_paused


# Global default instance (pre-configured with device_index=1 or system default)
stt = SpeechRecognizer(device_index=1)

