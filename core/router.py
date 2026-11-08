"""
Action Router Module for J.A.R.V.I.S.
-------------------------------------
Coordinates intent recognition, local deterministic execution, desktop automation,
and cloud AI routing using the Command Dispatcher pattern.
"""

from dataclasses import dataclass, field
import datetime
import threading
import time
from typing import Any, Callable, Dict, List, Optional

import psutil

from ai.gemini_client import GeminiBrain, brain as default_brain
from automation.app_launcher import AppLauncher, app_launcher as default_app_launcher
from automation.browser import BrowserController, browser_controller as default_browser
from automation.clipboard_controller import ClipboardController, clipboard_controller as default_clipboard
from automation.file_manager import FileManager, file_manager as default_file_mgr
from automation.media_controller import MediaController, media_controller as default_media
from automation.screenshot_controller import ScreenshotController, screenshot_controller as default_screenshot
from automation.shortcut_controller import ShortcutController, shortcut_controller as default_shortcut
from automation.spotify_controller import SpotifyController, spotify_controller as default_spotify
from automation.timer_manager import TimerManager, timer_manager as default_timer
from automation.window_controller import WindowController, window_controller as default_window
from core.context import ContextManager, context_manager as default_context
from nlp.intent_classifier import IntentClassifier, IntentResult, IntentType
from system.audio_controller import AudioController, audio_controller as default_audio
from system.brightness_controller import BrightnessController, brightness_controller as default_brightness
from system.display_controller import DisplayController, display_controller as default_display
from system.network_controller import NetworkController, network_controller as default_network
from system.power_controller import PowerController, power_controller as default_power
from system.task_manager import TaskManager, task_manager as default_task_mgr
from utils.logger import logger


@dataclass
class ActionResult:
    """Standardized result returned by the Action Router."""
    intent: IntentType
    spoken_response: str
    log_message: str
    success: bool = True
    data: Dict[str, Any] = field(default_factory=dict)


