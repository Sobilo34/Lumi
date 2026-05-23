"""Text-to-speech helper with graceful fallback."""
from __future__ import annotations

try:
    import pyttsx3
except Exception:  # pragma: no cover - dependency may be absent in headless checks
    pyttsx3 = None


class TextToSpeech:
    def __init__(self) -> None:
        self._engine = pyttsx3.init() if pyttsx3 is not None else None

    def speak(self, text: str) -> bool:
        if self._engine is None:
            return False
        self._engine.say(text)
        self._engine.runAndWait()
        return True
