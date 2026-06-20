"""Safe speech-to-text helpers with Vosk-first fallback behavior.

Priority order:
1) Vosk offline recognition (sounddevice stream, or PyAudio stream)
2) SpeechRecognition backend (requires PyAudio + a microphone device)
3) Safe no-op fallback with friendly status messaging
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

VOSK_AVAILABLE = False
VOSK_MODEL_PATH: Optional[str] = None
SD_AVAILABLE = False
sd: Any = None
SR_AVAILABLE = False
sr = None
PYAUDIO_AVAILABLE = False

_MODEL_DIR_NAMES = (
    "vosk-model-small-en-us-0.15",
    "vosk-model-small-en-us-0.22",
    "vosk-model-en-us-0.22",
)

_VOSK_MODEL: Any = None
_LISTEN_SETTLE_SEC = 0.35


def _resolve_vosk_model_path() -> Optional[str]:
    env_model = os.environ.get("VOSK_MODEL_PATH")
    if env_model and os.path.isdir(env_model):
        return env_model

    module_root = Path(__file__).resolve().parent.parent
    repo_root = module_root.parent
    search_roots = (Path.cwd(), module_root, repo_root)

    for model_name in _MODEL_DIR_NAMES:
        for root in search_roots:
            candidate = root / "models" / model_name
            if candidate.is_dir():
                return str(candidate)
        legacy = Path.cwd() / "models" / model_name
        if legacy.is_dir():
            return str(legacy)
    return None


try:
    from vosk import Model, KaldiRecognizer  # type: ignore

    VOSK_MODEL_PATH = _resolve_vosk_model_path()
    VOSK_AVAILABLE = bool(VOSK_MODEL_PATH)
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

_pyaudio_checked = False


def _probe_pyaudio() -> bool:
    """Check PyAudio once, lazily, so broken drivers cannot block import."""
    global PYAUDIO_AVAILABLE, _pyaudio_checked
    if _pyaudio_checked:
        return PYAUDIO_AVAILABLE
    _pyaudio_checked = True
    try:
        import pyaudio  # type: ignore

        probe = pyaudio.PyAudio()
        PYAUDIO_AVAILABLE = int(probe.get_device_count()) > 0
        probe.terminate()
    except Exception:
        PYAUDIO_AVAILABLE = False
    return PYAUDIO_AVAILABLE


def _get_vosk_model() -> Any:
    global _VOSK_MODEL
    if _VOSK_MODEL is not None or not VOSK_MODEL_PATH:
        return _VOSK_MODEL
    try:
        from vosk import Model  # type: ignore

        _VOSK_MODEL = Model(VOSK_MODEL_PATH)
    except Exception as error:
        print(f"[Lumi Voice] Vosk model load failed safely: {error}")
        _VOSK_MODEL = None
    return _VOSK_MODEL


def _collect_vosk_text(recognizer: Any, *, final: bool = False) -> str:
    raw = recognizer.FinalResult() if final else recognizer.Result()
    try:
        parsed = json.loads(raw)
    except Exception:
        return ""
    return str(parsed.get("text") or "").strip()


def _listen_vosk_sounddevice(timeout: int) -> Optional[str]:
    if not SD_AVAILABLE or sd is None:
        return None
    model = _get_vosk_model()
    if model is None:
        return None
    try:
        from vosk import KaldiRecognizer  # type: ignore
        import queue

        samplerate = 16000
        blocksize = 8000
        recognizer = KaldiRecognizer(model, samplerate)
        audio_queue: queue.Queue[bytes] = queue.Queue()

        def _callback(indata: Any, frames: int, time_info: Any, status: Any) -> None:
            audio_queue.put(bytes(indata))

        collected: list[str] = []
        deadline = time.time() + max(1, timeout)
        with sd.RawInputStream(
            samplerate=samplerate,
            blocksize=blocksize,
            dtype="int16",
            channels=1,
            callback=_callback,
        ):
            time.sleep(_LISTEN_SETTLE_SEC)
            while time.time() < deadline:
                try:
                    chunk = audio_queue.get(timeout=0.12)
                except queue.Empty:
                    continue
                if recognizer.AcceptWaveform(chunk):
                    part = _collect_vosk_text(recognizer)
                    if part:
                        collected.append(part)
        final = _collect_vosk_text(recognizer, final=True)
        if final:
            collected.append(final)
        text = " ".join(collected).strip()
        return text or None
    except Exception as error:
        print(f"[Lumi Voice] Vosk sounddevice listen failed safely: {error}")
        return None


def _listen_vosk_pyaudio(timeout: int) -> Optional[str]:
    if not _probe_pyaudio():
        return None
    model = _get_vosk_model()
    if model is None:
        return None
    try:
        import pyaudio  # type: ignore
        from vosk import KaldiRecognizer  # type: ignore

        samplerate = 16000
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=samplerate,
            input=True,
            frames_per_buffer=8000,
        )
        recognizer = KaldiRecognizer(model, samplerate)
        collected: list[str] = []
        try:
            stream.start_stream()
            time.sleep(_LISTEN_SETTLE_SEC)
            deadline = time.time() + max(1, timeout)
            while time.time() < deadline:
                data = stream.read(4000, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    part = _collect_vosk_text(recognizer)
                    if part:
                        collected.append(part)
            final = _collect_vosk_text(recognizer, final=True)
            if final:
                collected.append(final)
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
        text = " ".join(collected).strip()
        return text or None
    except Exception as error:
        print(f"[Lumi Voice] Vosk PyAudio listen failed safely: {error}")
        return None


def _vosk_ready() -> bool:
    return bool(VOSK_AVAILABLE and VOSK_MODEL_PATH and (SD_AVAILABLE or _probe_pyaudio()))


def _speech_recognition_ready() -> bool:
    if not SR_AVAILABLE or sr is None or not _probe_pyaudio():
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
            backend = "Vosk offline"
            if SD_AVAILABLE:
                backend += " (sounddevice)"
            else:
                backend += " (PyAudio)"
            return f"Voice ready ({backend})."
        if _speech_recognition_ready():
            return "Voice ready (SpeechRecognition)."
        if VOSK_AVAILABLE and VOSK_MODEL_PATH and not _probe_pyaudio():
            return "Microphone driver is not ready. You can still tap answers."
        if SR_AVAILABLE and not _probe_pyaudio():
            return "Microphone driver is not ready. You can still tap answers."
        if VOSK_AVAILABLE and not VOSK_MODEL_PATH:
            return "Voice model is not installed. You can still tap answers."
        return "Voice is not ready. You can still tap answers."
    except Exception:
        return "Voice is not ready. You can still tap answers."


def listen_once(timeout: int = 7) -> Optional[str]:
    if not is_available():
        return None

    if _vosk_ready():
        text = _listen_vosk_sounddevice(timeout)
        if text:
            print(f"[Lumi Voice] Vosk heard: {text!r}")
            return text
        text = _listen_vosk_pyaudio(timeout)
        if text:
            print(f"[Lumi Voice] Vosk heard: {text!r}")
            return text

    if _speech_recognition_ready() and sr is not None:
        try:
            recognizer = sr.Recognizer()
            recognizer.dynamic_energy_threshold = True
            recognizer.energy_threshold = max(200, recognizer.energy_threshold)
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.35)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
            try:
                recognize_google = getattr(recognizer, "recognize_google", None)
                if recognize_google is None:
                    return None
                text = recognize_google(audio)
                cleaned = text.strip() or None
                if cleaned:
                    print(f"[Lumi Voice] SpeechRecognition heard: {cleaned!r}")
                return cleaned
            except sr.UnknownValueError:
                print("[Lumi Voice] SpeechRecognition heard nothing clear.")
                return None
            except sr.RequestError as error:
                print(f"[Lumi Voice] SpeechRecognition request failed safely: {error}")
                return None
        except Exception as error:
            print(f"[Lumi Voice] SpeechRecognition listen failed safely: {error}")
            return None

    return None


class SpeechToText:
    """Backward-compatible wrapper for older call sites."""

    def listen(self, timeout: int = 5) -> str:
        return listen_once(timeout=timeout) or ""
