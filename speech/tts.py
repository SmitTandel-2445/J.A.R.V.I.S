"""
Text-to-Speech (TTS) Module for J.A.R.V.I.S.
--------------------------------------------
Provides non-blocking, thread-safe speech synthesis using pyttsx3.
Uses a producer-consumer Queue and a background daemon thread so speech
never freezes the UI event loop or main application thread.
"""

import queue
import re
import threading
from typing import Callable, List, Optional
import comtypes
import comtypes.client

import config
from utils.logger import logger


class TTSEngine:
    """Manages text-to-speech synthesis in a dedicated background worker thread using native Windows SAPI."""

    def __init__(
        self,
        rate: Optional[int] = None,
        volume: float = 1.0,
        voice_index: int = 0,
        on_start: Optional[Callable[[str], None]] = None,
        on_end: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the TTS Engine.

        :param rate: Speed of speech in words-per-minute (defaults to config.VOICE_RATE or 175)
        :param volume: Volume level between 0.0 (silent) and 1.0 (maximum)
        :param voice_index: Index of the voice (0 is Microsoft David on Windows)
        :param on_start: Optional callback function triggered when speech starts
        :param on_end: Optional callback function triggered when speech finishes
        """
        self.rate = rate if rate is not None else getattr(config, "VOICE_RATE", 175)
        self.volume = max(0.0, min(1.0, volume))
        self.voice_index = voice_index

        self.on_start = on_start
        self.on_end = on_end

        # Thread-safe queue for incoming speech text
        self._queue: queue.Queue[Optional[str]] = queue.Queue()
        self._is_speaking = False
        self._is_running = True
        self._lock = threading.Lock()

        # Native SAPI.SpVoice COM object initialized inside the worker thread
        self._voice = None

        # Start the background daemon worker
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="JARVIS-TTS-Worker",
            daemon=True,
        )
        self._worker_thread.start()
        logger.info("TTS Engine initialized with background worker thread.")

    def _init_engine(self) -> None:
        """Initializes the native Windows SAPI.SpVoice engine within the worker thread."""
        try:
            self._voice = comtypes.client.CreateObject("SAPI.SpVoice")
            self._voice.Volume = int(self.volume * 100)

            # Map words-per-minute (150-200) to SAPI Rate scale (-10 to +10)
            sapi_rate = max(-10, min(10, int((self.rate - 175) / 10)))
            self._voice.Rate = sapi_rate

            voices = self._voice.GetVoices()
            if voices and 0 <= self.voice_index < voices.Count:
                self._voice.Voice = voices.Item(self.voice_index)
                logger.info(f"TTS voice set to: {voices.Item(self.voice_index).GetDescription()}")
            else:
                logger.info("TTS voice set to system default.")
        except Exception:
            logger.exception("Failed to initialize Windows SAPI.SpVoice audio engine.")
            self._voice = None

    def _worker_loop(self) -> None:
        """Continuous background loop processing speech requests from the queue."""
        # Initialize COM on this background worker thread
        try:
            comtypes.CoInitialize()
        except Exception:
            pass

        try:
            self._init_engine()

            while self._is_running:
                try:
                    # Wait for next text item
                    text = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if text is None:
                    # Sentinel value indicating shutdown
                    self._queue.task_done()
                    break

                text = text.strip()
                if not text or not self._voice:
                    self._queue.task_done()
                    continue

                with self._lock:
                    self._is_speaking = True

                # Trigger speech start callback
                if self.on_start:
                    try:
                        self.on_start(text)
                    except Exception:
                        logger.exception("Error in TTS on_start callback.")

                try:
                    logger.info(f"Speaking aloud: '{text}'")
                    # Synchronous speak on this worker thread
                    self._voice.Speak(text)
                except Exception:
                    logger.exception(f"Error while speaking text: '{text}'")
                finally:
                    with self._lock:
                        self._is_speaking = False

                    # Trigger speech end callback
                    if self.on_end:
                        try:
                            self.on_end(text)
                        except Exception:
                            logger.exception("Error in TTS on_end callback.")

                    self._queue.task_done()
        finally:
            try:
                comtypes.CoUninitialize()
            except Exception:
                pass

    @staticmethod
    def _sanitize_for_speech(text: str) -> str:
        """
        Normalizes acronyms and formatting so the speech synthesizer pronounces them naturally.
        Replaces 'J.A.R.V.I.S.' and 'JARVIS' with 'Jarvis' to prevent spelling out individual letters.
        """
        if not text:
            return ""
        pattern = re.compile(r"(?:J\.A\.R\.V\.I\.S\.?|\bJARVIS\b)", re.IGNORECASE)
        return pattern.sub("Jarvis", text)

    def speak(self, text: str, block: bool = False) -> None:
        """
        Queues text to be spoken by J.A.R.V.I.S.

        :param text: The sentence or message to speak.
        :param block: If True, waits until speech completes before returning.
                      If False (default), returns immediately (ideal for UI).
        """
        if not text:
            return

        clean_text = self._sanitize_for_speech(text)
        logger.info(f"Queued TTS: '{clean_text}'")
        self._queue.put(clean_text)

        if block:
            self._queue.join()

    def stop(self) -> None:
        """Interrupts and stops ongoing speech immediately and clears the queue."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

        if self._voice:
            try:
                # SVSFPurgeBeforeSpeak = 2 (instantly halts ongoing speech)
                self._voice.Speak("", 2)
            except Exception:
                pass

        with self._lock:
            self._is_speaking = False

        logger.info("TTS speech stopped and queue cleared.")

    def set_rate(self, rate: int) -> None:
        """Adjusts the speaking speed (words per minute)."""
        self.rate = rate
        if self._voice:
            try:
                self._voice.Rate = max(-10, min(10, int((rate - 175) / 10)))
            except Exception:
                pass

    def set_volume(self, volume: float) -> None:
        """Adjusts volume level (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self._voice:
            try:
                self._voice.Volume = int(self.volume * 100)
            except Exception:
                pass

    def set_voice(self, voice_index: int) -> None:
        """Switches the voice by index."""
        self.voice_index = voice_index
        if self._voice:
            try:
                voices = self._voice.GetVoices()
                if voices and 0 <= voice_index < voices.Count:
                    self._voice.Voice = voices.Item(voice_index)
            except Exception:
                pass

    def get_available_voices(self) -> List[dict]:
        """Returns a list of metadata for all available system voices."""
        voices_list = []
        try:
            try:
                comtypes.CoInitialize()
            except Exception:
                pass

            temp_voice = comtypes.client.CreateObject("SAPI.SpVoice")
            voices = temp_voice.GetVoices()
            for i in range(voices.Count):
                item = voices.Item(i)
                voices_list.append({
                    "index": i,
                    "id": getattr(item, "Id", f"voice_{i}"),
                    "name": item.GetDescription(),
                    "languages": [],
                })
        except Exception:
            logger.exception("Failed to retrieve available system voices.")
        finally:
            try:
                comtypes.CoUninitialize()
            except Exception:
                pass
        return voices_list

    @property
    def is_speaking(self) -> bool:
        """Returns True if J.A.R.V.I.S. is currently speaking, False otherwise."""
        with self._lock:
            return self._is_speaking

    def shutdown(self) -> None:
        """Stops the worker thread and shuts down the engine cleanly."""
        self._is_running = False
        self._queue.put(None)  # Wake up thread to terminate
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        logger.info("TTS Engine shut down cleanly.")


# Global default instance ready for import across the project
tts = TTSEngine()
