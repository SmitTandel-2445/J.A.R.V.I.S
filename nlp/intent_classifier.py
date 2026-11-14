"""
Intent Classifier Module for J.A.R.V.I.S.
-----------------------------------------
Classifies user speech into distinct intent categories (local system commands vs.
general AI queries) using high-speed regex pattern matching and entity extraction.
"""

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple


class IntentType(str, Enum):
    """Enumeration of recognized user intent categories."""
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    SYSTEM_VOLUME = "system_volume"
    SYSTEM_POWER = "system_power"
    BROWSER_TAB = "browser_tab"
    MEDIA_CONTROL = "media_control"
    WINDOW_CONTROL = "window_control"
    SCREENSHOT = "screenshot"
    FILE_FOLDER = "file_folder"
    SYSTEM_BRIGHTNESS = "system_brightness"
    TIME_DATE = "time_date"
    WEB_SEARCH = "web_search"
    YOUTUBE_PLAY = "youtube_play"
    SPOTIFY_PLAY = "spotify_play"
    PLAY_MEDIA = "play_media"
    SYSTEM_TELEMETRY = "system_telemetry"
    GO_OFFLINE = "go_offline"
    CLIPBOARD = "clipboard"
    NETWORK = "network"
    TASK_MANAGER = "task_manager"
    TIMER = "timer"
    DISPLAY = "display"
    SHORTCUT = "shortcut"
    CONVERSATION_AI = "conversation_ai"


