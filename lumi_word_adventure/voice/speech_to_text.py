"""Safe speech-to-text helpers with Vosk-first fallback behavior.

Priority order:
1) Vosk offline recognition (requires a local model and sounddevice)
2) SpeechRecognition backend (if installed)
3) Safe no-op fallback with friendly status messaging
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

VOSK_AVAILABLE = False
VOSK_MODEL_PATH: Optional[str] = None
SD_AVAILABLE = False
sd: Any = None
SR_AVAILABLE = False
sr = None

try:
    from vosk import Model, KaldiRecognizer  # type: ignore

    env_model = os.environ.get("VOSK_MODEL_PATH")
    if env_model and os.path.isdir(env_model):
        VOSK_MODEL_PATH = env_model
        VOSK_AVAILABLE = True
    else:
        for candidate in (
            "models/vosk-model-small-en-us-0.15",
            "models/vosk-model-small-en-us-0.22",
            "models/vosk-model-en-us-0.22",
        ):
            if os.path.isdir(candidate):
                VOSK_MODEL_PATH = candidate
                VOSK_AVAILABLE = True
                break
except Exception:
    VOSK_AVAILABLE = False

try:
    import sounddevice as sd  # type: ignore

    SD_AVAILABLE = True
except Exception:
    SD_AVAILABLE = False

try:
    import speech_recognition as sr_mod  # type: ignore

    sr = sr_mod
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False


def is_available() -> bool:
    if VOSK_AVAILABLE and SD_AVAILABLE and VOSK_MODEL_PATH:
        return True
    return SR_AVAILABLE


def get_status_message() -> str:
    if VOSK_AVAILABLE and SD_AVAILABLE and VOSK_MODEL_PATH:
        return "Voice ready (Vosk offline)."
    if SR_AVAILABLE:
        return "Voice ready (SpeechRecognition)."
    return "Voice is not ready. You can still tap answers."


def listen_once(timeout: int = 5) -> Optional[str]:
    if VOSK_AVAILABLE and SD_AVAILABLE and VOSK_MODEL_PATH:
        try:
            from vosk import Model, KaldiRecognizer  # type: ignore

            samplerate = 16000
            duration = int(max(1, timeout))
            model = Model(VOSK_MODEL_PATH)
            rec = KaldiRecognizer(model, samplerate)
            recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
            sd.wait()
            data = recording.tobytes()
            if rec.AcceptWaveform(data):
                raw = rec.Result()
            else:
                raw = rec.FinalResult()
            parsed = json.loads(raw)
            return (parsed.get("text") or "").strip() or None
        except Exception:
            pass

    if SR_AVAILABLE and sr is not None:
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
            try:
                recognize_google = getattr(recognizer, "recognize_google", None)
                if recognize_google is None:
                    return None
                text = recognize_google(audio)
                return text.strip() or None
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                return None
        except Exception:
            return None

    return None


class SpeechToText:
    """Backward-compatible wrapper for older call sites."""

    def listen(self, timeout: int = 5) -> str:
        return listen_once(timeout=timeout) or ""