class ActionRouter:
    """
    Central dispatcher routing user queries to immediate local actions
    (Desktop Apps, Volume, Power, Time, Telemetry, Web) or to the Gemini AI Brain.
    """

    def __init__(
        self,
        brain: Optional[GeminiBrain] = None,
        classifier: Optional[IntentClassifier] = None,
        app_launcher: Optional[AppLauncher] = None,
        audio_controller: Optional[AudioController] = None,
        browser_controller: Optional[BrowserController] = None,
        power_controller: Optional[PowerController] = None,
        media_controller: Optional[MediaController] = None,
        window_controller: Optional[WindowController] = None,
        screenshot_controller: Optional[ScreenshotController] = None,
        file_manager: Optional[FileManager] = None,
        brightness_controller: Optional[BrightnessController] = None,
        spotify_controller: Optional[SpotifyController] = None,
        clipboard_controller: Optional[ClipboardController] = None,
        network_controller: Optional[NetworkController] = None,
        task_manager: Optional[TaskManager] = None,
        timer_manager: Optional[TimerManager] = None,
        display_controller: Optional[DisplayController] = None,
        shortcut_controller: Optional[ShortcutController] = None,
        context_manager: Optional[ContextManager] = None,
    ):
        """
        Initialize the Action Router.
        """
        self.brain = brain or default_brain
        self.classifier = classifier or IntentClassifier()
        self.app_launcher = app_launcher or default_app_launcher
        self.audio_controller = audio_controller or default_audio
        self.browser_controller = browser_controller or default_browser
        self.power_controller = power_controller or default_power
        self.media_controller = media_controller or default_media
        self.window_controller = window_controller or default_window
        self.screenshot_controller = screenshot_controller or default_screenshot
        self.file_manager = file_manager or default_file_mgr
        self.brightness_controller = brightness_controller or default_brightness
        self.spotify_controller = spotify_controller or default_spotify
        self.clipboard_controller = clipboard_controller or default_clipboard
        self.network_controller = network_controller or default_network
        self.task_manager = task_manager or default_task_mgr
        self.timer_manager = timer_manager or default_timer
        self.display_controller = display_controller or default_display
        self.shortcut_controller = shortcut_controller or default_shortcut
        self.context_manager = context_manager or default_context

        # Dictionary mapping IntentType to internal handler methods
        self._handlers = {
            IntentType.TIME_DATE: self._handle_time_date,
            IntentType.SYSTEM_TELEMETRY: self._handle_system_telemetry,
            IntentType.SYSTEM_POWER: self._handle_system_power,
            IntentType.WEB_SEARCH: self._handle_web_search,
            IntentType.YOUTUBE_PLAY: self._handle_youtube_play,
            IntentType.SPOTIFY_PLAY: self._handle_spotify_play,
            IntentType.PLAY_MEDIA: self._handle_play_media,
            IntentType.OPEN_APP: self._handle_open_app,
            IntentType.CLOSE_APP: self._handle_close_app,
            IntentType.SYSTEM_VOLUME: self._handle_system_volume,
            IntentType.BROWSER_TAB: self._handle_browser_tab,
            IntentType.MEDIA_CONTROL: self._handle_media_control,
            IntentType.WINDOW_CONTROL: self._handle_window_control,
            IntentType.SCREENSHOT: self._handle_screenshot,
            IntentType.FILE_FOLDER: self._handle_file_folder,
            IntentType.SYSTEM_BRIGHTNESS: self._handle_system_brightness,
            IntentType.GO_OFFLINE: self._handle_go_offline,
            IntentType.CLIPBOARD: self._handle_clipboard,
            IntentType.NETWORK: self._handle_network,
            IntentType.TASK_MANAGER: self._handle_task_manager,
            IntentType.TIMER: self._handle_timer,
            IntentType.DISPLAY: self._handle_display,
            IntentType.SHORTCUT: self._handle_shortcut,
        }

    @staticmethod
    def _combine_spoken_responses(responses: List[str]) -> str:
        """
        Synthesizes multiple individual spoken replies into a natural, unified response.
        Example: ['Opening YouTube, sir.', 'Opening Spotify, sir.', 'Playing unstoppable on Spotify, sir.']
                 -> 'Opening YouTube, opening Spotify, and playing unstoppable on Spotify, sir.'
        """
        if not responses:
            return "Done, sir."
        if len(responses) == 1:
            return responses[0]

        clean_parts: List[str] = []
        for r in responses:
            c = r.strip()
            for suffix in [", sir.", ", sir", "."]:
                if c.lower().endswith(suffix.lower()):
                    c = c[:-len(suffix)].strip()
            if c:
                clean_parts.append(c)

        if not clean_parts:
            return "Done, sir."
        if len(clean_parts) == 1:
            return f"{clean_parts[0]}, sir."
        if len(clean_parts) == 2:
            return f"{clean_parts[0]}, and {clean_parts[1].lower()}, sir."

        lead = ", ".join([clean_parts[0]] + [p.lower() for p in clean_parts[1:-1]])
        return f"{lead}, and {clean_parts[-1].lower()}, sir."

    def _execute_single_intent(self, intent_result: IntentResult, query_text: str) -> ActionResult:
        """Executes a single classified intent."""
        if intent_result.intent in self._handlers:
            handler = self._handlers[intent_result.intent]
            try:
                res = handler(intent_result)
                if res.spoken_response and intent_result.intent != IntentType.CLIPBOARD:
                    self.context_manager.set("last_spoken_response", res.spoken_response)
                return res
            except Exception as e:
                logger.exception(f"Error executing local handler for intent {intent_result.intent}: {e}")
                pass

        # Default: Route to Gemini AI Brain
        ai_reply = self.brain.ask(intent_result.parameters.get("query", query_text))
        self.context_manager.set("last_ai_reply", ai_reply)
        self.context_manager.set("last_spoken_response", ai_reply)
        return ActionResult(
            intent=IntentType.CONVERSATION_AI,
            spoken_response=ai_reply,
            log_message=f"JARVIS: {ai_reply}",
            success=True,
        )

    def route(
        self,
        text: str,
        on_step: Optional[Callable[[ActionResult, int, int], None]] = None,
    ) -> ActionResult:
        """
        Synchronously classifies and executes commands (supporting single and compound commands).

        :param text: Spoken or typed user input
        :param on_step: Optional callback triggered after each step in a compound command: on_step(res, step_index, total_steps)
        :return: ActionResult containing the response and execution status
        """
        if not text or not text.strip():
            return ActionResult(
                intent=IntentType.CONVERSATION_AI,
                spoken_response="",
                log_message="",
                success=False,
            )

        intents = self.classifier.classify_multi(text)

        # 1. Single command: execute directly
        if len(intents) == 1:
            return self._execute_single_intent(intents[0], text)

        # 2. Compound / Multi-command execution: execute sequentially one by one!
        logger.info(f"Executing compound query ({len(intents)} actions): '{text}'")
        results: List[ActionResult] = []
        spoken_parts: List[str] = []
        all_success = True

        for idx, item in enumerate(intents):
            logger.info(f"Compound step {idx + 1}/{len(intents)} ({item.intent.value}): '{item.cleaned_text}'")
            step_res = self._execute_single_intent(item, item.cleaned_text)
            results.append(step_res)
            if not step_res.success:
                all_success = False
            if step_res.spoken_response:
                spoken_parts.append(step_res.spoken_response)

            if on_step:
                try:
                    on_step(step_res, idx + 1, len(intents))
                except Exception as e:
                    logger.warning(f"Error in on_step callback: {e}")

            # Brief pause between sequential OS actions so windows/tabs open smoothly
            if idx < len(intents) - 1:
                time.sleep(1.0)

        # Combine responses into a unified result
        combined_speech = self._combine_spoken_responses(spoken_parts)
        combined_log = "\n".join([r.log_message for r in results if r.log_message])

        # If any step was GO_OFFLINE, mark the final intent as GO_OFFLINE so app shuts down
        final_intent = IntentType.GO_OFFLINE if any(r.intent == IntentType.GO_OFFLINE for r in results) else results[-1].intent

        return ActionResult(
            intent=final_intent,
            spoken_response=combined_speech,
            log_message=combined_log,
            success=all_success,
            data={"compound": True, "count": len(results), "steps": [r.data for r in results]},
        )

    def route_async(
        self,
        text: str,
        on_result: Callable[[ActionResult], None],
        on_error: Optional[Callable[[str], None]] = None,
        on_step: Optional[Callable[[ActionResult, int, int], None]] = None,
    ) -> None:
        """
        Asynchronous non-blocking wrapper for route().
        Executes on a background worker thread so the Arc Reactor animation
        and UI event loop remain completely smooth.
        """
        def _worker():
            try:
                res = self.route(text, on_step=on_step)
                if on_result:
                    on_result(res)
            except Exception as e:
                logger.exception(f"Error in ActionRouter worker for query: '{text}'")
                if on_error:
                    on_error(str(e))
                elif on_result:
                    fallback = ActionResult(
                        intent=IntentType.CONVERSATION_AI,
                        spoken_response="I encountered an internal error processing your command, sir.",
                        log_message=f"ROUTER ERROR: {e}",
                        success=False,
                    )
                    on_result(fallback)

        thread = threading.Thread(
            target=_worker,
            name="JARVIS-ActionRouter-Worker",
            daemon=True,
        )
        thread.start()

    # -------------------------------------------------------------------------
    # Local Intent Handlers (Phase 5 Desktop Automation & System Control)
    # -------------------------------------------------------------------------

    def _handle_time_date(self, item: IntentResult) -> ActionResult:
        """Handles local time and date queries with zero API latency."""
        now = datetime.datetime.now()
        query_type = item.parameters.get("query_type", "time")

        if query_type == "time":
            time_str = now.strftime("%I:%M %p").lstrip("0")
            speech = f"It is currently {time_str}, sir."
        else:
            date_str = now.strftime("%A, %B %d, %Y")
            speech = f"Today is {date_str}, sir."

        return ActionResult(
            intent=IntentType.TIME_DATE,
            spoken_response=speech,
            log_message=f"JARVIS: {speech}",
            data={"timestamp": now.isoformat()},
        )

    def _handle_system_telemetry(self, item: IntentResult) -> ActionResult:
        """Reads live system telemetry metrics or battery diagnostics."""
        cleaned = item.cleaned_text.lower()
        if "battery" in cleaned:
            speech = self.power_controller.get_battery_report()
            return ActionResult(
                intent=IntentType.SYSTEM_TELEMETRY,
                spoken_response=speech,
                log_message=f"JARVIS: {speech}",
            )

        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()
            battery_text = f"battery is at {int(battery.percent)}%" if battery else "running on AC power"

            speech = f"All systems operational, sir. CPU load is {int(cpu)}%, memory usage is {int(mem)}%, and {battery_text}."
        except Exception:
            speech = "Core telemetry sensors are reporting nominal status, sir."

        return ActionResult(
            intent=IntentType.SYSTEM_TELEMETRY,
            spoken_response=speech,
            log_message=f"JARVIS: {speech}",
        )

    def _handle_system_power(self, item: IntentResult) -> ActionResult:
        """Handles system workstation locking and sleep states."""
        action = item.parameters.get("action", "")
        if action == "lock":
            success, speech = self.power_controller.lock_workstation()
        elif action == "sleep":
            success, speech = self.power_controller.sleep()
        else:
            success, speech = False, "Unrecognized system power command, sir."

        return ActionResult(
            intent=IntentType.SYSTEM_POWER,
            spoken_response=speech,
            log_message=f"JARVIS: [POWER] {speech}",
            success=success,
            data={"action": action},
        )

    def _handle_go_offline(self, item: IntentResult) -> ActionResult:
        """Handles voice commands to power down listener and transition offline."""
        speech = "Going offline, sir. Have a wonderful day."
        return ActionResult(
            intent=IntentType.GO_OFFLINE,
            spoken_response=speech,
            log_message=f"JARVIS: {speech}",
            success=True,
            data={"action": "offline"},
        )

    def _handle_web_search(self, item: IntentResult) -> ActionResult:
        """
        Executes web search. If a YouTube or Spotify tab/window is currently active,
        routes the search directly inside that app. Otherwise defaults to Google.
        """
        query = item.parameters.get("query", "")

        # 1. If YouTube tab is active, search specifically on YouTube!
        if self.context_manager.is_youtube_active():
            logger.info(f"Active context is YouTube. Searching '{query}' on YouTube.")
            success, speech = self.browser_controller.search_youtube(query)
            return ActionResult(
                intent=IntentType.YOUTUBE_PLAY,
                spoken_response=speech,
                log_message=f"JARVIS: [YOUTUBE] {speech}",
                success=success,
                data={"query": query},
            )

        # 2. If Spotify window is active, search specifically in Spotify!
        if self.context_manager.is_spotify_active():
            logger.info(f"Active context is Spotify. Searching & playing '{query}' in Spotify.")
            success, speech = self.spotify_controller.play_song(query)
            return ActionResult(
                intent=IntentType.SPOTIFY_PLAY,
                spoken_response=speech,
                log_message=f"JARVIS: [SPOTIFY] {speech}",
                success=success,
                data={"query": query},
            )

        # 3. Otherwise: Normal Google search in active browser tab!
        success, speech = self.browser_controller.search_google(query)
        return ActionResult(
            intent=IntentType.WEB_SEARCH,
            spoken_response=speech,
            log_message=f"JARVIS: {speech} -> {query}",
            success=success,
            data={"query": query},
        )

    def _handle_youtube_play(self, item: IntentResult) -> ActionResult:
        """Explicit YouTube play ('play X on youtube')."""
        query = item.parameters.get("query", "")
        self.context_manager.set("app", "youtube")
        success, speech = self.browser_controller.play_youtube(query)
        return ActionResult(
            intent=IntentType.YOUTUBE_PLAY,
            spoken_response=speech,
            log_message=f"JARVIS: {speech} -> {query}",
            success=success,
            data={"query": query},
        )

    def _handle_spotify_play(self, item: IntentResult) -> ActionResult:
        """Explicit Spotify play ('play X on spotify')."""
        query = item.parameters.get("query", "")
        self.context_manager.set("app", "spotify")
        success, speech = self.spotify_controller.play_song(query)
        return ActionResult(
            intent=IntentType.SPOTIFY_PLAY,
            spoken_response=speech,
            log_message=f"JARVIS: [SPOTIFY] {speech}",
            success=success,
            data={"query": query},
        )

    def _handle_play_media(self, item: IntentResult) -> ActionResult:
        """
        Context-aware media playback for 'play [query]' (e.g. 'play luna bala').
        - If Spotify is open/active: plays on Spotify.
        - If YouTube is open/active: plays on YouTube.
        - Otherwise: defaults to YouTube without breaking or conflicting with Google/LLM.
        """
        query = item.parameters.get("query", "")
        if not query:
            return ActionResult(
                intent=IntentType.PLAY_MEDIA,
                spoken_response="What would you like me to play, sir?",
                log_message="JARVIS: What would you like me to play, sir?",
                success=False,
            )

        if self.context_manager.is_spotify_active():
            logger.info(f"Context-aware play: routing '{query}' to active Spotify.")
            return self._handle_spotify_play(item)

        if self.context_manager.is_youtube_active():
            logger.info(f"Context-aware play: routing '{query}' to active YouTube.")
            return self._handle_youtube_play(item)

        # Default fallback: YouTube
        logger.info(f"Context-aware play: defaulting '{query}' to YouTube.")
        return self._handle_youtube_play(item)

    def _handle_open_app(self, item: IntentResult) -> ActionResult:
        """Launches a desktop application asynchronously."""
        app_name = item.parameters.get("app_name", "")
        success, speech = self.app_launcher.launch(app_name)
        return ActionResult(
            intent=IntentType.OPEN_APP,
            spoken_response=speech,
            log_message=f"JARVIS: [APP] {speech}",
            success=success,
            data={"app_name": app_name},
        )

    def _handle_close_app(self, item: IntentResult) -> ActionResult:
        """Closes running instances of an application gracefully or terminates process."""
        app_name = item.parameters.get("app_name", "")

        # 1. First attempt graceful window close via window_controller
        win_success, win_speech = self.window_controller.close(app_name)
        if win_success:
            return ActionResult(
                intent=IntentType.CLOSE_APP,
                spoken_response=win_speech,
                log_message=f"JARVIS: [APP] {win_speech}",
                success=True,
                data={"app_name": app_name, "method": "window_close"},
            )

        # 2. Fall back to process termination (psutil) if window close was not applicable
        success, speech = self.app_launcher.close(app_name)
        return ActionResult(
            intent=IntentType.CLOSE_APP,
            spoken_response=speech,
            log_message=f"JARVIS: [APP] {speech}",
            success=success,
            data={"app_name": app_name, "method": "process_terminate"},
        )

    def _handle_system_volume(self, item: IntentResult) -> ActionResult:
        """Controls Windows master volume and mute states via pycaw."""
        action = item.parameters.get("action", "")
        if action == "mute":
            self.audio_controller.mute()
            speech = "Audio muted, sir."
        elif action == "unmute":
            self.audio_controller.unmute()
            speech = "Audio unmuted, sir."
        elif action == "set":
            level = item.parameters.get("level", 50)
            actual = self.audio_controller.set_volume(level)
            speech = f"System volume set to {actual} percent, sir."
        elif action == "up":
            step = item.parameters.get("step", 10)
            actual = self.audio_controller.change_volume(+step)
            speech = f"Volume increased to {actual} percent, sir."
        elif action == "down":
            step = item.parameters.get("step", 10)
            actual = self.audio_controller.change_volume(-step)
            speech = f"Volume decreased to {actual} percent, sir."
        else:
            speech = "Could not adjust system volume, sir."

        return ActionResult(
            intent=IntentType.SYSTEM_VOLUME,
            spoken_response=speech,
            log_message=f"JARVIS: [VOLUME] {speech}",
            data=item.parameters,
        )

    def _handle_browser_tab(self, item: IntentResult) -> ActionResult:
        """Executes browser tab shortcut controls, page navigation, and text search."""
        action = item.parameters.get("action", "")

        if action == "find":
            query = item.parameters.get("query", "")
            success, speech = self.browser_controller.find_in_page(query)
            return ActionResult(
                intent=IntentType.BROWSER_TAB,
                spoken_response=speech,
                log_message=f"JARVIS: [BROWSER] {speech}",
                success=success,
                data={"action": "find", "query": query},
            )

        elif action == "navigate":
            url = item.parameters.get("url", "")
            success, speech = self.browser_controller.navigate_url(url)
            return ActionResult(
                intent=IntentType.BROWSER_TAB,
                spoken_response=speech,
                log_message=f"JARVIS: [BROWSER] {speech}",
                success=success,
                data={"action": "navigate", "url": url},
            )

        success, speech = self.browser_controller.execute_tab_command(action)
        return ActionResult(
            intent=IntentType.BROWSER_TAB,
            spoken_response=speech,
            log_message=f"JARVIS: [BROWSER] {speech}",
            success=success,
            data={"action": action},
        )

    def _handle_media_control(self, item: IntentResult) -> ActionResult:
        """Executes global multimedia playback controls."""
        action = item.parameters.get("action", "")
        if action == "play_pause":
            success, speech = self.media_controller.play_pause()
        elif action == "next":
            success, speech = self.media_controller.next_track()
        elif action == "previous":
            success, speech = self.media_controller.previous_track()
        elif action == "stop":
            success, speech = self.media_controller.stop()
        else:
            success, speech = False, "Unrecognized media command, sir."

        return ActionResult(
            intent=IntentType.MEDIA_CONTROL,
            spoken_response=speech,
            log_message=f"JARVIS: [MEDIA] {speech}",
            success=success,
            data={"action": action},
        )

    def _handle_window_control(self, item: IntentResult) -> ActionResult:
        """Executes desktop window management actions."""
        action = item.parameters.get("action", "")
        app_name = item.parameters.get("app_name")

        if action == "minimize":
            success, speech = self.window_controller.minimize(app_name)
        elif action == "maximize":
            success, speech = self.window_controller.maximize(app_name)
        elif action == "restore":
            success, speech = self.window_controller.restore(app_name)
        elif action == "close":
            success, speech = self.window_controller.close(app_name)
        elif action == "switch":
            success, speech = self.window_controller.switch_window()
        elif action == "desktop":
            success, speech = self.window_controller.show_desktop()
        elif action == "snap_left":
            success, speech = self.window_controller.snap_left(app_name)
        elif action == "snap_right":
            success, speech = self.window_controller.snap_right(app_name)
        else:
            success, speech = False, "Unrecognized window command, sir."

        return ActionResult(
            intent=IntentType.WINDOW_CONTROL,
            spoken_response=speech,
            log_message=f"JARVIS: [WINDOW] {speech}",
            success=success,
            data={"action": action, "app_name": app_name},
        )

    def _handle_screenshot(self, item: IntentResult) -> ActionResult:
        """Captures a screenshot and saves to Pictures folder."""
        success, speech, path = self.screenshot_controller.capture()
        return ActionResult(
            intent=IntentType.SCREENSHOT,
            spoken_response=speech,
            log_message=f"JARVIS: [SCREENSHOT] {speech} -> {path}",
            success=success,
            data={"path": path},
        )

    def _handle_file_folder(self, item: IntentResult) -> ActionResult:
        """Executes file, directory navigation, and recycle bin cleanup."""
        action = item.parameters.get("action", "")
        if action == "open":
            folder = item.parameters.get("folder", "")
            success, speech = self.file_manager.open_folder(folder)
        elif action == "create":
            name = item.parameters.get("name", "")
            success, speech = self.file_manager.create_folder(name)
        elif action == "empty_recycle_bin":
            success, speech = self.file_manager.empty_recycle_bin()
        elif action == "latest_download":
            success, speech, path = self.file_manager.open_latest_download()
            return ActionResult(
                intent=IntentType.FILE_FOLDER,
                spoken_response=speech,
                log_message=f"JARVIS: [FILE] {speech}",
                success=success,
                data={"action": "latest_download", "path": path},
            )
        else:
            success, speech = False, "Unrecognized folder command, sir."

        return ActionResult(
            intent=IntentType.FILE_FOLDER,
            spoken_response=speech,
            log_message=f"JARVIS: [FILE] {speech}",
            success=success,
            data=item.parameters,
        )

    def _handle_system_brightness(self, item: IntentResult) -> ActionResult:
        """Controls display screen brightness via screen_brightness_control."""
        action = item.parameters.get("action", "")
        if action == "set":
            level = item.parameters.get("level", 75)
            success, _, speech = self.brightness_controller.set_brightness(level)
        elif action == "up":
            step = item.parameters.get("step", 10)
            success, _, speech = self.brightness_controller.change_brightness(+step)
        elif action == "down":
            step = item.parameters.get("step", 10)
            success, _, speech = self.brightness_controller.change_brightness(-step)
        else:
            success, speech = False, "Could not adjust screen brightness, sir."

        return ActionResult(
            intent=IntentType.SYSTEM_BRIGHTNESS,
            spoken_response=speech,
            log_message=f"JARVIS: [BRIGHTNESS] {speech}",
            success=success,
            data=item.parameters,
        )

    def _handle_clipboard(self, item: IntentResult) -> ActionResult:
        """Executes voice-activated clipboard and text automation."""
        action = item.parameters.get("action", "")

        if action == "read":
            success, speech, raw_text = self.clipboard_controller.read()
            return ActionResult(
                intent=IntentType.CLIPBOARD,
                spoken_response=speech,
                log_message=f"JARVIS: [CLIPBOARD] {speech}",
                success=success,
                data={"action": "read", "text": raw_text},
            )

        elif action == "copy_last":
            last_text = self.context_manager.get("last_ai_reply") or self.context_manager.get("last_spoken_response")
            if not last_text:
                return ActionResult(
                    intent=IntentType.CLIPBOARD,
                    spoken_response="I don't have any recent response to copy, sir.",
                    log_message="JARVIS: [CLIPBOARD] No recent response to copy.",
                    success=False,
                    data={"action": "copy_last"},
                )
            success, speech = self.clipboard_controller.copy(last_text)
            return ActionResult(
                intent=IntentType.CLIPBOARD,
                spoken_response=speech,
                log_message="JARVIS: [CLIPBOARD] Copied last response to clipboard.",
                success=success,
                data={"action": "copy_last", "text": last_text},
            )

        elif action == "copy":
            text_to_copy = item.parameters.get("text", "")
            success, speech = self.clipboard_controller.copy(text_to_copy)
            return ActionResult(
                intent=IntentType.CLIPBOARD,
                spoken_response=speech,
                log_message=f"JARVIS: [CLIPBOARD] {speech} -> '{text_to_copy}'",
                success=success,
                data={"action": "copy", "text": text_to_copy},
            )

        elif action == "clear":
            success, speech = self.clipboard_controller.clear()
            return ActionResult(
                intent=IntentType.CLIPBOARD,
                spoken_response=speech,
                log_message=f"JARVIS: [CLIPBOARD] {speech}",
                success=success,
                data={"action": "clear"},
            )

        elif action == "type":
            text_to_type = item.parameters.get("text", "")
            success, speech = self.clipboard_controller.type_text(text_to_type)
            return ActionResult(
                intent=IntentType.CLIPBOARD,
                spoken_response=speech,
                log_message=f"JARVIS: [TYPE] {speech} -> '{text_to_type}'",
                success=success,
                data={"action": "type", "text": text_to_type},
            )

        return ActionResult(
            intent=IntentType.CLIPBOARD,
            spoken_response="Unrecognized clipboard action, sir.",
            log_message="JARVIS: [CLIPBOARD] Unrecognized action.",
            success=False,
            data=item.parameters,
        )

    def _handle_network(self, item: IntentResult) -> ActionResult:
        """Executes network diagnostics, Wi-Fi status queries, and IP lookups."""
        action = item.parameters.get("action", "")

        if action == "wifi":
            success, speech, data = self.network_controller.check_wifi()
            return ActionResult(
                intent=IntentType.NETWORK,
                spoken_response=speech,
                log_message=f"JARVIS: [NETWORK] {speech}",
                success=success,
                data=data,
            )

        elif action == "internet":
            success, speech, data = self.network_controller.test_internet()
            return ActionResult(
                intent=IntentType.NETWORK,
                spoken_response=speech,
                log_message=f"JARVIS: [NETWORK] {speech}",
                success=success,
                data=data,
            )

        elif action == "ip":
            scope = item.parameters.get("scope", "all")
            success, speech, data = self.network_controller.get_ip_address(scope=scope)
            return ActionResult(
                intent=IntentType.NETWORK,
                spoken_response=speech,
                log_message=f"JARVIS: [NETWORK] {speech}",
                success=success,
                data=data,
            )

        elif action == "diagnostics":
            success, speech, data = self.network_controller.get_diagnostics()
            return ActionResult(
                intent=IntentType.NETWORK,
                spoken_response=speech,
                log_message=f"JARVIS: [NETWORK] {speech}",
                success=success,
                data=data,
            )

        elif action == "flush_dns":
            success, speech = self.network_controller.flush_dns()
            return ActionResult(
                intent=IntentType.NETWORK,
                spoken_response=speech,
                log_message=f"JARVIS: [NETWORK] {speech}",
                success=success,
                data={"action": "flush_dns"},
            )

        elif action == "disconnect_wifi":
            success, speech = self.network_controller.disconnect_wifi()
            return ActionResult(
                intent=IntentType.NETWORK,
                spoken_response=speech,
                log_message=f"JARVIS: [NETWORK] {speech}",
                success=success,
                data={"action": "disconnect_wifi"},
            )

        elif action == "connect_wifi":
            success, speech = self.network_controller.connect_wifi()
            return ActionResult(
                intent=IntentType.NETWORK,
                spoken_response=speech,
                log_message=f"JARVIS: [NETWORK] {speech}",
                success=success,
                data={"action": "connect_wifi"},
            )

        return ActionResult(
            intent=IntentType.NETWORK,
            spoken_response="Unrecognized network action, sir.",
            log_message="JARVIS: [NETWORK] Unrecognized action.",
            success=False,
            data=item.parameters,
        )

    def _handle_task_manager(self, item: IntentResult) -> ActionResult:
        """Executes process monitoring, resource bottlenecks, and task manager commands."""
        action = item.parameters.get("action", "")

        if action == "top_cpu":
            success, speech, data = self.task_manager.get_top_processes(sort_by="cpu")
            return ActionResult(
                intent=IntentType.TASK_MANAGER,
                spoken_response=speech,
                log_message=f"JARVIS: [TASK_MGR] {speech}",
                success=success,
                data={"top_cpu": data},
            )

        elif action == "top_memory":
            success, speech, data = self.task_manager.get_top_processes(sort_by="memory")
            return ActionResult(
                intent=IntentType.TASK_MANAGER,
                spoken_response=speech,
                log_message=f"JARVIS: [TASK_MGR] {speech}",
                success=success,
                data={"top_memory": data},
            )

        elif action == "process_info":
            app_name = item.parameters.get("app_name", "")
            success, speech, data = self.task_manager.get_process_info(app_name)
            return ActionResult(
                intent=IntentType.TASK_MANAGER,
                spoken_response=speech,
                log_message=f"JARVIS: [TASK_MGR] {speech}",
                success=success,
                data=data,
            )

        elif action == "disk_space":
            drive = item.parameters.get("drive", "C")
            success, speech, data = self.task_manager.get_disk_space(drive)
            return ActionResult(
                intent=IntentType.TASK_MANAGER,
                spoken_response=speech,
                log_message=f"JARVIS: [TASK_MGR] {speech}",
                success=success,
                data=data,
            )

        elif action == "memory_breakdown":
            success, speech, data = self.task_manager.get_memory_breakdown()
            return ActionResult(
                intent=IntentType.TASK_MANAGER,
                spoken_response=speech,
                log_message=f"JARVIS: [TASK_MGR] {speech}",
                success=success,
                data=data,
            )

        elif action == "check_frozen":
            success, speech, hung_list = self.task_manager.check_unresponsive_processes()
            return ActionResult(
                intent=IntentType.TASK_MANAGER,
                spoken_response=speech,
                log_message=f"JARVIS: [TASK_MGR] {speech}",
                success=success,
                data={"hung_apps": hung_list},
            )

        elif action == "end_process":
            app_name = item.parameters.get("app_name", "")
            success, speech = self.task_manager.end_process(app_name)
            return ActionResult(
                intent=IntentType.TASK_MANAGER,
                spoken_response=speech,
                log_message=f"JARVIS: [TASK_MGR] {speech}",
                success=success,
                data={"app_name": app_name},
            )

        elif action == "uptime":
            success, speech, data = self.task_manager.get_system_uptime()
            return ActionResult(
                intent=IntentType.TASK_MANAGER,
                spoken_response=speech,
                log_message=f"JARVIS: [TASK_MGR] {speech}",
                success=success,
                data=data,
            )

        return ActionResult(
            intent=IntentType.TASK_MANAGER,
            spoken_response="Unrecognized task manager action, sir.",
            log_message="JARVIS: [TASK_MGR] Unrecognized action.",
            success=False,
            data=item.parameters,
        )

    def _handle_timer(self, item: IntentResult) -> ActionResult:
        """Executes productivity countdown timers, voice reminders, and focus sessions."""
        action = item.parameters.get("action", "")

        if action == "set_timer":
            seconds = item.parameters.get("seconds", 60)
            label = item.parameters.get("label", "timer")
            success, speech = self.timer_manager.set_timer(seconds, label)
            return ActionResult(
                intent=IntentType.TIMER,
                spoken_response=speech,
                log_message=f"JARVIS: [TIMER] {speech}",
                success=success,
                data={"action": "set_timer", "seconds": seconds, "label": label},
            )

        elif action == "status":
            success, speech = self.timer_manager.get_timer_status()
            return ActionResult(
                intent=IntentType.TIMER,
                spoken_response=speech,
                log_message=f"JARVIS: [TIMER] {speech}",
                success=success,
                data={"action": "status"},
            )

        elif action == "cancel":
            success, speech = self.timer_manager.cancel_timer()
            return ActionResult(
                intent=IntentType.TIMER,
                spoken_response=speech,
                log_message=f"JARVIS: [TIMER] {speech}",
                success=success,
                data={"action": "cancel"},
            )

        elif action == "set_reminder":
            seconds = item.parameters.get("seconds", 60)
            message = item.parameters.get("message", "Reminder")
            success, speech = self.timer_manager.set_reminder(seconds, message)
            return ActionResult(
                intent=IntentType.TIMER,
                spoken_response=speech,
                log_message=f"JARVIS: [TIMER] {speech}",
                success=success,
                data={"action": "set_reminder", "seconds": seconds, "message": message},
            )

        elif action == "focus_session":
            minutes = item.parameters.get("minutes", 25)
            success, speech = self.timer_manager.start_focus_session(minutes)
            return ActionResult(
                intent=IntentType.TIMER,
                spoken_response=speech,
                log_message=f"JARVIS: [TIMER] {speech}",
                success=success,
                data={"action": "focus_session", "minutes": minutes},
            )

        return ActionResult(
            intent=IntentType.TIMER,
            spoken_response="Unrecognized timer command, sir.",
            log_message="JARVIS: [TIMER] Unrecognized action.",
            success=False,
            data=item.parameters,
        )

    def _handle_display(self, item: IntentResult) -> ActionResult:
        """Executes multi-monitor window movement and Windows theme controls."""
        action = item.parameters.get("action", "")

        if action == "move_monitor":
            direction = item.parameters.get("direction", "right")
            success, speech = self.display_controller.move_window_to_monitor(direction)
            return ActionResult(
                intent=IntentType.DISPLAY,
                spoken_response=speech,
                log_message=f"JARVIS: [DISPLAY] {speech}",
                success=success,
                data={"action": "move_monitor", "direction": direction},
            )

        elif action == "theme":
            mode = item.parameters.get("mode", "dark")
            success, speech = self.display_controller.set_theme(mode)
            return ActionResult(
                intent=IntentType.DISPLAY,
                spoken_response=speech,
                log_message=f"JARVIS: [DISPLAY] {speech}",
                success=success,
                data={"action": "theme", "mode": mode},
            )

        elif action == "night_light":
            success, speech = self.display_controller.toggle_night_light()
            return ActionResult(
                intent=IntentType.DISPLAY,
                spoken_response=speech,
                log_message=f"JARVIS: [DISPLAY] {speech}",
                success=success,
                data={"action": "night_light"},
            )

        return ActionResult(
            intent=IntentType.DISPLAY,
            spoken_response="Unrecognized display command, sir.",
            log_message="JARVIS: [DISPLAY] Unrecognized action.",
            success=False,
            data=item.parameters,
        )

    def _handle_shortcut(self, item: IntentResult) -> ActionResult:
        """Executes editor shortcuts and system recording microphone mute."""
        action = item.parameters.get("action", "")

        if action == "mute_mic":
            success = self.audio_controller.mute_microphone()
            speech = "Microphone muted, sir." if success else "Failed to mute microphone, sir."
            return ActionResult(
                intent=IntentType.SHORTCUT,
                spoken_response=speech,
                log_message=f"JARVIS: [MIC] {speech}",
                success=success,
                data={"action": "mute_mic"},
            )

        elif action == "unmute_mic":
            success = self.audio_controller.unmute_microphone()
            speech = "Microphone unmuted, sir." if success else "Failed to unmute microphone, sir."
            return ActionResult(
                intent=IntentType.SHORTCUT,
                spoken_response=speech,
                log_message=f"JARVIS: [MIC] {speech}",
                success=success,
                data={"action": "unmute_mic"},
            )

        success, speech = self.shortcut_controller.execute_shortcut(action)
        return ActionResult(
            intent=IntentType.SHORTCUT,
            spoken_response=speech,
            log_message=f"JARVIS: [SHORTCUT] {speech}",
            success=success,
            data={"action": action},
        )


# Global default instance
router = ActionRouter()
