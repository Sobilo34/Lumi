#!/usr/bin/env python3
"""Install badge unlock background and per-badge icon PNGs."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

ASSETS = Path("/home/bilal/.cursor/projects/home-bilal-bilal-projects-Learning-AIU-python-Lumi/assets")
DEST = PROJECT / "assets" / "ui_chunks" / "badge_unlock"
BADGES_DIR = DEST / "badges"
SHIPPED_MARKER = DEST / ".shipped_ready"

BACKGROUND_FILE = "image-43f2bd2a-abcc-4f20-885f-a4769209654c.png"

BADGE_FILES: dict[str, str] = {
    "badge_a.png": "image-a83acf2f-ef85-465d-9061-e90a64af8e0f.png",
    "badge_b.png": "image-75740d4c-5a1e-436a-a7e4-ba9b677fb02c.png",
    "badge_c.png": "image-ae1049c7-6c8f-448d-801e-d7fcd8a21c7d.png",
    "b_and_d_master.png": "image-d8b3855f-340d-4057-a3c3-7662a4b55fee.png",
    "word_explorer.png": "image-ed18068f-b08d-46b1-94c5-4031d84d6246.png",
    "brave_speaker.png": "image-1f36f077-cf99-45c9-b875-353a0848e246.png",
    "sentence_builder.png": "image-271a10c1-a9c6-42e3-b9e0-6533643b9216.png",
    "great_learner.png": "image-c7b2a05d-31c7-4103-827c-cb82fac983e7.png",
    # Placeholder until a dedicated Letter Island Complete badge is provided.
    "letter_island_complete.png": "image-ae1049c7-6c8f-448d-801e-d7fcd8a21c7d.png",
}


def _copy(src_name: str, dest: Path) -> None:
    src = ASSETS / src_name
    if not src.is_file():
        raise FileNotFoundError(f"Missing asset: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"  -> {dest.relative_to(PROJECT)}")


def main() -> None:
    print(f"Installing badge unlock chunks to {DEST}")
    _copy(BACKGROUND_FILE, DEST / "background.png")
    for dest_name, src_name in BADGE_FILES.items():
        _copy(src_name, BADGES_DIR / dest_name)
    SHIPPED_MARKER.write_text("1\n", encoding="utf-8")
    print(f"  -> {SHIPPED_MARKER.relative_to(PROJECT)}")
    print("Done.")


if __name__ == "__main__":
    main()
