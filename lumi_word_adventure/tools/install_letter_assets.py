#!/usr/bin/env python3
"""Install letter tile PNGs (A–Z normal + selected) with checkerboard removal."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from engine.letter_tile_bg import knock_out_letter_backdrop  # noqa: E402
LETTERS_DIR = PROJECT_DIR / "assets" / "ui_chunks" / "letter_island_game" / "letters"
CURSOR_ASSETS = Path.home() / ".cursor/projects/home-bilal-bilal-projects-Learning-AIU-python-Lumi/assets"

# User upload order: A–Z normal, then A–Z selected.
SOURCE_FILES: tuple[str, ...] = (
    "image-7e26a255-b82c-45ce-a152-5fefa7675665.png",
    "image-2107478e-2af5-44f3-acdb-1cca67dece66.png",
    "image-fba5bf81-9712-475d-a331-e06270805625.png",
    "image-45ed5b75-fcd9-49b4-a64a-8b7be0a4308a.png",
    "image-d80a4c91-dcb9-4be0-af80-171fd26c58ab.png",
    "image-29d65ec7-35ec-43ce-a8cc-baf6e313d3aa.png",
    "image-5c5519b0-f17b-42de-bdcd-2242429eebca.png",
    "image-c6dbe683-ef4b-46b1-a925-babb2033b98c.png",
    "image-5818ab41-b88f-4726-a3ae-f2aaf2c914e2.png",
    "image-3aa20c6c-651b-42ad-b898-93b13782bdc6.png",
    "image-43188512-fc7f-43bd-93a2-4754f875853d.png",
    "image-9bc139a1-3672-4a71-8b3f-317660587e51.png",
    "image-2930aa7e-709b-4a40-82e7-a12f0df12171.png",
    "image-599298e4-b1ae-4442-b0c9-364e71c269bf.png",
    "image-26227a03-94be-4519-bb17-53450e48d0ec.png",
    "image-1c4bd2de-6c64-4dcc-82ca-f0eac4fdde0c.png",
    "image-dd6762ad-b905-44e6-890f-9219aa342249.png",
    "image-267021e2-72a9-43f0-8ca4-82b5fbc4120f.png",
    "image-7b157bc7-ce09-4efa-a881-e769d542af4a.png",
    "image-38dd7dc8-d113-4a8f-a036-41102db995da.png",
    "image-9ff18355-5e46-4f1e-8fe5-ff4ff1f8258b.png",
    "image-1ee1f03c-86fc-4687-83d1-ad5c296c7f0e.png",
    "image-83590f99-57be-4984-9b44-5daf83f6a173.png",
    "image-463297cf-c99c-45ad-873a-fa4e624ecc59.png",
    "image-d95f818b-12a2-4823-9ef8-d8fd9d8556ab.png",
    "image-06773ed9-3857-4f38-9a23-10d727ef718c.png",
    "image-30e4e905-11a8-4d99-9aea-41c368dd5121.png",
    "image-7ae48ec9-846b-43c9-95ac-c17e59e3191f.png",
    "image-2a5ff664-3b7a-4d45-9e83-f57294d414e6.png",
    "image-0a2b9a54-f04e-4697-ac5f-60bd097e8b2b.png",
    "image-2093447a-39e2-482a-a8fa-321f8f62fb80.png",
    "image-edc3a070-59c4-42f2-85f8-a6c5113a0341.png",
    "image-13761b04-7b5b-4ecd-8104-9250710e77b3.png",
    "image-bc1d9c2e-94ca-4759-b298-8f7368a6b229.png",
    "image-4e59de6b-7c34-4dab-ba5d-1555ed0cb7d3.png",
    "image-c9d5bd48-4f69-4cc6-a2e2-d5c93523a96b.png",
    "image-6eefc89c-78c5-4eaa-a330-4abaf53c091f.png",
    "image-2c87c8f3-869c-4c92-a713-127b99b0f73f.png",
    "image-e23c53c2-aa5a-4f65-9643-0abf28473774.png",
    "image-b0573592-6c47-43d3-a6e5-4e60a335f483.png",
    "image-4733b42c-fd3b-44f4-8d28-9eb4e068cb33.png",
    "image-1c533ea6-8166-485a-abb1-f2243872dc89.png",
    "image-e2b17ad8-f5bc-4459-99f9-65cbe522061b.png",
    "image-c8ed30fe-4c20-43c9-b0bd-431a7c133dbb.png",
    "image-f1888046-7f5a-4dce-ac79-eca70d486c64.png",
    "image-d896617a-f57f-4958-b80d-b64e6291e309.png",
    "image-88d605e8-e741-4fb3-a01a-812956126e97.png",
    "image-81861201-c12c-471b-99b3-0a76775c1c36.png",
    "image-0e639864-9944-45e5-b49f-44d42173bdb2.png",
    "image-144992c1-3de3-4f36-8a57-fa43a7f1824d.png",
    "image-90b8248a-581b-4aae-90fd-bb76e302156d.png",
)

LETTERS = tuple(chr(code) for code in range(ord("A"), ord("Z") + 1))


def _normal_source(index: int) -> Path:
    """Normal tiles from the first 25 uploads: A–X, then Y and Z."""
    if index <= 23:
        return CURSOR_ASSETS / SOURCE_FILES[index]
    if index == 24:
        return CURSOR_ASSETS / SOURCE_FILES[23]
    return CURSOR_ASSETS / SOURCE_FILES[24]


def _selected_source(index: int) -> Path:
    """Selected tiles: SOURCE[25..49] for A–Y, Z uses SOURCE[50]."""
    if index < 25:
        return CURSOR_ASSETS / SOURCE_FILES[index + 25]
    return CURSOR_ASSETS / SOURCE_FILES[50]


def main() -> int:
    if len(SOURCE_FILES) != 51:
        print(f"Expected 51 source images, got {len(SOURCE_FILES)}", file=sys.stderr)
        return 1

    LETTERS_DIR.mkdir(parents=True, exist_ok=True)
    for old in LETTERS_DIR.glob("*.png"):
        old.unlink()

    for index, letter in enumerate(LETTERS):
        normal_src = _normal_source(index)
        selected_src = _selected_source(index)
        key = letter.lower()
        if not normal_src.is_file() or not selected_src.is_file():
            print(f"Missing source for {letter}: {normal_src.name} / {selected_src.name}", file=sys.stderr)
            return 1
        knock_out_letter_backdrop(Image.open(normal_src)).save(LETTERS_DIR / f"{key}.png", compress_level=1)
        knock_out_letter_backdrop(Image.open(selected_src)).save(LETTERS_DIR / f"{key}_selected.png", compress_level=1)
        print(f"  {letter}: {normal_src.name} -> {key}.png, {selected_src.name} -> {key}_selected.png")

    print(f"Installed 52 letter tiles into {LETTERS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
