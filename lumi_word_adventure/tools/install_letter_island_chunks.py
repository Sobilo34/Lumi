#!/usr/bin/env python3
"""Copy Letter Island chunk PNGs from Cursor assets into assets/ui_chunks/letter_island_game/."""
from __future__ import annotations

import shutil
import string
from pathlib import Path

ASSETS = Path("/home/bilal/.cursor/projects/home-bilal-bilal-projects-Learning-AIU-python-Lumi/assets")
DEST = Path(__file__).resolve().parents[1] / "assets" / "ui_chunks" / "letter_island_game"
PROFILE = Path(__file__).resolve().parents[1] / "assets" / "ui_chunks" / "profile_selection"
WELCOME = Path(__file__).resolve().parents[1] / "assets" / "ui_chunks" / "welcome"

UI_CHUNKS: dict[str, str] = {
    "background.png": "48433057-aeb2-4df2-ade0-491fb3ad86ed",
    "board.png": "73fe7195-7513-4ba6-a37c-b657a18b3000",
    "sign.png": "c1cb3173-64a5-4976-b1d3-2308c3da41ed",
    "hud_profile.png": "bd898187-f422-4bfd-ac55-29fe9b34478f",
    "hud_stars.png": "8a471180-53a1-43ee-98e5-70394801ab57",
    "mascot.png": "7c78b0b2-87d1-4fcc-8481-54cd04575b70",
    "mascot_celebrate.png": "ab9306e1-eee6-4370-b222-b675f2ae640b",
    "mascot_point.png": "7c78b0b2-87d1-4fcc-8481-54cd04575b70",
    "btn_repeat.png": "dca11bc5-e4d5-4cb9-bf03-5915144bb65e",
    "btn_hint.png": "4a41904d-4537-4287-8e7c-e04a2e936b2d",
    "btn_speak.png": "18a3153e-26b5-407b-8d68-d400b56e7dc6",
    "btn_next.png": "95bf23bd-6042-4bd3-a000-abea3209f9f4",
    "btn_try_again.png": "ece4d164-a20c-48ad-a87a-1706ea69a240",
    "speech_great_job.png": "eacb8b99-2c6d-40a1-b1f6-b352596447bf",
    "speech_bubble.png": "ea2ae738-2e69-4c47-b4cc-867563ccf8bc",
}

# Portrait tiles A–J (768×1024)
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

# Square tiles K–Z (1024×1024)
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


def main() -> None:
    letters_dir = DEST / "letters"
    if letters_dir.exists():
        shutil.rmtree(letters_dir)
    DEST.mkdir(parents=True, exist_ok=True)

    for name, uuid in UI_CHUNKS.items():
        _copy_uuid(uuid, DEST / name)

    for src_name, dest_name in (("btn_back.png", "btn_home.png"), ("btn_settings.png", "btn_settings.png")):
        source = PROFILE / src_name
        if source.is_file():
            shutil.copy2(source, DEST / dest_name)

    welcome_mascot = WELCOME / "mascot.png"
    if welcome_mascot.is_file():
        shutil.copy2(welcome_mascot, DEST / "mascot.png")

    for letter, (sel_id, norm_id) in PORTRAIT_LETTERS.items():
        key = letter.lower()
        _copy_uuid(sel_id, letters_dir / f"{key}_selected.png")
        _copy_uuid(norm_id, letters_dir / f"{key}.png")

    for letter, (sel_id, norm_id) in SQUARE_LETTERS.items():
        key = letter.lower()
        _copy_uuid(sel_id, letters_dir / f"{key}_selected.png")
        _copy_uuid(norm_id, letters_dir / f"{key}.png")

    print(f"Installed Letter Island chunks to {DEST}")
    print(f"  UI files: {len(UI_CHUNKS)}")
    print(f"  Letter tiles: {len(list(letters_dir.glob('*.png')))}")


if __name__ == "__main__":
    main()
