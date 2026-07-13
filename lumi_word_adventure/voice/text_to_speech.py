"""Text-to-speech helper with a warm, female, child-friendly voice.

Design goals:
- A gentle FEMALE voice that is pleasing for 2-4 year olds (never a deep,
  "scary" default robot voice).
- Context-adaptive prosody: prompts are calm and clear, praise is bright and
  excited, "try again" is soft and reassuring.
- Fully offline and resilient: if the speech backend is missing we degrade to
  silent no-ops instead of crashing.

pyttsx3 must only be driven from one worker thread. On Windows the engine is
created inside that worker after ``pythoncom.CoInitialize()`` so SAPI/COM audio
works reliably. When pygame mixer is active (game is running), Windows laptops
often block live SAPI output after background music starts — we synthesize to a
short WAV and play it through pygame instead. Never call engine.stop() from the
main/game thread while runAndWait() is active — that deadlocks the app.
"""
from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

try:
    import pyttsx3
except Exception:  # pragma: no cover - dependency may be absent in headless checks
    pyttsx3 = None

_WAV_PLAYBACK: bool | None = None

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
        self._engine_ready = threading.Event()
        self._speaking = threading.Event()
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

    @property
    def is_busy(self) -> bool:
        """True while a line is queued or actively playing."""
        return self._speaking.is_set() or not self._queue.empty()

    def _initialize_engine(self) -> None:
        if pyttsx3 is None:
            self._available = False
            return
        self._worker = threading.Thread(target=self._run_worker, daemon=True, name="lumi-tts")
        self._worker.start()

    def _probe_voice_profile_on_worker(self) -> None:
        """Resolve voice settings without leaving a pyttsx3 engine alive."""
        if pyttsx3 is None:
            return
        probe = pyttsx3.init()
        try:
            try:
                voices = probe.getProperty("voices") or []
            except Exception:
                voices = []
            self._voice_base, self._espeak_like = self._resolve_voice_profile(voices)
            self._voice_id = self._female_voice_id_for_engine(probe)
        finally:
            del probe

    def _init_engine_on_worker(self) -> bool:
        if pyttsx3 is None:
            return False
        try:
            if self._prefer_wav_playback():
                # A persistent engine on the worker thread deadlocks the second
                # save_to_file() on Windows when music uses pygame.mixer.
                self._engine = None
                self._probe_voice_profile_on_worker()
                self._available = True
                self._engine_ready.set()
                print(f"[Lumi Voice] TTS ready (wav) voice={self.voice_label}")
                return True
            self._engine = pyttsx3.init()
            self._select_female_voice()
            self._engine.setProperty("rate", self._rate)
            try:
                self._engine.setProperty("volume", 1.0)
            except Exception:
                pass
            self._available = True
            self._engine_ready.set()
            print(f"[Lumi Voice] TTS ready voice={self.voice_label}")
            return True
        except Exception as error:
            self._engine = None
            self._available = False
            print(f"[Lumi Voice] TTS init failed safely: {error}")
            return False

    def _select_female_voice(self) -> None:
        """Pick the warmest available female voice and remember how to tune it."""
        engine = self._engine
        if engine is None:
            return
        try:
            voices = engine.getProperty("voices") or []
        except Exception:
            voices = []

        self._voice_base, self._espeak_like = self._resolve_voice_profile(voices)
        self._voice_id = self._resolve_female_voice_id()
        self._apply_voice(self._voice_id)

    @classmethod
    def _resolve_voice_profile(cls, voices: list[Any]) -> tuple[str | None, bool]:
        chosen_id: str | None = None
        for voice in voices:
            name = (getattr(voice, "name", "") or "").lower()
            vid = (getattr(voice, "id", "") or "").lower()
            gender = str(getattr(voice, "gender", "") or "").lower()
            if gender == "female" or any(hint in name for hint in _FEMALE_NAME_HINTS):
                if "zira" in name or "en-us" in vid or "en_us" in vid:
                    chosen_id = getattr(voice, "id", None)
                    break
        if chosen_id is None:
            for voice in voices:
                name = (getattr(voice, "name", "") or "").lower()
                gender = str(getattr(voice, "gender", "") or "").lower()
                if gender == "female" or any(hint in name for hint in _FEMALE_NAME_HINTS):
                    chosen_id = getattr(voice, "id", None)
                    break
        if chosen_id is None:
            chosen_id = cls._find_voice(voices, _PREFERRED_BASE_HINTS)
        if chosen_id is None:
            chosen_id = cls._find_voice(voices, ("english", "/en", "en-", "en_"))

        vid_l = (chosen_id or "").lower()
        espeak_like = bool(chosen_id) and (
            "espeak" in vid_l
            or "english" in vid_l
            or "/en" in vid_l
            or vid_l.startswith("en")
        ) and "+" not in vid_l
        return chosen_id, espeak_like

    def _female_voice_id_for_engine(self, engine: Any) -> str | None:
        try:
            voices = engine.getProperty("voices") or []
        except Exception:
            voices = []
        voice_base, espeak_like = self._resolve_voice_profile(voices)
        if not voice_base:
            return None
        if not espeak_like:
            return voice_base
        for variant in FEMALE_VARIANT_FALLBACKS:
            candidate = f"{voice_base}+{variant}"
            try:
                engine.setProperty("voice", candidate)
                return candidate
            except Exception:
                continue
        return voice_base

    def _configure_ephemeral_engine(self, engine: Any, item: _Utterance) -> None:
        voice_id = self._female_voice_id_for_engine(engine)
        if voice_id:
            try:
                engine.setProperty("voice", voice_id)
            except Exception:
                pass
        engine.setProperty("rate", item.rate)
        try:
            engine.setProperty("volume", item.volume)
        except Exception:
            pass

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

    @property
    def voice_label(self) -> str:
        return str(self._voice_id or self._voice_base or "default")

    def _duck_background(self) -> None:
        try:
            from engine import audio_ducking

            audio_ducking.duck("tts")
        except Exception:
            pass

    def _unduck_background(self) -> None:
        try:
            from engine import audio_ducking

            audio_ducking.unduck("tts")
        except Exception:
            pass

    @staticmethod
    def _prefer_wav_playback() -> bool:
        """Windows + pygame: one-shot WAV + winsound avoids SAPI/mixer deadlocks."""
        global _WAV_PLAYBACK
        if _WAV_PLAYBACK is not None:
            return _WAV_PLAYBACK
        if sys.platform != "win32":
            _WAV_PLAYBACK = False
            return False
        try:
            import pygame

            _WAV_PLAYBACK = pygame.mixer.get_init() is not None
        except Exception:
            _WAV_PLAYBACK = False
        return _WAV_PLAYBACK

    def _apply_utterance_properties(self, item: _Utterance) -> None:
        if self._engine is None:
            return
        self._configure_ephemeral_engine(self._engine, item)

    def _synthesize_to_wav(self, item: _Utterance, path: Path) -> None:
        """Synthesize with a fresh engine — pyttsx3 cannot chain save_to_file calls."""
        if pyttsx3 is None:
            raise RuntimeError("pyttsx3 unavailable")
        com_initialized = False
        if sys.platform == "win32":
            try:
                import pythoncom

                pythoncom.CoInitialize()
                com_initialized = True
            except Exception:
                pass
        try:
            engine = pyttsx3.init()
            self._configure_ephemeral_engine(engine, item)
            engine.save_to_file(item.text, str(path))
            engine.runAndWait()
        finally:
            if com_initialized:
                try:
                    import pythoncom

                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    @staticmethod
    def _play_wav_file(path: Path) -> None:
        if sys.platform == "win32":
            import winsound

            flags = winsound.SND_FILENAME | winsound.SND_NODEFAULT
            winsound.PlaySound(str(path), flags)
            return
        import pygame

        sound = pygame.mixer.Sound(str(path))
        channel = pygame.mixer.find_channel(True)
        if channel is None:
            raise RuntimeError("no free pygame mixer channel for TTS")
        channel.play(sound)
        deadline = time.monotonic() + max(2.0, sound.get_length() + 1.5)
        while channel.get_busy() and time.monotonic() < deadline:
            time.sleep(0.03)

    def _playback_via_sapi_ephemeral(self, item: _Utterance) -> None:
        if pyttsx3 is None:
            return
        com_initialized = False
        if sys.platform == "win32":
            try:
                import pythoncom

                pythoncom.CoInitialize()
                com_initialized = True
            except Exception:
                pass
        try:
            engine = pyttsx3.init()
            self._configure_ephemeral_engine(engine, item)
            started = time.monotonic()
            engine.say(item.text)
            engine.runAndWait()
            elapsed = time.monotonic() - started
            if elapsed < 0.12 and len(item.text) > 12:
                raise RuntimeError(
                    f"live SAPI returned too quickly ({elapsed:.2f}s); likely silent on this device"
                )
            print(f"[Lumi Voice] spoke (live): {item.text[:72]!r}")
        finally:
            if com_initialized:
                try:
                    import pythoncom

                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def _playback_via_sapi(self, item: _Utterance) -> None:
        if self._engine is None:
            self._playback_via_sapi_ephemeral(item)
            return
        self._apply_utterance_properties(item)
        started = time.monotonic()
        self._engine.say(item.text)
        self._engine.runAndWait()
        elapsed = time.monotonic() - started
        if elapsed < 0.12 and len(item.text) > 12:
            raise RuntimeError(
                f"live SAPI returned too quickly ({elapsed:.2f}s); likely silent on this device"
            )
        print(f"[Lumi Voice] spoke (live): {item.text[:72]!r}")

    def _playback_via_wav(self, item: _Utterance) -> None:
        fd, path_str = tempfile.mkstemp(suffix=".wav", prefix="lumi-tts-")
        os.close(fd)
        path = Path(path_str)
        try:
            self._synthesize_to_wav(item, path)
            if not path.is_file() or path.stat().st_size < 128:
                raise RuntimeError("TTS did not create a WAV file")
            time.sleep(0.05)
            self._play_wav_file(path)
            print(f"[Lumi Voice] spoke (wav): {item.text[:72]!r}")
        finally:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

    def _playback_utterance(self, item: _Utterance) -> None:
        self._speaking.set()
        try:
            self._duck_background()
            if self._prefer_wav_playback():
                try:
                    self._playback_via_wav(item)
                except Exception as error:
                    print(f"[Lumi Voice] WAV playback failed ({error}); trying live SAPI")
                    self._playback_via_sapi_ephemeral(item)
            else:
                if self._engine is None and not self._init_engine_on_worker():
                    return
                self._playback_via_sapi(item)
        except Exception as error:
            print(f"[Lumi Voice] TTS playback failed safely: {error}")
            self._recover_engine_after_failure()
        finally:
            self._unduck_background()
            self._speaking.clear()

    def _recover_engine_after_failure(self) -> None:
        """Recreate the live SAPI engine after a failed utterance."""
        if self._prefer_wav_playback():
            return
        self._engine = None
        self._available = False
        self._engine_ready.clear()
        if not self._init_engine_on_worker():
            print("[Lumi Voice] TTS recovery failed; speech disabled until restart.")

    def _run_worker(self) -> None:
        com_initialized = False
        if sys.platform == "win32":
            try:
                import pythoncom

                pythoncom.CoInitialize()
                com_initialized = True
            except Exception as error:
                print(f"[Lumi Voice] COM init failed safely: {error}")

        if not self._init_engine_on_worker():
            return

        try:
            while True:
                try:
                    item = self._queue.get(timeout=0.2)
                except Empty:
                    continue

                if item is None:
                    break

                if not self._enabled:
                    continue

                if not self._available and not self._init_engine_on_worker():
                    continue

                self._playback_utterance(item)
        finally:
            if com_initialized:
                try:
                    import pythoncom

                    pythoncom.CoUninitialize()
                except Exception:
                    pass

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
            print("[Lumi Voice] TTS disabled in settings; skipped speech.")
            return False
        if pyttsx3 is None or self._worker is None:
            print("[Lumi Voice] TTS unavailable, skipped speech.")
            return False
        if not self._available and not self._engine_ready.wait(timeout=2.0):
            print("[Lumi Voice] TTS not ready yet, skipped speech.")
            return False
        preset = TONE_PRESETS.get(str(tone), TONE_PRESETS[DEFAULT_TONE])
        self._queue.put(
            _Utterance(
                text=cleaned_text,
                rate=int(preset.get("rate", self._rate)),
                volume=float(preset.get("volume", 1.0)),
            )
        )
        preview = cleaned_text if len(cleaned_text) <= 72 else f"{cleaned_text[:69]}..."
        print(f"[Lumi Voice] queued: {preview!r}")
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
