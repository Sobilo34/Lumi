"""Preload and warm caches for early menu screens during splash."""
from __future__ import annotations

from string import ascii_lowercase

from engine.asset_manager import AssetManager
from engine.screen_registry import ScreenRegistry
from engine.word_garden import get_word_garden_pool
from ui.chunk_manifest import ScreenChunkSpec, get_screen_spec
from ui.chunk_screen import ChunkScreen

EARLY_SCREEN_IDS = ("profile_selection",)

# Full reference PNGs for gameplay screens (loaded via AssetManager.load_image).
GAMEPLAY_REFERENCE_IMAGES: tuple[str, ...] = (
    "07_letter_island_gameplay.png",
    "11_word_garden_gameplay.png",
)

# Screens where leftover preload work can continue without blocking input.
IDLE_PRELOAD_SCREEN_IDS = frozenset({
    "splash_loading",
    "welcome",
    "profile_selection",
    "main_menu",
    "how_to_play",
    "world_map",
    "settings",
    "progress_complete",
})


def collect_chunk_files(spec: ScreenChunkSpec) -> tuple[str, ...]:
    files: set[str] = set()
    for layer in spec.layers:
        if layer.file:
            files.add(layer.file)
    profile_cards = spec.dynamic.get("profile_cards") or {}
    if isinstance(profile_cards, dict):
        frame = str(profile_cards.get("card_frame") or "")
        if frame:
            files.add(frame)
        for slot in profile_cards.get("slots") or []:
            if isinstance(slot, dict):
                avatar = str(slot.get("avatar") or "")
                if avatar:
                    files.add(avatar)
    letter_cards = spec.dynamic.get("letter_cards") or {}
    if isinstance(letter_cards, dict):
        frame = str(letter_cards.get("card_frame") or "")
        if frame:
            files.add(frame)
    return tuple(sorted(files))


def build_gameplay_chunk_queue() -> list[tuple[str, str]]:
    """Chunk paths for Word Garden and Letter Island — cheap assets first."""
    queue: list[tuple[str, str]] = [
        ("word_garden_game", "background.png"),
        ("word_garden_game", "speak_background.png"),
    ]
    word_pool = get_word_garden_pool()
    for word in word_pool:
        queue.append(("word_garden_game", f"prompts/{word}.png"))
    for letter in ascii_lowercase:
        queue.append(("letter_island_game", f"find/{letter}.png"))
        queue.append(("letter_island_game", f"letters/{letter}.png"))
        queue.append(("letter_island_game", f"letters/{letter}_selected.png"))
    queue.append(("letter_island_game", "speak_background.png"))
    for word in word_pool:
        queue.append(("word_garden_game", f"objects/{word}.png"))
    return queue


def preload_item_cost(filename: str) -> int:
    """Relative load cost for spreading preload work across frames."""
    return 1


# Word Garden card draw sizes (matches ui_chunk_manifest slot + scale cache).
WORD_GARDEN_OBJECT_W = 182
WORD_GARDEN_OBJECT_H = 227
WORD_GARDEN_PROMPT_W = 112
WORD_GARDEN_PROMPT_H = 29
WORD_GARDEN_SPEAK_OBJECT_W = 237
WORD_GARDEN_SPEAK_OBJECT_H = 194


def warm_word_garden_draw_cache(asset_manager: AssetManager, word: str) -> None:
    """Pre-scale a word's prompt/object after its PNG chunk is loaded."""
    key = str(word or "").strip().lower()
    if not key:
        return
    asset_manager.scaled_word_prompt(
        "word_garden_game",
        key,
        WORD_GARDEN_PROMPT_W,
        WORD_GARDEN_PROMPT_H,
        fit="contain",
    )
    asset_manager.scaled_word_object(
        "word_garden_game",
        key,
        WORD_GARDEN_OBJECT_W,
        WORD_GARDEN_OBJECT_H,
        fit="contain",
    )
    asset_manager.scaled_word_object(
        "word_garden_game",
        key,
        WORD_GARDEN_SPEAK_OBJECT_W,
        WORD_GARDEN_SPEAK_OBJECT_H,
        fit="contain",
    )


def preload_early_screens(
    asset_manager: AssetManager,
    registry: ScreenRegistry,
    screens: dict[str, object],
) -> None:
    for screen_id in EARLY_SCREEN_IDS:
        spec = get_screen_spec(screen_id, fallback_image=registry.get_image_filename(screen_id))
        asset_manager.preload_screen(screen_id, collect_chunk_files(spec))
        screen = screens.get(screen_id)
        if isinstance(screen, ChunkScreen):
            screen._composer.warm_static(spec)
