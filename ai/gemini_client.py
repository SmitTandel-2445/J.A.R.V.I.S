"""
Gemini AI Client Module for J.A.R.V.I.S.
----------------------------------------
Provides intelligence, reasoning, and multi-turn conversational capabilities
using the Google GenAI SDK.
"""

import threading
from typing import Callable, Optional
from google import genai
from google.genai import types

import config
from ai.prompts import JARVIS_SYSTEM_INSTRUCTION
from utils.logger import logger


class GeminiBrain:
    """Manages conversational intelligence and multi-turn dialog with Google Gemini."""

    DEFAULT_MODEL = "gemini-3.5-flash-lite"
    FALLBACK_MODEL = "gemini-3.5-flash"
    REQUEST_TIMEOUT_MS = 20000  # 20 seconds timeout to prevent hanging

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        system_instruction: str = JARVIS_SYSTEM_INSTRUCTION,
        temperature: float = 0.7,
        max_output_tokens: int = 250,
    ):
        """
        Initialize the Gemini AI brain.

        :param api_key: Gemini API key (defaults to config.GEMINI_API_KEY)
        :param model: Gemini model identifier (defaults to gemini-3.5-flash-lite)
        :param system_instruction: J.A.R.V.I.S. persona prompt
        :param temperature: Creativity/predictability (0.0 = deterministic, 1.0 = creative)
        :param max_output_tokens: Maximum tokens in response (keeps voice output concise)
        """
        self.api_key = api_key or getattr(config, "GEMINI_API_KEY", None)
        self.model = model or self.DEFAULT_MODEL
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        self._client: Optional[genai.Client] = None
        self._chat: Optional[genai.chats.Chat] = None
        self._lock = threading.Lock()

        self._init_client()

    def _create_chat(self) -> None:
        """Helper to create a fresh multi-turn chat session."""
        if not self._client:
            return
        try:
            self._chat = self._client.chats.create(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                ),
            )
            logger.info("Chat session initialized successfully.")
        except Exception:
            logger.exception("Failed to create chat session.")
            self._chat = None

    def _init_client(self) -> None:
        """Initializes the GenAI Client with HTTP timeout and multi-turn chat session."""
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY found. AI Brain will run in offline mode.")
            return

        try:
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=self.REQUEST_TIMEOUT_MS),
            )
            self._create_chat()
            logger.info(f"Gemini AI Brain initialized with model '{self.model}'.")
        except Exception:
            logger.exception("Failed to initialize Google GenAI client.")
            self._client = None
            self._chat = None

    def ask(self, query: str) -> str:
        """
        Sends a query to Gemini and returns the spoken response.
        Thread-safe and equipped with graceful offline fallbacks and timeout safeguards.

        :param query: Spoken user query or command
        :return: Natural language response string from J.A.R.V.I.S.
        """
        query = query.strip()
        if not query:
            return ""

        if not self._client:
            logger.warning("AI Brain queried, but client is not initialized.")
            return "My core neural connection is offline, sir. Please check your API configuration."

        # Acquire lock with a timeout so subsequent threads never deadlock
        acquired = self._lock.acquire(timeout=15.0)
        if not acquired:
            logger.warning(f"Could not acquire brain lock within 15s for query: '{query}'")
            return "Apologies sir, I am currently processing your previous request. One moment please."

        try:
            # Recreate chat session if it was invalidated or not yet created
            if not self._chat:
                self._create_chat()

            if self._chat:
                try:
                    response = self._chat.send_message(query)
                    answer = response.text.strip() if response and response.text else ""
                    if answer:
                        logger.info(f"Gemini Replied: '{answer}'")
                        return answer
                    else:
                        return "I processed your request, sir, but have nothing further to report."
                except Exception as e:
                    logger.warning(f"Primary chat request failed ({e}). Re-initializing chat and trying fallback model...")
                    # Reset chat state in case the session history was corrupted by the failure
                    self._create_chat()

            # Fallback to single-shot generation using the robust fallback model
            try:
                res = self._client.models.generate_content(
                    model=self.FALLBACK_MODEL,
                    contents=f"{self.system_instruction}\nUser: {query}",
                    config=types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_output_tokens,
                    ),
                )
                if res and res.text:
                    answer = res.text.strip()
                    logger.info(f"Gemini (Fallback) Replied: '{answer}'")
                    return answer
            except Exception:
                logger.exception(f"Fallback generation also failed for query: '{query}'")

            return (
                "I experienced a momentary connection interruption, sir. "
                "Could you please repeat that?"
            )

        finally:
            self._lock.release()

    def ask_async(
        self,
        query: str,
        on_reply: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Non-blocking asynchronous version of ask().
        Executes query on a worker thread and delivers reply via callback.
        Ideal for the GUI so the Arc Reactor animation never freezes.
        """
        def _worker():
            try:
                reply = self.ask(query)
                if on_reply:
                    on_reply(reply)
            except Exception as e:
                logger.exception("Unexpected error in AI ask worker thread.")
                if on_error:
                    on_error(str(e))
                elif on_reply:
                    on_reply("I encountered an internal error processing your request, sir.")

        thread = threading.Thread(
            target=_worker,
            name="JARVIS-AI-Worker",
            daemon=True,
        )
        thread.start()

    def reset_chat(self) -> None:
        """Clears conversational history and begins a fresh session."""
        acquired = self._lock.acquire(timeout=5.0)
        if acquired:
            try:
                self._create_chat()
                logger.info("Conversational memory reset.")
            finally:
                self._lock.release()


# Global default instance
brain = GeminiBrain()
