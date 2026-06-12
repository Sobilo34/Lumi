"""Shared voice failure guards for STT entry points."""
from __future__ import annotations

import voice.speech_to_text as speech_to_text

STT_UNAVAILABLE_MESSAGE = "Voice is not ready. You can still tap answers."


def stt_status_message() -> str:
    message = speech_to_text.get_status_message()
    return message or STT_UNAVAILABLE_MESSAGE


def is_stt_ready() -> bool:
    try:
        return bool(speech_to_text.is_available())
    except Exception as error:
        print(f"[Lumi Voice] STT availability check failed safely: {error}")
        return False


def safe_listen_once(timeout: int = 5) -> str | None:
    if not is_stt_ready():
        return None
    try:
        return speech_to_text.listen_once(timeout=timeout)
    except Exception as error:
        print(f"[Lumi Voice] listen_once failed safely: {error}")
        return None
