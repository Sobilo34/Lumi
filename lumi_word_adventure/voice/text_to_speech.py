"""Text-to-speech helper with graceful fallback.

pyttsx3 must only be driven from one worker thread. Never call engine.stop()
from the main/game thread while runAndWait() is active — that deadlocks the app.
"""
from __future__ import annotations

from queue import Empty, Queue
import threading
from typing import Any

try:
    import pyttsx3
except Exception:  # pragma: no cover - dependency may be absent in headless checks
    pyttsx3 = None


class TextToSpeech:
    def __init__(self, enabled: bool = True, rate: int = 135) -> None:
        self._enabled = enabled
        self._rate = rate
        self._queue: Queue[str | None] = Queue()
        self._engine: Any = None
        self._worker: threading.Thread | None = None
        self._available = False
        self._initialize_engine()

    @property
    def enabled(self) -> bool:
        return self._enabled and self._available

    @property
    def is_available(self) -> bool:
        return self._available

    def _initialize_engine(self) -> None:
        if pyttsx3 is None:
            self._available = False
            return
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._rate)
            self._available = True
            self._worker = threading.Thread(target=self._run_worker, daemon=True, name="lumi-tts")
            self._worker.start()
        except Exception as error:
            self._engine = None
            self._available = False
            print(f"[Lumi Voice] TTS init failed safely: {error}")

    def _run_worker(self) -> None:
        while True:
            try:
                text = self._queue.get(timeout=0.2)
            except Empty:
                continue

            if text is None:
                break

            if not self._enabled or self._engine is None:
                continue

            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as error:
                print(f"[Lumi Voice] TTS playback failed safely: {error}")

    def clear_pending(self) -> None:
        """Drop queued lines without touching the pyttsx3 engine (thread-safe)."""
        try:
            while True:
                self._queue.get_nowait()
        except Empty:
            pass

    def speak(self, text: str) -> bool:
        cleaned_text = str(text).strip()
        if not cleaned_text:
            return False
        if not self._enabled:
            return False
        if not self._available:
            print(f"[Lumi Voice] TTS unavailable, skipped speech.")
            return False
        self._queue.put(cleaned_text)
        return True

    def stop(self) -> None:
        """Clear pending speech only — safe to call from the game thread."""
        self.clear_pending()

    def shutdown(self) -> None:
        """Stop worker thread during app exit."""
        self.clear_pending()
        if self._worker is not None and self._worker.is_alive():
            self._queue.put(None)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        if not self._enabled:
            self.clear_pending()

    def set_rate(self, rate: int) -> None:
        self._rate = int(rate)
        if self._engine is not None:
            try:
                self._engine.setProperty("rate", self._rate)
            except Exception:
                pass
