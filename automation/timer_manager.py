"""
Productivity Timers, Reminders & Focus Sessions Module for J.A.R.V.I.S.
------------------------------------------------------------------------
Provides background, non-blocking countdown timers, timestamped reminders,
and Pomodoro focus sessions with voice notifications.
"""

from dataclasses import dataclass
import threading
import time
from typing import Dict, List, Optional, Tuple

from utils.logger import logger


@dataclass
class ActiveTimer:
    """Represents a live countdown timer or reminder."""
    timer_id: str
    label: str
    total_seconds: int
    start_time: float
    end_time: float
    is_reminder: bool = False
    message: Optional[str] = None
    cancelled: bool = False


class TimerManager:
    """Manages concurrent countdown timers, reminders, and focus sessions."""

    def __init__(self):
        self._timers: Dict[str, ActiveTimer] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _speak_alert(message: str) -> None:
        """Speaks an alert asynchronously via the TTS engine."""
        try:
            from speech.tts import tts_engine
            tts_engine.speak_async(message)
        except Exception as e:
            logger.warning(f"Could not speak timer alert via TTS: {e}")

    def set_timer(self, seconds: int, label: str = "timer") -> Tuple[bool, str]:
        """
        Starts a background countdown timer.
        :param seconds: Duration in seconds
        :param label: Optional name/label for the timer
        :return: (success: bool, spoken_response: str)
        """
        if seconds <= 0:
            return False, "Please specify a timer duration greater than zero, sir."

        now = time.time()
        timer_id = f"timer_{int(now)}"
        clean_label = label.strip() or "timer"

        timer_obj = ActiveTimer(
            timer_id=timer_id,
            label=clean_label,
            total_seconds=seconds,
            start_time=now,
            end_time=now + seconds,
        )

        with self._lock:
            self._timers[timer_id] = timer_obj

        def _worker():
            time.sleep(seconds)
            with self._lock:
                active = self._timers.get(timer_id)
                if not active or active.cancelled:
                    return
                del self._timers[timer_id]

            logger.info(f"Timer elapsed: '{clean_label}' ({seconds}s)")
            self._speak_alert(f"Time is up, sir! Your {clean_label} timer for {_format_duration(seconds)} has elapsed.")

        threading.Thread(target=_worker, name=f"JARVIS-Timer-{timer_id}", daemon=True).start()

        duration_str = _format_duration(seconds)
        speech = f"Timer set for {duration_str}, sir."
        logger.info(f"Started timer '{clean_label}' for {duration_str}")
        return True, speech

    def get_timer_status(self) -> Tuple[bool, str]:
        """
        Queries time remaining on the active timer.
        :return: (success: bool, spoken_response: str)
        """
        with self._lock:
            if not self._timers:
                return True, "There are currently no active timers running, sir."

            # Find the timer with the nearest expiration
            active_list = [t for t in self._timers.values() if not t.cancelled]
            if not active_list:
                return True, "There are currently no active timers running, sir."

            nearest = min(active_list, key=lambda t: t.end_time)

        remaining = max(0, int(nearest.end_time - time.time()))
        if remaining == 0:
            return True, f"Your {nearest.label} timer has just finished, sir."

        rem_str = _format_duration(remaining)
        return True, f"You have {rem_str} remaining on your {nearest.label}, sir."

    def cancel_timer(self) -> Tuple[bool, str]:
        """
        Cancels active countdown timers.
        :return: (success: bool, spoken_response: str)
        """
        with self._lock:
            if not self._timers:
                return True, "There are no active timers to cancel, sir."

            count = len(self._timers)
            for t in self._timers.values():
                t.cancelled = True
            self._timers.clear()

        logger.info(f"Cancelled {count} active timers.")
        return True, "Active timer cancelled, sir."

    def set_reminder(self, seconds: int, message: str) -> Tuple[bool, str]:
        """
        Schedules a voice reminder after specified seconds.
        :param seconds: Duration in seconds
        :param message: Reminder task text
        :return: (success: bool, spoken_response: str)
        """
        if seconds <= 0:
            return False, "Please specify a valid time for the reminder, sir."
        if not message.strip():
            return False, "Please specify what you would like to be reminded about, sir."

        clean_msg = message.strip()
        now = time.time()
        timer_id = f"remind_{int(now)}"

        timer_obj = ActiveTimer(
            timer_id=timer_id,
            label="reminder",
            total_seconds=seconds,
            start_time=now,
            end_time=now + seconds,
            is_reminder=True,
            message=clean_msg,
        )

        with self._lock:
            self._timers[timer_id] = timer_obj

        def _worker():
            time.sleep(seconds)
            with self._lock:
                active = self._timers.get(timer_id)
                if not active or active.cancelled:
                    return
                del self._timers[timer_id]

            logger.info(f"Reminder triggered: '{clean_msg}'")
            self._speak_alert(f"Sir, here is your reminder: {clean_msg}.")

        threading.Thread(target=_worker, name=f"JARVIS-Reminder-{timer_id}", daemon=True).start()

        duration_str = _format_duration(seconds)
        speech = f"I will remind you to {clean_msg} in {duration_str}, sir."
        logger.info(f"Scheduled reminder: '{clean_msg}' in {duration_str}")
        return True, speech

    def start_focus_session(self, duration_minutes: int = 25) -> Tuple[bool, str]:
        """
        Starts a Pomodoro focus interval.
        :param duration_minutes: Work block duration in minutes (default: 25)
        :return: (success: bool, spoken_response: str)
        """
        seconds = duration_minutes * 60
        now = time.time()
        timer_id = f"focus_{int(now)}"

        timer_obj = ActiveTimer(
            timer_id=timer_id,
            label="focus session",
            total_seconds=seconds,
            start_time=now,
            end_time=now + seconds,
        )

        with self._lock:
            self._timers[timer_id] = timer_obj

        def _worker():
            time.sleep(seconds)
            with self._lock:
                active = self._timers.get(timer_id)
                if not active or active.cancelled:
                    return
                del self._timers[timer_id]

            logger.info(f"Focus session complete: {duration_minutes}m")
            self._speak_alert("Focus session complete, sir! Time for a well-deserved 5-minute break.")

        threading.Thread(target=_worker, name=f"JARVIS-Focus-{timer_id}", daemon=True).start()

        speech = f"Starting a {duration_minutes}-minute focus session, sir. I will alert you when it is time for a break."
        logger.info(f"Started focus session ({duration_minutes}m)")
        return True, speech


def _format_duration(total_seconds: int) -> str:
    """Formats seconds into readable string (e.g. '10 minutes', '1 hour and 15 minutes')."""
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    if minutes > 0:
        parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} {'second' if seconds == 1 else 'seconds'}")

    return ", ".join(parts[:-1]) + ", and " + parts[-1] if len(parts) > 1 else parts[0]


# Global default instance
timer_manager = TimerManager()

