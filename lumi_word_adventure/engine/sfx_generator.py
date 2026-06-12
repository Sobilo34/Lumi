"""Generate lightweight WAV sound effects when asset files are missing."""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from config import SOUNDS_DIR


def _write_tone(path: Path, frequency: float, duration: float, volume: float = 0.35) -> None:
    sample_rate = 22050
    sample_count = int(sample_rate * duration)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for index in range(sample_count):
            t = index / sample_rate
            envelope = min(1.0, t * 20.0) * max(0.0, 1.0 - (t / duration))
            sample = int(volume * envelope * 32767.0 * math.sin(2.0 * math.pi * frequency * t))
            frames.extend(struct.pack("<h", sample))
        handle.writeframes(frames)


def _write_chime(path: Path) -> None:
    sample_rate = 22050
    duration = 0.45
    sample_count = int(sample_rate * duration)
    freqs = (523.25, 659.25, 783.99)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for index in range(sample_count):
            t = index / sample_rate
            value = sum(math.sin(2.0 * math.pi * freq * t) for freq in freqs)
            envelope = min(1.0, t * 15.0) * max(0.0, 1.0 - (t / duration))
            sample = int(0.12 * envelope * value * 32767.0 / len(freqs))
            frames.extend(struct.pack("<h", sample))
        handle.writeframes(frames)


def generate_default_sfx(output_dir: Path | None = None) -> list[Path]:
    target_dir = Path(output_dir) if output_dir is not None else SOUNDS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    specs = {
        "correct.wav": _write_chime,
        "wrong.wav": lambda path: _write_tone(path, 220.0, 0.25, volume=0.28),
        "star.wav": lambda path: _write_tone(path, 880.0, 0.18, volume=0.3),
        "badge.wav": _write_chime,
    }
    written: list[Path] = []
    for filename, writer in specs.items():
        path = target_dir / filename
        if not path.is_file():
            writer(path)
        written.append(path)
    return written
