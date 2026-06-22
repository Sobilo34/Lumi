"""Build screens: PNG chunks (preferred) → full reference PNG → procedural fallback."""
from __future__ import annotations

from collections.abc import Callable

from engine.asset_manager import AssetManager
from engine.screen_registry import ScreenRegistry
from ui.chunk_composer import ChunkComposer
from ui.chunk_manifest import get_screen_spec
from ui.chunk_screen import ChunkScreen
from ui.hitboxes import Hitbox
from ui.scene_factory import create_component_screen
from ui.scenes.renderers import SCENE_RENDERERS
from ui.writing_castle_screen import WritingCastleScreen
from ui.scene_view import SceneView
from ui.screens import BaseScreen, create_screen_with_hitboxes

# Full reference PNG only — no chunk layers or dynamic overlays.
IMAGE_ONLY_SCREEN_IDS = frozenset({
    "welcome",
})

# Menu / flow / info screens have no dedicated image components, so they are
# drawn with the procedural component renderers. These paint the shared app
# background and clean vector components on top (kid-friendly, simple to read).
PROCEDURAL_SCREEN_IDS = frozenset({
    "main_menu",
    "world_map",
    "bd_practice",
    "progress_complete",
    "practice_weak_skills",
    "writing_castle_game",
    "teacher_report",
    "settings",
    "microphone_check",
    "end_session",
    "offline_continue",
    "points_page",
})


def create_game_screen(
    screen_id: str,
    hitboxes: list[Hitbox],
    registry: ScreenRegistry,
    asset_manager: AssetManager,
    view_fn: Callable[[], SceneView],
    *,
    prefer_procedural: bool = False,
) -> ChunkScreen | BaseScreen | object:
    fallback = registry.get_image_filename(screen_id)

    if screen_id in IMAGE_ONLY_SCREEN_IDS:
        return create_screen_with_hitboxes(fallback, hitboxes, asset_manager)

    spec = get_screen_spec(screen_id, fallback_image=fallback)
    composer = ChunkComposer(asset_manager)

    if prefer_procedural or screen_id in PROCEDURAL_SCREEN_IDS:
        if screen_id == "writing_castle_game":
            return WritingCastleScreen(
                hitboxes,
                SCENE_RENDERERS[screen_id],
                view_fn,
            )
        return create_component_screen(screen_id, hitboxes, view_fn)

    # Image-first: chunk layers when present, otherwise full reference_interfaces PNG.
    return ChunkScreen(spec, hitboxes, composer, view_fn)
