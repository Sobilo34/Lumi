"""Safe microphone readiness checks for the settings flow."""
from __future__ import annotations

from config import VOICE_FALLBACK_SCREEN_ID
import voice.speech_to_text as speech_to_text


def run_microphone_check(*, listen_timeout: int = 2) -> dict[str, str | bool | None]:
    """Run a short STT availability test without raising.

    Returns a result dict with:
    - next_screen_id: ``listening_state`` or ``offline_continue``
    - status_message: child-friendly status text
    - heard_text: recognized text when available
    - available: whether STT reported ready
    """
    if not speech_to_text.is_available():
        status_message = speech_to_text.get_status_message()
        if not status_message:
            status_message = "Voice is not ready. You can still tap answers."
        print(f"[Lumi Mic] STT unavailable: {status_message}")
        return {
            "next_screen_id": VOICE_FALLBACK_SCREEN_ID,
            "status_message": status_message,
            "heard_text": None,
            "available": False,
        }

    heard_text = None
    listen_error = False
    try:
        heard_text = speech_to_text.listen_once(timeout=listen_timeout)
    except Exception as error:
        listen_error = True
        print(f"[Lumi Mic] listen_once failed safely: {error}")
        heard_text = None

    if listen_error:
        status_message = speech_to_text.get_status_message()
        print(f"[Lumi Mic] routing offline after listen error: {status_message}")
        return {
            "next_screen_id": VOICE_FALLBACK_SCREEN_ID,
            "status_message": status_message,
            "heard_text": None,
            "available": False,
        }

    if heard_text:
        status_message = f"Microphone is ready. I heard: {heard_text}."
    else:
        status_message = "Microphone is ready."
    print(f"[Lumi Mic] {status_message}")
    return {
        "next_screen_id": "listening_state",
        "status_message": status_message,
        "heard_text": heard_text,
        "available": True,
    }
