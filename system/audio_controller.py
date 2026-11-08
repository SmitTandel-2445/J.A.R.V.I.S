"""
System Audio Controller Module for J.A.R.V.I.S.
------------------------------------------------
Provides programmatic control over the Windows Master Audio Endpoint
using pycaw (Python Core Audio Windows Library).
Supports volume level query, volume adjustment, and mute/unmute toggles.
"""

import threading
from typing import Optional
import comtypes
from pycaw.pycaw import AudioUtilities

from utils.logger import logger


class AudioController:
    """Manages Windows master audio volume and mute states via pycaw."""

    def __init__(self):
        self._lock = threading.Lock()

    def _get_endpoint(self):
        """Helper to safely acquire the active speaker endpoint volume interface."""
        try:
            comtypes.CoInitialize()
        except Exception:
            pass

        device = AudioUtilities.GetSpeakers()
        if not device:
            raise RuntimeError("No audio output device found.")
        return device.EndpointVolume

    def get_volume(self) -> int:
        """
        Returns the current master volume level as an integer percentage (0 to 100).
        """
        with self._lock:
            try:
                endpoint = self._get_endpoint()
                scalar = endpoint.GetMasterVolumeLevelScalar()
                return int(round(scalar * 100))
            except Exception as e:
                logger.error(f"Failed to read master volume: {e}")
                return 50

    def set_volume(self, level: int) -> int:
        """
        Sets master volume to a specified percentage between 0 and 100.

        :param level: Desired volume percentage (0 - 100)
        :return: Actual volume percentage set
        """
        clamped = max(0, min(100, int(level)))
        with self._lock:
            try:
                endpoint = self._get_endpoint()
                scalar = clamped / 100.0
                endpoint.SetMasterVolumeLevelScalar(scalar, None)
                # If unmuting when volume is set
                if endpoint.GetMute():
                    endpoint.SetMute(0, None)
                logger.info(f"System volume set to {clamped}%.")
                return clamped
            except Exception as e:
                logger.error(f"Failed to set master volume to {level}%: {e}")
                return self.get_volume()

    def change_volume(self, delta: int) -> int:
        """
        Adjusts master volume relatively by a positive or negative delta.

        :param delta: Relative step (e.g., +10 or -10)
        :return: Resulting volume percentage
        """
        current = self.get_volume()
        target = current + delta
        return self.set_volume(target)

    def mute(self) -> bool:
        """Mutes the master audio output."""
        with self._lock:
            try:
                endpoint = self._get_endpoint()
                endpoint.SetMute(1, None)
                logger.info("System audio muted.")
                return True
            except Exception as e:
                logger.error(f"Failed to mute audio: {e}")
                return False

    def unmute(self) -> bool:
        """Unmutes the master audio output."""
        with self._lock:
            try:
                endpoint = self._get_endpoint()
                endpoint.SetMute(0, None)
                logger.info("System audio unmuted.")
                return True
            except Exception as e:
                logger.error(f"Failed to unmute audio: {e}")
                return False

    def is_muted(self) -> bool:
        """Checks if the master audio output is currently muted."""
        with self._lock:
            try:
                endpoint = self._get_endpoint()
                return bool(endpoint.GetMute())
            except Exception as e:
                logger.error(f"Failed to read mute state: {e}")
                return False

    def _get_mic_endpoint(self):
        """Helper to acquire the recording microphone volume interface."""
        try:
            comtypes.CoInitialize()
        except Exception:
            pass
        mic = AudioUtilities.GetMicrophone()
        if not mic:
            raise RuntimeError("No microphone recording device found.")
        from ctypes import cast, POINTER
        from pycaw.pycaw import IAudioEndpointVolume
        interface = mic.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    def mute_microphone(self) -> bool:
        """Mutes the default recording microphone."""
        with self._lock:
            try:
                mic_endpoint = self._get_mic_endpoint()
                mic_endpoint.SetMute(1, None)
                logger.info("Microphone hardware muted.")
                return True
            except Exception as e:
                logger.error(f"Failed to mute microphone: {e}")
                return False

    def unmute_microphone(self) -> bool:
        """Unmutes the default recording microphone."""
        with self._lock:
            try:
                mic_endpoint = self._get_mic_endpoint()
                mic_endpoint.SetMute(0, None)
                logger.info("Microphone hardware unmuted.")
                return True
            except Exception as e:
                logger.error(f"Failed to unmute microphone: {e}")
                return False

    def is_microphone_muted(self) -> bool:
        """Checks if the default recording microphone is muted."""
        with self._lock:
            try:
                mic_endpoint = self._get_mic_endpoint()
                return bool(mic_endpoint.GetMute())
            except Exception as e:
                logger.error(f"Failed to check microphone mute state: {e}")
                return False


# Global default instance
audio_controller = AudioController()

