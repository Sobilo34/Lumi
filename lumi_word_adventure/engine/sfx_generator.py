"""Generate gentle, pleasant WAV sound effects (kid-friendly, never harsh).

The sounds are synthesised from soft bell-like tones (fundamental + a couple of
quiet harmonics) with smooth attack/release envelopes so there are no clicks or
buzzy edges. A small ``SFX_VERSION`` marker lets us refresh shipped audio when
the recipe improves.
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from config import SOUNDS_DIR

SAMPLE_RATE = 22050
# Bump when the synthesis recipe changes so old WAVs get regenerated.
SFX_VERSION = "2"
_VERSION_MARKER = ".sfx_version"


def _bell_sample(frequency: float, t: float) -> float:
    """A warm bell-ish tone: fundamental plus soft, quieter harmonics."""
    return (
        1.00 * math.sin(2.0 * math.pi * frequency * t)
        + 0.32 * math.sin(2.0 * math.pi * frequency * 2.0 * t)
        + 0.14 * math.sin(2.0 * math.pi * frequency * 3.0 * t)
    )


def _envelope(t: float, duration: float, *, attack: float = 0.012) -> float:
    """Smooth attack, exponential bell-like decay (no clicks)."""
    if t < 0 or t > duration:
        return 0.0
    attack_gain = min(1.0, t / max(1e-4, attack))
    decay = math.exp(-3.2 * (t / max(1e-4, duration)))
    return attack_gain * decay


def _write_sequence(
    path: Path,
    notes: list[tuple[float, float, float, float]],
    *,
    total: float,
    volume: float = 0.5,
) -> None:
    """Render notes = [(frequency, start_s, duration_s, gain)] to a mono WAV."""
    sample_count = int(SAMPLE_RATE * total)
    frames = bytearray()
    for index in range(sample_count):
        t = index / SAMPLE_RATE
        value = 0.0
        for frequency, start, duration, gain in notes:
            local = t - start
            if 0.0 <= local <= duration:
                value += gain * _bell_sample(frequency, local) * _envelope(local, duration)
        # Soft-clip to keep it gentle even if notes overlap.
        value = math.tanh(value * 0.9)
        sample = int(max(-1.0, min(1.0, value * volume)) * 32767.0)
        frames.extend(struct.pack("<h", sample))
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(frames)


# Note frequencies (equal temperament).
C5, D5, E5, G5, A5 = 523.25, 587.33, 659.25, 783.99, 880.00
C6, E6, G6, C7 = 1046.50, 1318.51, 1567.98, 2093.00
G4, A4, F4 = 392.00, 440.00, 349.23


def _write_correct(path: Path) -> None:
    """Cheerful ascending sparkle arpeggio."""
    notes = [
        (C5, 0.00, 0.30, 0.55),
        (E5, 0.10, 0.30, 0.55),
        (G5, 0.20, 0.34, 0.60),
        (C6, 0.30, 0.40, 0.65),
        (E6, 0.44, 0.34, 0.30),  # gentle shimmer on top
    ]
    _write_sequence(path, notes, total=0.85, volume=0.5)


def _write_badge_fanfare(path: Path) -> None:
    """Triumphant little fanfare with a shimmering tail."""
    notes = [
        (G4, 0.00, 0.26, 0.55),
        (C5, 0.16, 0.28, 0.58),
        (E5, 0.32, 0.30, 0.60),
        (G5, 0.48, 0.34, 0.62),
        # Held major chord finish.
        (C6, 0.66, 0.70, 0.62),
        (E6, 0.66, 0.70, 0.42),
        (G6, 0.70, 0.66, 0.30),
        (C7, 0.84, 0.52, 0.20),  # sparkle
    ]
    _write_sequence(path, notes, total=1.45, volume=0.5)


def _write_star(path: Path) -> None:
    """Light twinkle for a perfect 3-star answer."""
    notes = [
        (C6, 0.00, 0.18, 0.5),
        (E6, 0.08, 0.18, 0.5),
        (G6, 0.16, 0.22, 0.55),
        (C7, 0.24, 0.26, 0.4),
    ]
    _write_sequence(path, notes, total=0.55, volume=0.45)


def _write_wrong(path: Path) -> None:
    """Soft, kind 'try again' — two mellow descending notes, never harsh."""
    notes = [
        (A4, 0.00, 0.26, 0.5),
        (F4, 0.18, 0.34, 0.5),
    ]
    _write_sequence(path, notes, total=0.6, volume=0.4)


_SPECS = {
    "correct.wav": _write_correct,
    "wrong.wav": _write_wrong,
    "star.wav": _write_star,
    "badge.wav": _write_badge_fanfare,
}


def _version_is_current(target_dir: Path) -> bool:
    marker = target_dir / _VERSION_MARKER
    return marker.is_file() and marker.read_text(encoding="utf-8").strip() == SFX_VERSION


def _write_version(target_dir: Path) -> None:
    (target_dir / _VERSION_MARKER).write_text(f"{SFX_VERSION}\n", encoding="utf-8")


def generate_default_sfx(output_dir: Path | None = None) -> list[Path]:
    target_dir = Path(output_dir) if output_dir is not None else SOUNDS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    refresh = not _version_is_current(target_dir)
    written: list[Path] = []
    for filename, writer in _SPECS.items():
        path = target_dir / filename
        if refresh or not path.is_file():
            writer(path)
        written.append(path)
    if refresh:
        _write_version(target_dir)
    return written
