"""Generate lightweight WAV sound effects for Lumi (run once if assets are missing)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import SOUNDS_DIR
from engine.sfx_generator import generate_default_sfx


if __name__ == "__main__":
    for path in generate_default_sfx(SOUNDS_DIR):
        print(f"Generated: {path}")
