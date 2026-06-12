"""Offline fallback helpers when voice or microphone is unavailable."""
from __future__ import annotations

from config import VOICE_FALLBACK_MESSAGE
import voice.speech_to_text as speech_to_text


OFFLINE_SCREEN_ID = "offline_continue"
OFFLINE_REASSURANCE = "You can still tap to play. Voice is optional."


def resolve_offline_message(reason: str | None = None) -> str:
    if reason and str(reason).strip():
        return str(reason).strip()
    status = speech_to_text.get_status_message()
    if status and "not ready" in status.lower():
        return status
    return VOICE_FALLBACK_MESSAGE


def offline_prompt_text(status_message: str) -> str:
    """Short overlay copy for the offline screen."""
    message = status_message.strip() or VOICE_FALLBACK_MESSAGE
    return f"{message}  {OFFLINE_REASSURANCE}"
