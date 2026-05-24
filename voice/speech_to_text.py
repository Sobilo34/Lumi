"""Safe speech-to-text helpers with Vosk-first, SpeechRecognition fallback.

API:
- listen_once(timeout=5) -> str|None
- is_available() -> bool
- get_status_message() -> str

This module never raises if libraries or hardware are missing; it returns None
from `listen_once` and a friendly status message from `get_status_message()`.
"""
from __future__ import annotations
import os
import json
from typing import Any, Optional

# Detect Vosk availability and model path
VOSK_AVAILABLE = False
VOSK_MODEL_PATH = None
try:
    from vosk import Model, KaldiRecognizer  # type: ignore
    # require user to set VOSK_MODEL_PATH env var or place model under ./models/
    env_path = os.environ.get("VOSK_MODEL_PATH")
    if env_path and os.path.isdir(env_path):
        VOSK_MODEL_PATH = env_path
        VOSK_AVAILABLE = True
    else:
        for candidate in ("models/vosk-model-small-en-us-0.15", "models/vosk-model-small-en-us-0.22", "models/vosk-model-en-us-0.22"):
            if os.path.isdir(candidate):
                VOSK_MODEL_PATH = candidate
                VOSK_AVAILABLE = True
                break
except Exception:
    VOSK_AVAILABLE = False

# sounddevice is optional for recording with Vosk
SD_AVAILABLE = False
sd: Any = None
try:
    import sounddevice as sd  # type: ignore
    SD_AVAILABLE = True
except Exception:
    SD_AVAILABLE = False

# SpeechRecognition fallback
SR_AVAILABLE = False
sr = None
try:
    import speech_recognition as sr_mod  # type: ignore
    sr = sr_mod
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False


def is_available() -> bool:
    """Return True if some speech-to-text backend is usable on this machine.
    Vosk requires both a model path and `sounddevice`; SpeechRecognition needs
    its dependencies (PyAudio) available.
    """
    if VOSK_AVAILABLE and SD_AVAILABLE and VOSK_MODEL_PATH:
        return True
    if SR_AVAILABLE:
        return True
    return False


def get_status_message() -> str:
    if VOSK_AVAILABLE and SD_AVAILABLE and VOSK_MODEL_PATH:
        return "Voice ready (Vosk offline)."
    if SR_AVAILABLE:
        return "Voice ready (SpeechRecognition)."
    return "Voice is not ready. You can still tap answers."


def listen_once(timeout: int = 5) -> Optional[str]:
    """Listen for a short utterance and return recognized text, or None.

    Priority: Vosk offline (if model + sounddevice available) -> SpeechRecognition
    fallback. Any errors or missing deps are swallowed and None is returned.
    """
    # Try Vosk offline first
    if VOSK_AVAILABLE and SD_AVAILABLE and VOSK_MODEL_PATH:
        try:
            # Local import to keep module import cheap when unused
            from vosk import Model, KaldiRecognizer  # type: ignore
            import numpy as np  # type: ignore

            model = Model(VOSK_MODEL_PATH)
            recognizer = KaldiRecognizer(model, 16000)

            duration = int(max(1, timeout))
            samplerate = 16000
            recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
            sd.wait()
            # recording is a numpy array of int16
            data = recording.tobytes()
            if recognizer.AcceptWaveform(data):
                out = recognizer.Result()
            else:
                out = recognizer.FinalResult()
            try:
                parsed = json.loads(out)
                return parsed.get("text") or None
            except Exception:
                return None
        except Exception:
            # fall through to SR fallback
            pass

    # SpeechRecognition fallback (uses microphone + Google online recognizer by default)
    if SR_AVAILABLE and sr is not None:
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.4)
                audio = r.listen(source, timeout=timeout, phrase_time_limit=timeout)
            try:
                recognize_google = getattr(r, "recognize_google", None)
                if recognize_google is None:
                    return None
                return recognize_google(audio)
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                # network / service error
                return None
        except Exception:
            return None

    # Nothing available
    return None
