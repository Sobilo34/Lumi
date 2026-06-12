"""Safe speech-to-text helpers with Vosk-first fallback behavior.

Priority order:
1) Vosk offline recognition (requires a local model and sounddevice)
2) SpeechRecognition backend (requires PyAudio + a microphone device)
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
PYAUDIO_AVAILABLE = False

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

try:
    import pyaudio  # type: ignore

    _probe = pyaudio.PyAudio()
    PYAUDIO_AVAILABLE = int(_probe.get_device_count()) > 0
    _probe.terminate()
except Exception:
    PYAUDIO_AVAILABLE = False


def _vosk_ready() -> bool:
    return bool(VOSK_AVAILABLE and SD_AVAILABLE and VOSK_MODEL_PATH)


def _speech_recognition_ready() -> bool:
    if not SR_AVAILABLE or sr is None or not PYAUDIO_AVAILABLE:
        return False
    try:
        names = sr.Microphone.list_microphone_names()
        return bool(names)
    except Exception:
        return False


def is_available() -> bool:
    try:
        return _vosk_ready() or _speech_recognition_ready()
    except Exception:
        return False


def get_status_message() -> str:
    try:
        if _vosk_ready():
            return "Voice ready (Vosk offline)."
        if _speech_recognition_ready():
            return "Voice ready (SpeechRecognition)."
        if SR_AVAILABLE and not PYAUDIO_AVAILABLE:
            return "Microphone driver is not ready. You can still tap answers."
        if VOSK_AVAILABLE and not VOSK_MODEL_PATH:
            return "Voice model is not installed. You can still tap answers."
        return "Voice is not ready. You can still tap answers."
    except Exception:
        return "Voice is not ready. You can still tap answers."


def listen_once(timeout: int = 5) -> Optional[str]:
    if not is_available():
        return None

    if _vosk_ready():
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

    if _speech_recognition_ready() and sr is not None:
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
