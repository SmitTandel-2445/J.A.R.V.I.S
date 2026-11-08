"""
AI subsystem for J.A.R.V.I.S.
Provides Google Gemini client, persona prompts, and conversational reasoning.
"""

from ai.gemini_client import GeminiBrain, brain
from ai.prompts import JARVIS_SYSTEM_INSTRUCTION

__all__ = ["GeminiBrain", "brain", "JARVIS_SYSTEM_INSTRUCTION"]