@dataclass
class IntentResult:
    """Structured representation of a classified user intent."""
    intent: IntentType
    raw_text: str
    cleaned_text: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class IntentClassifier:
    """
    Fast rule-based intent classifier.
    Evaluates queries against regular expressions to detect deterministic desktop
    actions in sub-millisecond time before falling back to cloud LLM processing.
    """

    # Prefixes / filler words to strip for cleaner intent matching (English, Hindi, and Hinglish)
    FILLER_PREFIXES = [
        r"^jarvis\b[,:]?\s*",
        r"^hey\s+jarvis\b[,:]?\s*",
        r"^ok\s+jarvis\b[,:]?\s*",
        r"^arre\s+jarvis\b[,:]?\s*",
        r"^suno\s+jarvis\b[,:]?\s*",
        r"^jarvis\s+(?:bhai|ji|yaar)\b[,:]?\s*",
        r"^kripya\b\s*",
        r"^zara\b\s*",
        r"^please\b\s*",
        r"^could\s+you\s+(?:please\s+)?",
        r"^can\s+you\s+(?:please\s+)?",
        r"^would\s+you\s+(?:please\s+)?",
    ]

    COMMAND_STARTERS = [
        r"open\b", r"launch\b", r"start\b", r"run\b",
        r"close\b", r"exit\b", r"terminate\b", r"kill\b", r"quit\b",
        r"play\b", r"pause\b", r"resume\b", r"stop\b",
        r"search\b", r"google\b", r"find\b", r"look\s+up\b",
        r"minimize\b", r"minimise\b", r"maximize\b", r"maximise\b", r"restore\b",
        r"snap\b", r"switch\b", r"show\s+desktop\b",
        r"set\s+volume\b", r"volume\b", r"mute\b", r"unmute\b",
        r"kholo\b", r"chalu\s+karo\b", r"band\s+karo\b", r"shuru\s+karo\b",
        r"awaaz\b", r"gaana\b", r"samay\b", r"tarikh\b", r"batao\b",
        r"set\s+brightness\b", r"brightness\b",
        r"take\s+(?:a\s+)?screenshot\b", r"capture\s+(?:the\s+)?screen\b", r"screenshot\b",
        r"create\s+(?:a\s+)?(?:new\s+)?folder\b", r"empty\s+(?:the\s+)?recycle\s+bin\b",
        r"lock\s+(?:screen|pc|workstation)\b",
        r"new\s+tab\b", r"close\s+tab\b", r"refresh\b", r"reload\b",
        r"go\s+offline\b", r"shutdown\b", r"shut\s+down\b", r"sleep\b",
        r"type\b", r"write\b", r"copy\b", r"clear\s+clipboard\b", r"read\s+clipboard\b",
        r"what\b", r"tell\s+me\b", r"who\b", r"how\b", r"check\b",
        r"test\b", r"ping\b", r"wifi\b", r"flush\s+dns\b", r"disconnect\b",
        r"end\s+task\b", r"is\b",
        r"scroll\b", r"zoom\b", r"go\s+to\b", r"navigate\b", r"bookmark\b", r"full\s*screen\b",
        r"set\s+(?:a\s+)?timer\b", r"timer\b", r"remind\b", r"focus\s+session\b", r"pomodoro\b",
        r"move\s+window\b", r"dark\s+mode\b", r"light\s+mode\b", r"night\s+light\b",
        r"save\b", r"select\s+all\b", r"undo\b", r"redo\b", r"mute\s+mic\b", r"unmute\s+mic\b"
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compiles regex patterns for performance."""
        # Cleaners
        self._prefix_regexes = [
            re.compile(p, re.IGNORECASE) for p in self.FILLER_PREFIXES
        ]
        self._command_starter_regex = re.compile(
            r"^(?:" + "|".join(self.COMMAND_STARTERS) + r")",
            re.IGNORECASE,
        )

        # Go Offline / Goodbye: "bye jarvis", "good bye jarvis", "go offline", "system offline", "halt", "shutdown"
        self._go_offline_regex = re.compile(
            r"^(?:"
            r"(?:(?:good\s*bye|bye\s*bye|bye|see\s+you(?:\s+later)?|farewell)(?:\s+jarvis)?)|"
            r"(?:(?:go\s+(?:to\s+|into\s+)?|become\s+)?offline(?:\s+now|\s+mode|\s+jarvis)?)|"
            r"(?:system\s+)?(?:offline|halt|halted)(?:\s+jarvis)?|"
            r"(?:jarvis\s+(?:go\s+(?:to\s+|into\s+)?offline|offline|halt|shut\s*down|shutdown|turn\s+off|power\s+down|power\s+off|stop\s+listening|sleep))|"
            r"(?:(?:shut\s*down|shutdown|turn\s+off|power\s+down|power\s+off|quit|exit|halt|stop\s+listening)(?:\s+jarvis|\s+system|\s+now)?)|"
            r"(?:(?:sleep|rest|stand\s*by|go\s+to\s+sleep)(?:\s+jarvis))"
            r")$",
            re.IGNORECASE,
        )

        # App Launching: "open chrome", "launch notepad", "start spotify", "chrome kholo", "notepad chalu karo"
        self._open_app_regex = re.compile(
            r"^(?:(?:open|launch|start|run|chalu\s+karo|shuru\s+karo)\s+(?:the\s+)?(?P<app_name>.+)|"
            r"(?P<app_name_hi>.+?)\s+(?:kholo|chalu\s+karo|start\s+karo|open\s+karo|chalao))$",
            re.IGNORECASE,
        )

        # App Closing: "close chrome", "exit notepad", "kill discord", "quit spotify", "chrome band karo"
        self._close_app_regex = re.compile(
            r"^(?:(?:close|exit|terminate|kill|quit|band\s+karo)\s+(?:the\s+)?(?P<app_name>.+)|"
            r"(?P<app_name_hi>.+?)\s+(?:band\s+karo|close\s+karo|hatao|kill\s+karo))$",
            re.IGNORECASE,
        )

        # Volume Controls: "volume up", "increase volume", "mute", "unmute", "set volume to 50", "awaaz badhao"
        self._volume_set_regex = re.compile(
            r"^(?:(?:set\s+volume\s+(?:to\s+)?|volume\s+(?:to\s+)?)(?P<level>\d{1,3})(?:\s*%)?|"
            r"(?:volume|awaaz)\s+(?P<level_hi>\d{1,3})\s+(?:karo|pe\s+karo|percent\s+karo))$",
            re.IGNORECASE,
        )
        self._volume_up_regex = re.compile(
            r"^(?:volume\s+up|increase\s+volume|turn\s+up\s+the\s+volume|louder|awaaz\s+badhao|volume\s+badhao|sound\s+badhao|awaaz\s+badao|awaaz\s+tez\s+karo|awaaz\s+tej\s+karo)$",
            re.IGNORECASE,
        )
        self._volume_down_regex = re.compile(
            r"^(?:volume\s+down|decrease\s+volume|lower\s+volume|turn\s+down\s+the\s+volume|softer|awaaz\s+kam\s+karo|volume\s+kam\s+karo|sound\s+kam\s+karo|awaaz\s+dheemi\s+karo|dheemi\s+karo)$",
            re.IGNORECASE,
        )
        self._volume_mute_regex = re.compile(
            r"^(?:mute|mute\s+audio|mute\s+sound|silence|awaaz\s+band\s+karo|mute\s+karo|chup\s+ho\s+jao)$",
            re.IGNORECASE,
        )
        self._volume_unmute_regex = re.compile(
            r"^(?:unmute|unmute\s+audio|unmute\s+sound|unmute\s+karo|awaaz\s+chalu\s+karo)$",
            re.IGNORECASE,
        )

        # Time & Date: "what time is it", "tell me the time", "what is today's date", "time kya hua hai"
        self._time_regex = re.compile(
            r"^(?:what(?:'s|\s+is)\s+(?:the\s+)?time|what\s+time\s+is\s+it|tell\s+me\s+the\s+time|current\s+time|time\s+kya\s+hua\s+hai|samay\s+kya\s+hua\s+hai|kitne\s+baje\s+hain|time\s+batao|samay\s+batao)$",
            re.IGNORECASE,
        )
        self._date_regex = re.compile(
            r"^(?:what(?:'s|\s+is)\s+(?:the\s+|today'?s\s+)?date|what\s+date\s+is\s+it|tell\s+me\s+the\s+date|what\s+day\s+is\s+it|aaj\s+ki\s+date\s+kya\s+hai|aaj\s+konsi\s+tarikh\s+hai|aaj\s+konsa\s+din\s+hai|date\s+batao|tarikh\s+batao)$",
            re.IGNORECASE,
        )

        # Web Search: "search X", "search for X", "search google for X", "google X", "find X", "look up X"
        self._search_regex = re.compile(
            r"^(?:search\s+(?:google\s+)?(?:for\s+)?|google\s+|find\s+|look\s+up\s+)(?P<query>.+)$",
            re.IGNORECASE,
        )

        # YouTube & Spotify Explicit Plays: "play X on youtube", "play X on spotify", "youtube par X bajao"
        self._youtube_regex = re.compile(
            r"^(?:play(?:\s+(?:the\s+)?(?:song|track|music|video))?\s+(?P<query>.+?)\s+(?:on|in)\s+youtube|"
            r"youtube\s+(?:par|pe)\s+(?P<query_hi>.+?)\s+(?:bajao|chalao|play\s+karo))$",
            re.IGNORECASE,
        )
        self._spotify_play_regex = re.compile(
            r"^(?:play(?:\s+(?:the\s+)?(?:song|track|music))?\s+(?P<query>.+?)\s+(?:on|in)\s+spotify|"
            r"spotify\s+(?:par|pe)\s+(?P<query_hi>.+?)\s+(?:bajao|chalao|play\s+karo))$",
            re.IGNORECASE,
        )

        # Context-Aware Play: "play luna bala", "play starboy", "play tarak mehta"
        self._generic_play_regex = re.compile(
            r"^play(?:\s+(?:the\s+)?(?:song|track|music))?\s+(?P<query>.+)$",
            re.IGNORECASE,
        )

        # Browser Tab Controls: "new tab", "close tab", "refresh page", "reopen tab", etc.
        self._tab_new_regex = re.compile(r"^(?:new\s+tab|open\s+(?:a\s+)?new\s+tab)$", re.IGNORECASE)
        self._tab_close_regex = re.compile(r"^(?:close\s+tab|close\s+this\s+tab)$", re.IGNORECASE)
        self._tab_reopen_regex = re.compile(r"^(?:reopen\s+tab|restore\s+tab)$", re.IGNORECASE)
        self._tab_next_regex = re.compile(r"^(?:next\s+tab|switch\s+to\s+next\s+tab)$", re.IGNORECASE)
        self._tab_prev_regex = re.compile(r"^(?:previous\s+tab|prev\s+tab|switch\s+to\s+previous\s+tab)$", re.IGNORECASE)
        self._tab_refresh_regex = re.compile(r"^(?:refresh(?:\s+the)?\s+(?:page|tab)|reload(?:\s+the)?\s+(?:page|tab)|reload)$", re.IGNORECASE)
        self._tab_back_regex = re.compile(r"^(?:go\s+back|back\s+page)$", re.IGNORECASE)
        self._tab_forward_regex = re.compile(r"^(?:go\s+forward|forward\s+page)$", re.IGNORECASE)
        self._tab_window_regex = re.compile(r"^(?:new\s+window|open\s+(?:a\s+)?new\s+window)$", re.IGNORECASE)
        self._tab_incognito_regex = re.compile(r"^(?:(?:open\s+)?incognito(?:\s+window)?|(?:open\s+)?private\s+window)$", re.IGNORECASE)

        # Extended Browser & Navigation Automations: scrolling, zoom, history, bookmarks, fullscreen, search page, navigate
        self._browser_scroll_down_regex = re.compile(r"^(?:scroll\s+down(?:\s+the\s+page)?|page\s+down)$", re.IGNORECASE)
        self._browser_scroll_up_regex = re.compile(r"^(?:scroll\s+up(?:\s+the\s+page)?|page\s+up)$", re.IGNORECASE)
        self._browser_scroll_top_regex = re.compile(r"^(?:scroll\s+to\s+(?:the\s+)?top|top\s+of\s+(?:the\s+)?page|go\s+to\s+(?:the\s+)?top)$", re.IGNORECASE)
        self._browser_scroll_bottom_regex = re.compile(r"^(?:scroll\s+to\s+(?:the\s+)?bottom|bottom\s+of\s+(?:the\s+)?page|go\s+to\s+(?:the\s+)?bottom)$", re.IGNORECASE)
        self._browser_zoom_in_regex = re.compile(r"^(?:zoom\s+in|increase\s+zoom)$", re.IGNORECASE)
        self._browser_zoom_out_regex = re.compile(r"^(?:zoom\s+out|decrease\s+zoom)$", re.IGNORECASE)
        self._browser_zoom_reset_regex = re.compile(r"^(?:reset\s+zoom|normal\s+zoom|default\s+zoom)$", re.IGNORECASE)
        self._browser_history_regex = re.compile(r"^(?:(?:show|open)\s+(?:browser\s+)?history|browser\s+history)$", re.IGNORECASE)
        self._browser_downloads_regex = re.compile(r"^(?:(?:show|open)\s+(?:browser\s+)?downloads|browser\s+downloads)$", re.IGNORECASE)
        self._browser_bookmarks_regex = re.compile(r"^(?:(?:show|open)\s+(?:browser\s+)?bookmarks|browser\s+bookmarks)$", re.IGNORECASE)
        self._browser_bookmark_page_regex = re.compile(r"^(?:bookmark(?:\s+this)?\s+page|add\s+(?:a\s+)?bookmark)$", re.IGNORECASE)
        self._browser_fullscreen_regex = re.compile(r"^(?:(?:toggle\s+|exit\s+)?full\s*screen(?:\s+browser|\s+mode)?|browser\s+full\s*screen)$", re.IGNORECASE)
        self._browser_find_regex = re.compile(r"^(?:find(?:\s+in|\s+on)?\s+(?:this\s+)?page(?:\s+for)?|search\s+(?:this\s+)?page(?:\s+for)?)\s+(?P<query>.+)$", re.IGNORECASE)
        self._browser_nav_regex = re.compile(r"^(?:(?:go\s+to|navigate\s+to|visit|open\s+website)\s+(?P<url>[a-zA-Z0-9\.\-/_:]+\.[a-zA-Z]{2,}(?:/\S*)?)|open\s+(?P<url2>https?://\S+|www\.\S+))$", re.IGNORECASE)

        # System Telemetry: "system status", "battery status", "cpu usage", "ram usage"
        self._telemetry_regex = re.compile(
            r"^(?:system\s+status|system\s+report|diagnostics|battery\s+status|check\s+battery|battery\s+report|cpu\s+usage|ram\s+usage)$",
            re.IGNORECASE,
        )

        # System Power: "lock screen", "lock workstation", "sleep", "go to sleep", "screen lock karo"
        self._lock_regex = re.compile(
            r"^(?:lock(?:\s+the)?\s+(?:screen|workstation|pc|computer)|lock\s+down|screen\s+lock\s+karo|pc\s+lock\s+karo)$",
            re.IGNORECASE,
        )
        self._sleep_regex = re.compile(
            r"^(?:(?:go\s+to\s+|put\s+(?:the\s+|this\s+)?(?:pc|computer)\s+to\s+)?sleep|enter\s+sleep\s+mode|sleep\s+pc|computer\s+ko\s+sleep\s+mode\s+me\s+daalo|pc\s+sleep\s+karo)$",
            re.IGNORECASE,
        )

        # Media Controls: "play music", "pause music", "next track", "gaana bajao", "gaana roko"
        self._media_play_pause_regex = re.compile(
            r"^(?:(?:play|pause|resume)(?:\s+(?:the\s+)?(?:music|song))?|pause|resume|gaana\s+bajao|music\s+bajao|gaana\s+roko|gaana\s+pause\s+karo)$",
            re.IGNORECASE,
        )
        self._media_next_regex = re.compile(
            r"^(?:next\s+(?:song|track)|skip\s+(?:song|track)?|agla\s+gaana|next\s+gaana)$",
            re.IGNORECASE,
        )
        self._media_prev_regex = re.compile(
            r"^(?:previous\s+(?:song|track)|prev\s+(?:song|track)|pichhla\s+gaana|pichla\s+gaana)$",
            re.IGNORECASE,
        )
        self._media_stop_regex = re.compile(
            r"^(?:stop\s+(?:the\s+)?(?:music|playback)|gaana\s+band\s+karo)$",
            re.IGNORECASE,
        )

        # Window Controls: "minimize window", "minimize chrome", "maximize window", "maximize vs code", "close window"
        self._win_min_regex = re.compile(
            r"^(?:minimize|minimise)(?:\s+(?:the\s+|this\s+|current\s+|active\s+)?(?:window|app|application)|\s+(?P<app_name>.+))?$",
            re.IGNORECASE,
        )
        self._win_max_regex = re.compile(
            r"^(?:maximize|maximise)(?:\s+(?:the\s+|this\s+|current\s+|active\s+)?(?:window|app|application)|\s+(?P<app_name>.+))?$",
            re.IGNORECASE,
        )
        self._win_restore_regex = re.compile(
            r"^(?:restore|unminimize|unminimise)(?:\s+(?:the\s+|this\s+|current\s+|active\s+)?(?:window|app|application)|\s+(?P<app_name>.+))?$",
            re.IGNORECASE,
        )
        self._win_close_regex = re.compile(
            r"^(?:close(?:\s+(?:the\s+|this\s+|current\s+|active\s+)?window)?|close\s+(?P<app_name>.+?)\s+window)$",
            re.IGNORECASE,
        )
        self._win_switch_regex = re.compile(r"^(?:switch(?:\s+(?:the\s+)?window)?|alt\s+tab)$", re.IGNORECASE)
        self._win_desktop_regex = re.compile(r"^(?:show\s+desktop|go\s+to\s+desktop)$", re.IGNORECASE)
        self._win_snap_left_regex = re.compile(r"^(?:snap(?:\s+(?:the\s+)?window)?\s+left|snap\s+left)$", re.IGNORECASE)
        self._win_snap_right_regex = re.compile(r"^(?:snap(?:\s+(?:the\s+)?window)?\s+right|snap\s+right)$", re.IGNORECASE)

        # Screenshot: "take screenshot", "capture screen", "screenshot", "screenshot lo", "screenshot kheencho"
        self._screenshot_regex = re.compile(
            r"^(?:take(?:\s+a)?\s+screenshot|capture(?:\s+the)?\s+screen|screenshot|screenshot\s+lo|screenshot\s+kheencho|screen\s+capture\s+karo)$",
            re.IGNORECASE,
        )

        # File & Folder: "open downloads", "open documents", "create folder [name]", "empty recycle bin"
        self._folder_open_regex = re.compile(
            r"^open\s+(?:the\s+)?(?P<folder>downloads|documents|desktop|pictures|photos|videos|movies|music|c\s+drive|d\s+drive)(?:\s+folder)?$",
            re.IGNORECASE,
        )
        self._folder_create_regex = re.compile(
            r"^create\s+(?:a\s+)?(?:new\s+)?folder\s+(?:named\s+|called\s+)?(?P<name>.+)$",
            re.IGNORECASE,
        )
        self._recycle_bin_regex = re.compile(
            r"^(?:empty(?:\s+the)?\s+recycle\s+bin|clean\s+recycle\s+bin)$",
            re.IGNORECASE,
        )

        # Brightness: "set brightness to 70%", "brightness up", "brightness down"
        self._bright_set_regex = re.compile(
            r"^(?:set\s+brightness\s+(?:to\s+)?|brightness\s+(?:to\s+)?)(?P<level>\d{1,3})(?:\s*%)?$",
            re.IGNORECASE,
        )
        self._bright_up_regex = re.compile(
            r"^(?:brightness\s+up|increase\s+brightness|screen\s+brighter)$",
            re.IGNORECASE,
        )
        self._bright_down_regex = re.compile(
            r"^(?:brightness\s+down|decrease\s+brightness|dim\s+screen|screen\s+dimmer)$",
            re.IGNORECASE,
        )

        # Clipboard & Typing Automation: "read clipboard", "copy that", "clear clipboard", "type X"
        self._clip_read_regex = re.compile(
            r"^(?:(?:what(?:'s|\s+is)\s+(?:on|in)\s+(?:my\s+|the\s+)?clipboard|read\s+(?:my\s+|the\s+)?clipboard(?:\s+contents?)?|check\s+(?:my\s+|the\s+)?clipboard|clipboard\s+content(?:s)?))$",
            re.IGNORECASE,
        )
        self._clip_copy_last_regex = re.compile(
            r"^(?:copy\s+(?:that|this|the\s+last\s+(?:response|answer|reply|message))(?:\s+to\s+(?:my\s+|the\s+)?clipboard)?|copy\s+to\s+(?:my\s+|the\s+)?clipboard)$",
            re.IGNORECASE,
        )
        self._clip_copy_text_regex = re.compile(
            r"^copy\s+(?P<text>.+?)\s+to\s+(?:my\s+|the\s+)?clipboard$",
            re.IGNORECASE,
        )
        self._clip_clear_regex = re.compile(
            r"^(?:clear|empty|clean)\s+(?:my\s+|the\s+)?clipboard$",
            re.IGNORECASE,
        )
        self._clip_type_regex = re.compile(
            r"^(?:type(?:\s+this)?(?:\s+out)?|write(?:\s+this)?(?:\s+down)?)(?:\s*[:,\-]\s*|\s+)(?P<text>.+)$",
            re.IGNORECASE,
        )

        # Network, Wi-Fi & Internet Diagnostics
        self._net_wifi_regex = re.compile(
            r"^(?:(?:check|test|show|get)(?:\s+(?:the|my))?\s+(?:wi-?fi|wifi|wireless)(?:\s+(?:status|connection|signal|network|speed))?|"
            r"(?:what\s+(?:wi-?fi|wifi)\s+(?:am\s+i|are\s+we)\s+connected\s+to)|"
            r"(?:what(?:'s|\s+is)\s+(?:my\s+|the\s+)?(?:wi-?fi|wifi|wireless)(?:\s+network|\s+status|\s+name)?)|"
            r"(?:wi-?fi|wifi|wireless)\s+(?:status|signal|info|details|check))$",
            re.IGNORECASE,
        )
        self._net_internet_regex = re.compile(
            r"^(?:(?:check|test)(?:\s+(?:the\s+|my\s+)?)?(?:internet|connection|network\s+connection|network\s+latency|ping)(?:\s+(?:speed|latency|connection|status))?|"
            r"is\s+(?:the\s+)?internet\s+working|"
            r"ping\s+test|"
            r"test\s+connection)$",
            re.IGNORECASE,
        )
        self._net_ip_regex = re.compile(
            r"^(?:(?:what(?:'s|\s+is)\s+(?:my\s+|the\s+)?(?:(?P<scope>local|private|public|external)\s+)?ip(?:\s+address)?)|"
            r"check\s+(?:my\s+)?(?:(?P<scope2>local|private|public|external)\s+)?ip(?:\s+address)?|"
            r"(?:my\s+)?(?:(?P<scope3>local|private|public|external)\s+)?ip\s+address)$",
            re.IGNORECASE,
        )
        self._net_diag_regex = re.compile(
            r"^(?:(?:run\s+)?network\s+diagnostics|"
            r"diagnose\s+(?:the\s+)?network|"
            r"network\s+(?:status|report|health))$",
            re.IGNORECASE,
        )
        self._net_flush_dns_regex = re.compile(
            r"^(?:flush\s+dns(?:\s+cache)?|clear\s+dns(?:\s+cache)?|empty\s+dns)$",
            re.IGNORECASE,
        )
        self._net_disconnect_wifi_regex = re.compile(
            r"^(?:disconnect\s+(?:from\s+)?(?:the\s+)?(?:wi-?fi|wifi|wireless)|turn\s+off\s+(?:wi-?fi|wifi|wireless))$",
            re.IGNORECASE,
        )

        # Advanced Task Manager & Resource Monitoring
        self._task_top_cpu_regex = re.compile(
            r"^(?:(?:what(?:'s|\s+is)\s+(?:using|consuming|taking\s+up)\s+(?:my\s+|the\s+)?cpu|(?:top|highest)\s+cpu(?:\s+(?:processes|consumers|apps))?|cpu\s+consumers|cpu\s+usage\s+by\s+process))$",
            re.IGNORECASE,
        )
        self._task_top_mem_regex = re.compile(
            r"^(?:(?:what(?:'s|\s+is)\s+(?:using|consuming|taking\s+up)\s+(?:my\s+|the\s+)?(?:ram|memory)|what(?:'s|\s+is)\s+slowing\s+down\s+my\s+(?:pc|computer)|(?:top|highest)\s+(?:ram|memory)(?:\s+(?:processes|consumers|apps))?|(?:heavy|highest\s+memory)\s+processes|ram\s+consumers))$",
            re.IGNORECASE,
        )
        self._task_proc_info_regex = re.compile(
            r"^(?:is\s+(?P<app1>.+?)\s+running|(?:check(?:\s+the)?\s+process|process\s+status|status\s+of(?:\s+process)?)\s+(?P<app2>.+)|how\s+much\s+(?:ram|memory|cpu)\s+is\s+(?P<app3>.+?)\s+using)$",
            re.IGNORECASE,
        )
        self._task_disk_regex = re.compile(
            r"^(?:(?:check\s+)?(?:disk|storage|drive)(?:\s+space)?(?:\s+(?:on|for)\s+(?P<drive>[a-zA-Z])(?:\s+drive)?)?|how\s+much\s+(?:storage|disk\s+space|free\s+space)(?:\s+do\s+i\s+have)?(?:\s+(?:left|remaining))?(?:\s+(?:on|in)\s+(?P<drive2>[a-zA-Z])(?:\s+drive)?)?|storage\s+status)$",
            re.IGNORECASE,
        )
        self._task_memory_regex = re.compile(
            r"^(?:(?:check\s+)?(?:ram|memory)\s+usage|(?:ram|memory)\s+breakdown|how\s+much\s+ram\s+(?:is\s+free|do\s+i\s+have|is\s+used)|check\s+(?:my\s+)?(?:ram|memory))$",
            re.IGNORECASE,
        )
        self._task_unresponsive_regex = re.compile(
            r"^(?:check(?:\s+for)?\s+(?:unresponsive|frozen|hung)\s+(?:apps|applications|processes|windows)|is\s+any(?:\s+app|\s+window)\s+(?:frozen|hung|unresponsive))$",
            re.IGNORECASE,
        )
        self._task_end_regex = re.compile(
            r"^(?:end\s+task\s+(?P<app1>.+)|kill\s+process\s+(?P<app2>.+)|terminate\s+process\s+(?P<app3>.+)|force\s+close\s+(?P<app4>.+))$",
            re.IGNORECASE,
        )

        # Connect Wi-Fi
        self._net_connect_wifi_regex = re.compile(
            r"^(?:(?:re)?connect(?:\s+to)?\s+(?:the\s+)?(?:wi-?fi|wifi|wireless)|turn\s+(?:on|back\s+on)\s+(?:wi-?fi|wifi|wireless)|turn\s+(?:the\s+)?(?:wi-?fi|wifi|wireless)\s+(?:back\s+on|on))$",
            re.IGNORECASE,
        )

        # System Uptime
        self._task_uptime_regex = re.compile(
            r"^(?:how\s+long\s+has\s+(?:my\s+|the\s+)?pc\s+been\s+(?:on|running)|check\s+system\s+uptime|system\s+uptime|uptime)$",
            re.IGNORECASE,
        )

        # Latest Download
        self._folder_latest_download_regex = re.compile(
            r"^(?:(?:open|what\s+is)\s+(?:my\s+|the\s+)?latest\s+download(?:ed\s+file)?|what\s+did\s+i(?:\s+just)?\s+download|open\s+last\s+download)$",
            re.IGNORECASE,
        )

        # Productivity Timers & Reminders
        self._timer_set_regex = re.compile(
            r"^(?:set\s+(?:a\s+)?timer\s+(?:for\s+)?(?P<num>\d+)\s*(?P<unit>seconds?|secs?|minutes?|mins?|hours?|hrs?)(?:\s+(?:for|called|named)\s+(?P<label>.+))?)$",
            re.IGNORECASE,
        )
        self._timer_status_regex = re.compile(
            r"^(?:how\s+much\s+time\s+(?:is\s+)?left(?:\s+on\s+(?:my|the)?\s*timer)?|timer\s+status|check\s+timer)$",
            re.IGNORECASE,
        )
        self._timer_cancel_regex = re.compile(
            r"^(?:cancel\s+(?:the\s+|my\s+)?timer|stop\s+(?:the\s+|my\s+)?timer)$",
            re.IGNORECASE,
        )
        self._reminder_set_regex = re.compile(
            r"^remind\s+me\s+(?:in\s+(?P<num>\d+)\s*(?P<unit>seconds?|secs?|minutes?|mins?|hours?|hrs?)\s+to\s+(?P<msg1>.+)|to\s+(?P<msg2>.+?)\s+in\s+(?P<num2>\d+)\s*(?P<unit2>seconds?|secs?|minutes?|mins?|hours?|hrs?))$",
            re.IGNORECASE,
        )
        self._focus_session_regex = re.compile(
            r"^(?:start\s+(?:a\s+)?(?:(?P<num>\d+)\s*[- ]?minute\s+)?(?:pomodoro|focus\s+session|work\s+session)|focus\s+session)$",
            re.IGNORECASE,
        )

        # Multi-Monitor & Theme Display
        self._display_move_regex = re.compile(
            r"^(?:move\s+(?:the\s+|this\s+)?window\s+to\s+(?:the\s+)?(?:second|next|other)\s+(?:monitor|screen|display)|send\s+(?:the\s+|this\s+)?window\s+to\s+(?:the\s+)?(?:second|next|other)\s+(?:monitor|screen|display))$",
            re.IGNORECASE,
        )
        self._theme_dark_regex = re.compile(
            r"^(?:switch(?:\s+to)?\s+dark\s+mode|turn\s+on\s+dark\s+mode|dark\s+mode)$",
            re.IGNORECASE,
        )
        self._theme_light_regex = re.compile(
            r"^(?:switch(?:\s+to)?\s+light\s+mode|turn\s+on\s+light\s+mode|light\s+mode)$",
            re.IGNORECASE,
        )
        self._night_light_regex = re.compile(
            r"^(?:turn\s+on\s+night\s+light|open\s+night\s+light|night\s+light)$",
            re.IGNORECASE,
        )

        # Global Keyboard & Workflow Shortcuts
        self._shortcut_save_regex = re.compile(
            r"^(?:save(?:\s+(?:the\s+)?file)?|save\s+document)$",
            re.IGNORECASE,
        )
        self._shortcut_select_all_regex = re.compile(
            r"^select\s+all$",
            re.IGNORECASE,
        )
        self._shortcut_undo_regex = re.compile(
            r"^undo$",
            re.IGNORECASE,
        )
        self._shortcut_redo_regex = re.compile(
            r"^redo$",
            re.IGNORECASE,
        )
        self._mic_mute_regex = re.compile(
            r"^(?:mute(?:\s+my)?\s+mic(?:rophone)?|silence\s+mic)$",
            re.IGNORECASE,
        )
        self._mic_unmute_regex = re.compile(
            r"^(?:unmute(?:\s+my)?\s+mic(?:rophone)?)$",
            re.IGNORECASE,
        )

    def clean_query(self, text: str) -> str:
        """
        Strips polite conversational wrappers and wake words to expose the core command.
        Example: 'Jarvis, could you please open Chrome' -> 'open Chrome'
        """
        cleaned = text.strip()
        # Repeatedly strip matching prefixes (e.g. 'Jarvis, please open...')
        changed = True
        while changed:
            changed = False
            for regex in self._prefix_regexes:
                new_text = regex.sub("", cleaned).strip()
                if new_text != cleaned:
                    cleaned = new_text
                    changed = True

        # Remove trailing punctuation
        cleaned = re.sub(r"[?!.]+$", "", cleaned).strip()
        return cleaned

    def is_command_start(self, phrase: str) -> bool:
        """Checks if a clause begins with an imperative action verb or intent trigger."""
        p = phrase.strip()
        p = re.sub(r"^(?:and\s+then\s+|and\s+also\s+|and\s+|then\s+|also\s+|after\s+that\s+)", "", p, flags=re.IGNORECASE).strip()
        p = re.sub(r"^(?:please\s+|could\s+you\s+|can\s+you\s+)", "", p, flags=re.IGNORECASE).strip()
        return bool(self._command_starter_regex.search(p))

    def split_compound_commands(self, text: str) -> List[str]:
        """
        Splits a compound spoken query into distinct sub-commands.
        Preserves 'and' inside search titles or song parameters (e.g. 'Tom and Jerry').
        """
        cleaned = self.clean_query(text)

        # 1. Primary split by explicit sequence transition markers and delimiters
        primary_split = re.split(
            r"(?:\s+(?:and\s+then|then|and\s+also|also|and\s+after\s+that|after\s+that)\s+|[;,]\s*(?:and\s+)?)",
            cleaned,
            flags=re.IGNORECASE,
        )

        sub_commands: List[str] = []
        for chunk in primary_split:
            chunk = chunk.strip()
            if not chunk:
                continue

            # 2. Check if chunk has ' and ' connecting two command clauses
            and_parts = re.split(r"\s+and\s+", chunk, flags=re.IGNORECASE)
            merged: List[str] = []
            for part in and_parts:
                part = part.strip()
                if not part:
                    continue
                if not merged:
                    merged.append(part)
                else:
                    if self.is_command_start(part):
                        merged.append(part)
                    else:
                        merged[-1] = merged[-1] + " and " + part
            sub_commands.extend(merged)

        # 3. Clean leading connectors from each piece and ensure valid non-empty commands
        connector_pattern = re.compile(r"^(?:and\s+then\s+|and\s+also\s+|and\s+|then\s+|also\s+|after\s+that\s+)", re.IGNORECASE)
        clean_subs = []
        for s in sub_commands:
            s_clean = connector_pattern.sub("", s.strip()).strip()
            if len(s_clean) > 1:
                clean_subs.append(s_clean)

        return clean_subs if clean_subs else [cleaned]

    def classify_multi(self, text: str) -> List[IntentResult]:
        """
        Analyzes a spoken query and returns a list of classified intents for
        compound commands, or a single intent for simple commands.
        """
        sub_phrases = self.split_compound_commands(text)
        if len(sub_phrases) <= 1:
            return [self.classify(text)]

        results = []
        for phrase in sub_phrases:
            results.append(self.classify(phrase))
        return results

    def classify(self, text: str) -> IntentResult:
        """
        Analyzes a raw voice utterance and returns its classified intent with parameters.

        :param text: Raw spoken text (e.g., 'Jarvis, open Chrome')
        :return: IntentResult object detailing the classified intent
        """
        cleaned = self.clean_query(text)

        # 0. Go Offline / Farewell Match ("bye jarvis", "good bye jarvis", "go offline", etc.)
        if self._go_offline_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.GO_OFFLINE,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "offline"},
            )

        # 0.1 Clipboard & Typing Automation Matches
        if self._clip_read_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "read"},
            )
        if self._clip_copy_last_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "copy_last"},
            )
        copy_text_m = self._clip_copy_text_regex.match(cleaned)
        if copy_text_m:
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "copy", "text": copy_text_m.group("text").strip()},
            )
        if self._clip_clear_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "clear"},
            )
        type_m = self._clip_type_regex.match(cleaned)
        if type_m:
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "type", "text": type_m.group("text").strip()},
            )

        # 1. Explicit YouTube Play Match ("play X on youtube", "youtube par X bajao")
        yt_match = self._youtube_regex.match(cleaned)
        if yt_match:
            yt_query = (yt_match.group("query") or yt_match.group("query_hi") or "").strip()
            return IntentResult(
                intent=IntentType.YOUTUBE_PLAY,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"query": yt_query},
            )

        # 2. Explicit Spotify Play Match ("play X on spotify", "spotify par X bajao")
        spot_match = self._spotify_play_regex.match(cleaned)
        if spot_match:
            spot_query = (spot_match.group("query") or spot_match.group("query_hi") or "").strip()
            return IntentResult(
                intent=IntentType.SPOTIFY_PLAY,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"query": spot_query},
            )

        # 3. Media Toggle Controls ("play music", "pause music", "resume")
        if self._media_play_pause_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.MEDIA_CONTROL,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "play_pause"},
            )

        # 4. Context-Aware Song Play ("play luna bala", "play starboy")
        play_match = self._generic_play_regex.match(cleaned)
        if play_match:
            return IntentResult(
                intent=IntentType.PLAY_MEDIA,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"query": play_match.group("query").strip()},
            )

        # 5. Browser Find in Page & Direct Navigation (Checked before Web Search so 'find in page' matches here)
        find_match = self._browser_find_regex.match(cleaned)
        if find_match:
            return IntentResult(
                intent=IntentType.BROWSER_TAB,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "find", "query": find_match.group("query").strip()},
            )

        nav_match = self._browser_nav_regex.match(cleaned)
        if nav_match:
            url = nav_match.group("url") or nav_match.group("url2") or ""
            return IntentResult(
                intent=IntentType.BROWSER_TAB,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "navigate", "url": url.strip()},
            )

        # 6. Web Search Match
        search_match = self._search_regex.match(cleaned)
        if search_match:
            return IntentResult(
                intent=IntentType.WEB_SEARCH,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"query": search_match.group("query").strip()},
            )

        # 3. Browser Tab Controls (Checked before Open App so 'open a new tab' matches here)
        tab_actions = [
            (self._tab_new_regex, "new_tab"),
            (self._tab_close_regex, "close_tab"),
            (self._tab_reopen_regex, "reopen_tab"),
            (self._tab_next_regex, "next_tab"),
            (self._tab_prev_regex, "prev_tab"),
            (self._tab_refresh_regex, "refresh"),
            (self._tab_back_regex, "back"),
            (self._tab_forward_regex, "forward"),
            (self._tab_window_regex, "new_window"),
            (self._tab_incognito_regex, "incognito"),
            (self._browser_scroll_down_regex, "scroll_down"),
            (self._browser_scroll_up_regex, "scroll_up"),
            (self._browser_scroll_top_regex, "scroll_top"),
            (self._browser_scroll_bottom_regex, "scroll_bottom"),
            (self._browser_zoom_in_regex, "zoom_in"),
            (self._browser_zoom_out_regex, "zoom_out"),
            (self._browser_zoom_reset_regex, "zoom_reset"),
            (self._browser_history_regex, "history"),
            (self._browser_downloads_regex, "downloads"),
            (self._browser_bookmarks_regex, "bookmarks"),
            (self._browser_bookmark_page_regex, "bookmark_page"),
            (self._browser_fullscreen_regex, "fullscreen"),
        ]
        for regex, act in tab_actions:
            if regex.match(cleaned):
                return IntentResult(
                    intent=IntentType.BROWSER_TAB,
                    raw_text=text,
                    cleaned_text=cleaned,
                    parameters={"action": act},
                )

        # 4. Window Control Matches (Evaluated before App Launch/Close so 'close window' is not treated as an app named 'window')
        win_actions = [
            (self._win_min_regex, "minimize"),
            (self._win_max_regex, "maximize"),
            (self._win_restore_regex, "restore"),
            (self._win_close_regex, "close"),
            (self._win_switch_regex, "switch"),
            (self._win_desktop_regex, "desktop"),
            (self._win_snap_left_regex, "snap_left"),
            (self._win_snap_right_regex, "snap_right"),
        ]
        for regex, act in win_actions:
            m = regex.match(cleaned)
            if m:
                app_name = m.groupdict().get("app_name")
                params = {"action": act}
                if app_name:
                    clean_app = app_name.strip()
                    if clean_app.lower() not in {"window", "the window", "this window", "app", "application"}:
                        params["app_name"] = clean_app
                return IntentResult(
                    intent=IntentType.WINDOW_CONTROL,
                    raw_text=text,
                    cleaned_text=cleaned,
                    parameters=params,
                )

        # 5. Folder Open Match (Checked before general Open App)
        if self._folder_latest_download_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.FILE_FOLDER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "latest_download"},
            )

        folder_match = self._folder_open_regex.match(cleaned)
        if folder_match:
            return IntentResult(
                intent=IntentType.FILE_FOLDER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "open", "folder": folder_match.group("folder").strip()},
            )

        # 6. Network, Wi-Fi & Internet Diagnostics (Evaluated before App Launch so 'run network diagnostics' is not treated as an app)
        if self._net_wifi_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.NETWORK,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "wifi"},
            )
        if self._net_internet_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.NETWORK,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "internet"},
            )
        ip_m = self._net_ip_regex.match(cleaned)
        if ip_m:
            raw_scope = (ip_m.group("scope") or ip_m.group("scope2") or ip_m.group("scope3") or "").lower()
            if raw_scope in ("local", "private"):
                scope = "local"
            elif raw_scope in ("public", "external"):
                scope = "public"
            else:
                scope = "all"
            return IntentResult(
                intent=IntentType.NETWORK,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "ip", "scope": scope},
            )
        if self._net_diag_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.NETWORK,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "diagnostics"},
            )
        if self._net_flush_dns_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.NETWORK,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "flush_dns"},
            )
        if self._net_disconnect_wifi_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.NETWORK,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "disconnect_wifi"},
            )
        if self._net_connect_wifi_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.NETWORK,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "connect_wifi"},
            )

        # 7. Advanced Task Manager & Resource Monitoring
        if self._task_top_cpu_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.TASK_MANAGER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "top_cpu"},
            )
        if self._task_top_mem_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.TASK_MANAGER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "top_memory"},
            )
        task_proc_m = self._task_proc_info_regex.match(cleaned)
        if task_proc_m:
            app = task_proc_m.group("app1") or task_proc_m.group("app2") or task_proc_m.group("app3") or ""
            return IntentResult(
                intent=IntentType.TASK_MANAGER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "process_info", "app_name": app.strip()},
            )
        task_disk_m = self._task_disk_regex.match(cleaned)
        if task_disk_m:
            drive = task_disk_m.group("drive") or task_disk_m.group("drive2") or "C"
            return IntentResult(
                intent=IntentType.TASK_MANAGER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "disk_space", "drive": drive.strip()},
            )
        if self._task_memory_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.TASK_MANAGER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "memory_breakdown"},
            )
        if self._task_unresponsive_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.TASK_MANAGER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "check_frozen"},
            )
        task_end_m = self._task_end_regex.match(cleaned)
        if task_end_m:
            app = task_end_m.group("app1") or task_end_m.group("app2") or task_end_m.group("app3") or task_end_m.group("app4") or ""
            return IntentResult(
                intent=IntentType.TASK_MANAGER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "end_process", "app_name": app.strip()},
            )
        if self._task_uptime_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.TASK_MANAGER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "uptime"},
            )

        # 8. Productivity Timers & Reminders
        timer_set_m = self._timer_set_regex.match(cleaned)
        if timer_set_m:
            num = int(timer_set_m.group("num"))
            unit = timer_set_m.group("unit").lower()
            mult = 1
            if unit.startswith(("min", "m")):
                mult = 60
            elif unit.startswith(("hour", "hr", "h")):
                mult = 3600
            total_sec = num * mult
            label = timer_set_m.group("label") or "timer"
            return IntentResult(
                intent=IntentType.TIMER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "set_timer", "seconds": total_sec, "label": label.strip()},
            )

        if self._timer_status_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.TIMER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "status"},
            )

        if self._timer_cancel_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.TIMER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "cancel"},
            )

        remind_m = self._reminder_set_regex.match(cleaned)
        if remind_m:
            num = int(remind_m.group("num") or remind_m.group("num2") or 0)
            unit = (remind_m.group("unit") or remind_m.group("unit2") or "seconds").lower()
            mult = 1
            if unit.startswith(("min", "m")):
                mult = 60
            elif unit.startswith(("hour", "hr", "h")):
                mult = 3600
            total_sec = num * mult
            msg = remind_m.group("msg1") or remind_m.group("msg2") or "Reminder"
            return IntentResult(
                intent=IntentType.TIMER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "set_reminder", "seconds": total_sec, "message": msg.strip()},
            )

        focus_m = self._focus_session_regex.match(cleaned)
        if focus_m:
            mins = int(focus_m.group("num") or 25)
            return IntentResult(
                intent=IntentType.TIMER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "focus_session", "minutes": mins},
            )

        # 9. Multi-Monitor & Theme Display Management
        if self._display_move_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.DISPLAY,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "move_monitor"},
            )
        if self._theme_dark_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.DISPLAY,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "theme", "mode": "dark"},
            )
        if self._theme_light_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.DISPLAY,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "theme", "mode": "light"},
            )
        if self._night_light_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.DISPLAY,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "night_light"},
            )

        # 10. Global Keyboard Shortcuts & Mic Mute
        if self._shortcut_save_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SHORTCUT,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "save"},
            )
        if self._shortcut_select_all_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SHORTCUT,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "select_all"},
            )
        if self._shortcut_undo_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SHORTCUT,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "undo"},
            )
        if self._shortcut_redo_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SHORTCUT,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "redo"},
            )
        if self._mic_mute_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SHORTCUT,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "mute_mic"},
            )
        if self._mic_unmute_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SHORTCUT,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "unmute_mic"},
            )

        # 11. App Launch Match ("open chrome", "chrome kholo")
        open_match = self._open_app_regex.match(cleaned)
        if open_match:
            app_name = (open_match.group("app_name") or open_match.group("app_name_hi") or "").strip()
            return IntentResult(
                intent=IntentType.OPEN_APP,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"app_name": app_name},
            )

        # 4. App Close Match ("close chrome", "chrome band karo")
        close_match = self._close_app_regex.match(cleaned)
        if close_match:
            app_name = (close_match.group("app_name") or close_match.group("app_name_hi") or "").strip()
            return IntentResult(
                intent=IntentType.CLOSE_APP,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"app_name": app_name},
            )

        # 5. Volume Set / Mute / Up / Down Matches
        vol_set_match = self._volume_set_regex.match(cleaned)
        if vol_set_match:
            raw_lvl = vol_set_match.group("level") or vol_set_match.group("level_hi") or "50"
            level = int(raw_lvl)
            return IntentResult(
                intent=IntentType.SYSTEM_VOLUME,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "set", "level": max(0, min(100, level))},
            )

        if self._volume_up_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SYSTEM_VOLUME,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "up", "step": 10},
            )

        if self._volume_down_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SYSTEM_VOLUME,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "down", "step": 10},
            )

        if self._volume_mute_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SYSTEM_VOLUME,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "mute"},
            )

        if self._volume_unmute_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SYSTEM_VOLUME,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "unmute"},
            )

        # 6. Time & Date Matches
        if self._time_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.TIME_DATE,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"query_type": "time"},
            )

        if self._date_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.TIME_DATE,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"query_type": "date"},
            )

        # 7. System Telemetry Match
        if self._telemetry_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SYSTEM_TELEMETRY,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={},
            )

        # 8. System Power Matches (Lock, Sleep)
        if self._lock_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SYSTEM_POWER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "lock"},
            )

        if self._sleep_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SYSTEM_POWER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "sleep"},
            )

        # 9. Media Control Matches
        if self._media_play_pause_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.MEDIA_CONTROL,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "play_pause"},
            )
        if self._media_next_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.MEDIA_CONTROL,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "next"},
            )
        if self._media_prev_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.MEDIA_CONTROL,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "previous"},
            )
        if self._media_stop_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.MEDIA_CONTROL,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "stop"},
            )


        # 11. Screenshot Match
        if self._screenshot_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SCREENSHOT,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={},
            )

        # 12. File & Folder Matches
        create_match = self._folder_create_regex.match(cleaned)
        if create_match:
            return IntentResult(
                intent=IntentType.FILE_FOLDER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "create", "name": create_match.group("name").strip()},
            )

        if self._recycle_bin_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.FILE_FOLDER,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "empty_recycle_bin"},
            )

        # 13. Screen Brightness Matches
        bright_set_match = self._bright_set_regex.match(cleaned)
        if bright_set_match:
            return IntentResult(
                intent=IntentType.SYSTEM_BRIGHTNESS,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "set", "level": int(bright_set_match.group("level"))},
            )
        if self._bright_up_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SYSTEM_BRIGHTNESS,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "up", "step": 10},
            )
        if self._bright_down_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.SYSTEM_BRIGHTNESS,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "down", "step": 10},
            )

        # 14. Clipboard & Text Automation Matches
        if self._clip_read_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "read"},
            )
        if self._clip_copy_last_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "copy_last"},
            )
        clip_copy_m = self._clip_copy_text_regex.match(cleaned)
        if clip_copy_m:
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "copy", "text": clip_copy_m.group("text").strip()},
            )
        if self._clip_clear_regex.match(cleaned):
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "clear"},
            )
        clip_type_m = self._clip_type_regex.match(cleaned)
        if clip_type_m:
            return IntentResult(
                intent=IntentType.CLIPBOARD,
                raw_text=text,
                cleaned_text=cleaned,
                parameters={"action": "type", "text": clip_type_m.group("text").strip()},
            )

        # 16. Fallback to General AI Conversation
        return IntentResult(
            intent=IntentType.CONVERSATION_AI,
            raw_text=text,
            cleaned_text=cleaned,
            parameters={"query": text},
        )
