#!/usr/bin/env python3
"""Install Letter Island assets: static bg, find prompts A–Z, letter tiles."""
from __future__ import annotations

import shutil
import string
import sys
from pathlib import Path

import pygame

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from engine.asset_manager import _trim_flat_backdrop, write_shipped_assets_marker  # noqa: E402

ASSETS = Path("/home/bilal/.cursor/projects/home-bilal-bilal-projects-Learning-AIU-python-Lumi/assets")
DEST = PROJECT / "assets" / "ui_chunks" / "letter_island_game"
REF = PROJECT.parent / "reference_interfaces"

# Static gameplay background (empty board — no find text or letter options).
BACKGROUND_UUID = "86df1731-ec95-463f-83f0-3d3b42c202ca"
SUCCESS_BACKGROUND_UUID = "c459dc81-ba6f-43ca-9a18-6cb76b0fcfab"

# "Find X" prompt PNGs (verified letter → uuid).
FIND_PROMPTS: dict[str, str] = {
    "A": "4433000a-35b5-4add-84ef-7d565b38aba9",
    "B": "16193ba7-b1ec-4aee-a452-cdeb652c7f7b",
    "C": "32d77f03-7133-4939-8e76-9338b39638ea",
    "D": "b47a3808-46d2-453d-b297-cfaaf96a76da",
    "E": "2b4df08d-0f65-4ec3-83a9-fe1c288ebc35",
    "F": "07f61f19-4edd-4aa4-981a-9eb615865fdf",
    "G": "8421e8a2-7669-42ff-ab3e-0ac42d41c4a2",
    "H": "82d1bacd-b413-435c-9f48-d122b6107ef7",
    "I": "7f8f4cf1-c463-4aae-aa70-f99dab4669d4",
    "J": "9c627b41-2472-4ed5-8097-83b45bd419de",
    "K": "75e56736-a5fe-4f3a-9aff-4c6ff6b764d2",
    "L": "ad31777b-9012-4caa-a198-e16bcd89de85",
    "M": "4c5fe00c-bd00-4461-a71d-26963815616e",
    "N": "a3795137-da43-405f-979e-dfc5039d116a",
    "O": "6d252578-2b42-47bc-83eb-5b12416a9029",
    "P": "e53f0c05-2c5d-4e4e-8f32-3b60eb475794",
    "Q": "7e836bf4-88be-46e9-9dc1-d725f4bcd82a",
    "R": "31be3f60-8b22-423c-abed-3906f69a600f",
    "S": "02ad49a0-117a-4748-9b99-fcc55d9fa3d4",
    "T": "3d43df29-b1d0-422b-ab86-3e112811653e",
    "U": "ca0fbebf-2147-44f1-a1cb-4c11e13a16ed",
    "V": "2e663b07-410d-4b09-a4db-9eaee163037e",
    "W": "c92a53d9-daf9-4693-84af-ab8a2fcbb0d5",
    "X": "75751cdb-f6f4-47c6-a9fe-1512f62d1060",
    "Y": "e863d00c-fb0c-4223-8483-f372007bf74a",
    "Z": "eae80c66-584e-49ee-9e56-fed6cb88100b",
}

PORTRAIT_LETTERS: dict[str, tuple[str, str]] = {
    letter: (f"{ids[0]}", f"{ids[1]}")
    for letter, ids in zip(
        string.ascii_uppercase[:10],
        [
            ("950a6acb-cafc-4187-8ae3-0c4b8a487288", "c7eef057-08db-4d1d-99bb-db1ad411b7a8"),
            ("377f97cc-007d-4a17-8190-21cc750eb476", "1ff0f0a1-c99c-427a-985c-2a99a5fc3fcb"),
            ("39bb8097-77d3-4eb1-93eb-9fe6dd5c3498", "b8a5e646-5854-4919-88c3-61993903ed85"),
            ("26f68790-6585-4156-bcc7-4a70d0dce531", "b8fd4033-78fb-4471-8d93-cf121afdea37"),
            ("78be80a0-68d5-4a5c-aeb6-75b3c8bc0afa", "af0abd5b-1c71-4d81-9fc5-dc62bf13d928"),
            ("2c6dae34-2195-4896-a6e5-c50896cf68dc", "3bc6bbf1-f002-4695-a1c8-2a2bd14be54a"),
            ("9096701c-8ca6-4f15-9919-5f16ed2cbc1e", "98efcd27-6047-406c-ae73-e62f653df568"),
            ("bc119d91-46fc-43af-a052-931bc70c3a31", "09d61861-39eb-4eda-a338-32cee4e897f3"),
            ("4a2192c3-da14-40f2-9b2e-43ff3f81819e", "09d8c2b5-bf77-4d54-a436-79710d23005a"),
            ("1a903a05-3fed-4206-b7f5-fcecae7f4921", "de047497-e70d-4be8-991c-09eb687939e1"),
        ],
    )
}

