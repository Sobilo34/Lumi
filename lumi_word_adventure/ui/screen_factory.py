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
from ui.scene_view import SceneView
from ui.screens import create_screen_with_hitboxes


def create_game_screen(
    screen_id: str,
    hitboxes: list[Hitbox],
    registry: ScreenRegistry,
    asset_manager: AssetManager,
    view_fn: Callable[[], SceneView],
    *,
    prefer_procedural: bool = False,
) -> ChunkScreen | object:
    fallback = registry.get_image_filename(screen_id)
    spec = get_screen_spec(screen_id, fallback_image=fallback)
    composer = ChunkComposer(asset_manager)

    if prefer_procedural:
        return create_component_screen(screen_id, hitboxes, view_fn)

    # Image-first: chunk layers when present, otherwise full reference_interfaces PNG.
    return ChunkScreen(spec, hitboxes, composer, view_fn)
