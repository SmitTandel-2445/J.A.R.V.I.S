"""
Speech subsystem for J.A.R.V.I.S.
Provides Text-to-Speech (TTS), Speech-to-Text (STT), and audio utilities.
"""

from speech.tts import TTSEngine, tts
from speech.stt import SpeechRecognizer, stt

__all__ = ["TTSEngine", "tts", "SpeechRecognizer", "stt"]

