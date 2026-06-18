"""Preload and warm caches for early menu screens during splash."""
from __future__ import annotations

from engine.asset_manager import AssetManager
from engine.screen_registry import ScreenRegistry
from ui.chunk_manifest import ScreenChunkSpec, get_screen_spec
from ui.chunk_screen import ChunkScreen

EARLY_SCREEN_IDS = ("splash_loading", "welcome", "profile_selection")


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