SQUARE_LETTERS: dict[str, tuple[str, str]] = {
    letter: (sel, norm)
    for letter, sel, norm in [
        ("K", "54f06226-eb83-4e6e-8c8b-6323de6c08a1", "4fc76415-a6d8-435b-8b78-22d92c9b0b05"),
        ("L", "9721a95b-18af-4e34-b84d-69f1a53bfe9c", "1fdfdcb2-53a9-4e61-9b3a-cbb21f05dedb"),
        ("M", "e44a4652-ce04-4cc1-b139-4232744d6e73", "134108ff-01bb-4d9d-a0d7-7d62462674ac"),
        ("N", "f2ef0623-3589-4998-9db6-d89eac74d040", "0017e2b9-80aa-469b-b691-9568d16c9dac"),
        ("O", "a491a234-f87e-4084-9ab2-ff7657b1def6", "73e8d32f-df7f-4091-8b09-137ac570f113"),
        ("P", "b88ee22a-652f-4caa-bbc7-5a37f10812ea", "84291da8-31a3-4664-9060-be0db5684618"),
        ("Q", "4b7123f7-eb0b-41a5-9c4d-87cb9ef2e08c", "9287367c-70a1-4168-abf6-a8b56eb0a8e0"),
        ("R", "2a25fddc-b8f1-47f5-bfeb-ea27afa65a54", "a890560e-d0c6-4a0f-8089-86fb2f96c3d6"),
        ("S", "e8b0f879-b0f2-42f4-bb3a-1311f6337d1f", "bf6ec95d-30af-4f27-b548-3dbbb53ca339"),
        ("T", "f3716ad8-d182-4309-b1f1-3b92c5e64a22", "194a4d27-8982-419a-a4c4-cd010a6c2855"),
        ("U", "644367b6-133d-40ff-979f-f2bf086f8df7", "8492e72e-3102-4a91-abab-b8ac5d5167f1"),
        ("V", "d0b4e386-c12d-4d7d-9519-198b67572859", "7aa4ff02-1c5e-412e-a20e-70be58f5478c"),
        ("W", "2bdf5ba3-0d22-4fe4-a683-77281f268a08", "5848b4f3-3c3b-43c9-b243-5ea4ce7db013"),
        ("X", "5848b4f3-3c3b-43c9-b243-5ea4ce7db013", "85ee9900-0540-48ef-b048-72561937fe61"),
        ("Y", "9d881fb9-72e0-489c-b5e4-f83f9a040987", "eba77a69-5087-49c4-94ff-f9029de4f990"),
        ("Z", "d35c0f69-f2b4-4759-9512-8174615fb36b", "94b08264-1abf-42c1-9923-972d3f6f9d06"),
    ]
}


def _copy_uuid(uuid: str, dest: Path) -> None:
    source = ASSETS / f"image-{uuid}.png"
    if not source.is_file():
        raise FileNotFoundError(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)


def _trim_assets_in_place(asset_root: Path, relative_dir: str) -> int:
    """Trim letter/find PNGs in place so runtime only needs pygame.image.load."""
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    source_dir = asset_root / relative_dir
    if not source_dir.is_dir():
        return 0
    count = 0
    for png in sorted(source_dir.glob("*.png")):
        image = pygame.image.load(str(png))
        trimmed = _trim_flat_backdrop(image)
        pygame.image.save(trimmed, str(png))
        count += 1
    return count


def _clear_ui_chunks() -> None:
    if not DEST.is_dir():
        return
    for path in DEST.iterdir():
        if path.name in {"letters", "find"}:
            continue
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)


def main() -> None:
    find_dir = DEST / "find"
    letters_dir = DEST / "letters"
    if find_dir.exists():
        shutil.rmtree(find_dir)
    if letters_dir.exists():
        shutil.rmtree(letters_dir)
    legacy_trim = DEST / ".trim_cache"
    if legacy_trim.exists():
        shutil.rmtree(legacy_trim)
    _clear_ui_chunks()
    DEST.mkdir(parents=True, exist_ok=True)
    REF.mkdir(parents=True, exist_ok=True)

    _copy_uuid(BACKGROUND_UUID, REF / "07_letter_island_gameplay.png")
    _copy_uuid(SUCCESS_BACKGROUND_UUID, REF / "08_letter_correct_feedback.png")

    for letter, uuid in FIND_PROMPTS.items():
        _copy_uuid(uuid, find_dir / f"{letter.lower()}.png")

    for letter, (sel_id, norm_id) in PORTRAIT_LETTERS.items():
        key = letter.lower()
        _copy_uuid(sel_id, letters_dir / f"{key}_selected.png")
        _copy_uuid(norm_id, letters_dir / f"{key}.png")

    for letter, (sel_id, norm_id) in SQUARE_LETTERS.items():
        key = letter.lower()
        _copy_uuid(sel_id, letters_dir / f"{key}_selected.png")
        _copy_uuid(norm_id, letters_dir / f"{key}.png")

    trimmed_letters = _trim_assets_in_place(DEST, "letters")
    trimmed_find = _trim_assets_in_place(DEST, "find")
    write_shipped_assets_marker(DEST.parent, "letter_island_game")

    print(f"Installed Letter Island assets to {DEST}")
    print(f"  Background: {REF / '07_letter_island_gameplay.png'}")
    print(f"  Success bg: {REF / '08_letter_correct_feedback.png'}")
    print(f"  Find prompts: {len(FIND_PROMPTS)}")
    print(f"  Letter tiles: {len(list(letters_dir.glob('*.png')))}")
    print(f"  Pre-trimmed: {trimmed_letters} letters, {trimmed_find} find prompts")


if __name__ == "__main__":
    main()
