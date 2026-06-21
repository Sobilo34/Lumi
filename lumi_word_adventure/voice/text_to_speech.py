"""Text-to-speech helper with a warm, female, child-friendly voice.

Design goals:
- A gentle FEMALE voice that is pleasing for 2-4 year olds (never a deep,
  "scary" default robot voice).
- Context-adaptive prosody: prompts are calm and clear, praise is bright and
  excited, "try again" is soft and reassuring.
- Fully offline and resilient: if the speech backend is missing we degrade to
  silent no-ops instead of crashing.

pyttsx3 must only be driven from one worker thread. Never call engine.stop()
from the main/game thread while runAndWait() is active — that deadlocks the app.
"""
from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
import threading
from typing import Any

try:
    import pyttsx3
except Exception:  # pragma: no cover - dependency may be absent in headless checks
    pyttsx3 = None


# One warm, young-sounding female timbre is used everywhere so toddlers hear a
# single familiar friend ("Lumi"). eSpeak-NG ships named female variants that
# are far gentler than the raw f1..f5 timbres (which sound robotic / "scary").
# We keep the SAME variant across contexts and only vary pace + loudness so the
# personality stays consistent; rates are deliberately slow for ages 2-4.
PRIMARY_FEMALE_VARIANT = "Annie"
# Tried in order until eSpeak accepts one (older builds may miss named ones).
FEMALE_VARIANT_FALLBACKS = ("Annie", "Alicia", "linda", "f3")

# Per-context prosody. Rates are eSpeak words-per-minute (slow = clearer for
# little ears); volume nudges add a touch of brightness or softness.
TONE_PRESETS: dict[str, dict[str, Any]] = {
    "neutral": {"rate": 132, "volume": 1.0},
    "instruct": {"rate": 124, "volume": 1.0},    # slow, clear prompts
    "encourage": {"rate": 134, "volume": 1.0},   # warm nudge
    "celebrate": {"rate": 144, "volume": 1.0},   # bright, happy praise
    "soothe": {"rate": 116, "volume": 0.92},     # extra gentle "try again"
}
DEFAULT_TONE = "neutral"

# Clear American English is the easiest base for young children to follow.
_PREFERRED_BASE_HINTS = ("en-us", "/en-us", "gmw/en-us")

# Names that reliably map to a pleasant female voice across platforms.
_FEMALE_NAME_HINTS = (
    "female", "zira", "samantha", "victoria", "karen", "tessa",
    "fiona", "moira", "serena", "allison", "ava", "susan", "hazel",
    "annie", "alicia", "linda", "f3", "f4", "+f",
)


@dataclass
class _Utterance:
    text: str
    rate: int
    volume: float


class TextToSpeech:
    def __init__(self, enabled: bool = True, rate: int = 150) -> None:
        self._enabled = enabled
        self._rate = rate
        self._queue: "Queue[_Utterance | None]" = Queue()
        self._engine: Any = None
        self._worker: threading.Thread | None = None
        self._available = False
        # Resolved at init: a base female voice id and whether it is an eSpeak
        # voice that accepts "+variant" suffixes for timbre tuning.
        self._voice_base: str | None = None
        self._voice_id: str | None = None
        self._espeak_like = False
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
            self._select_female_voice()
            self._engine.setProperty("rate", self._rate)
            try:
                self._engine.setProperty("volume", 1.0)
            except Exception:
                pass
            self._available = True
            self._worker = threading.Thread(target=self._run_worker, daemon=True, name="lumi-tts")
            self._worker.start()
        except Exception as error:
            self._engine = None
            self._available = False
            print(f"[Lumi Voice] TTS init failed safely: {error}")

    def _select_female_voice(self) -> None:
        """Pick the warmest available female voice and remember how to tune it."""
        engine = self._engine
        if engine is None:
            return
        try:
            voices = engine.getProperty("voices") or []
        except Exception:
            voices = []

        chosen_id: str | None = None
        # 1) An already-female voice (Windows/macOS expose gender/name).
        for voice in voices:
            name = (getattr(voice, "name", "") or "").lower()
            gender = str(getattr(voice, "gender", "") or "").lower()
            if gender == "female" or any(hint in name for hint in _FEMALE_NAME_HINTS):
                chosen_id = getattr(voice, "id", None)
                break
        # 2) Prefer clear American English (eSpeak-NG) we can feminize.
        if chosen_id is None:
            chosen_id = self._find_voice(voices, _PREFERRED_BASE_HINTS)
        # 3) Any English voice as a last resort.
        if chosen_id is None:
            chosen_id = self._find_voice(voices, ("english", "/en", "en-", "en_"))

        self._voice_base = chosen_id
        vid_l = (chosen_id or "").lower()
        # eSpeak/eSpeak-NG ids look like 'english-us', 'gmw/en-US', 'en-us'.
        self._espeak_like = bool(chosen_id) and (
            "espeak" in vid_l
            or "english" in vid_l
            or "/en" in vid_l
            or vid_l.startswith("en")
        ) and "+" not in vid_l

        self._voice_id = self._resolve_female_voice_id()
        self._apply_voice(self._voice_id)

    @staticmethod
    def _find_voice(voices: list[Any], hints: tuple[str, ...]) -> str | None:
        for voice in voices:
            vid = (getattr(voice, "id", "") or "").lower()
            name = (getattr(voice, "name", "") or "").lower()
            if any(hint in vid or hint in name for hint in hints):
                return getattr(voice, "id", None)
        return None

    def _resolve_female_voice_id(self) -> str | None:
        """Resolve base voice + the best warm female variant eSpeak accepts."""
        if not self._voice_base:
            return None
        if not self._espeak_like:
            return self._voice_base
        for variant in FEMALE_VARIANT_FALLBACKS:
            candidate = f"{self._voice_base}+{variant}"
            try:
                self._engine.setProperty("voice", candidate)
                return candidate
            except Exception:
                continue
        return self._voice_base

    def _apply_voice(self, voice_id: str | None) -> None:
        if voice_id is None or self._engine is None:
            return
        try:
            self._engine.setProperty("voice", voice_id)
        except Exception:
            try:
                self._engine.setProperty("voice", self._voice_base)
            except Exception:
                pass

    def _run_worker(self) -> None:
        while True:
            try:
                item = self._queue.get(timeout=0.2)
            except Empty:
                continue

            if item is None:
                break

            if not self._enabled or self._engine is None:
                continue

            try:
                self._engine.setProperty("rate", item.rate)
                try:
                    self._engine.setProperty("volume", item.volume)
                except Exception:
                    pass
                self._engine.say(item.text)
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

    def speak(self, text: str, tone: str = DEFAULT_TONE) -> bool:
        """Queue a line. `tone` adapts prosody to context (see TONE_PRESETS)."""
        cleaned_text = str(text).strip()
        if not cleaned_text:
            return False
        if not self._enabled:
            return False
        if not self._available:
            print(f"[Lumi Voice] TTS unavailable, skipped speech.")
            return False
        preset = TONE_PRESETS.get(str(tone), TONE_PRESETS[DEFAULT_TONE])
        self._queue.put(
            _Utterance(
                text=cleaned_text,
                rate=int(preset.get("rate", self._rate)),
                volume=float(preset.get("volume", 1.0)),
            )
        )
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
