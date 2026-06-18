"""Factory wiring every screen to a component renderer."""
from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.component_screen import ComponentScreen
from ui.hitboxes import Hitbox
from ui.scene_view import SceneView
from ui.scenes.renderers import SCENE_RENDERERS


def create_component_screen(
    screen_id: str,
    hitboxes: list[Hitbox],
    view_fn: Callable[[], SceneView],
) -> ComponentScreen:
    render_fn = SCENE_RENDERERS.get(screen_id)
    if render_fn is None:
        raise KeyError(f"No component renderer for screen: {screen_id}")

    def _render(surface: pygame.Surface, view: SceneView) -> None:
        view.screen_id = screen_id
        render_fn(surface, view)

    return ComponentScreen(hitboxes, _render, view_fn)
