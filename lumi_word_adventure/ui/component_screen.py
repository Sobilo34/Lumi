"""Base class for programmatic screens (no PNG backgrounds)."""
from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.hitboxes import Hitbox
from ui.scene_view import SceneView


class ComponentScreen:
    def __init__(
        self,
        hitboxes: list[Hitbox],
        render_fn: Callable[[pygame.Surface, SceneView], None],
        view_fn: Callable[[], SceneView],
    ) -> None:
        self.hitboxes = hitboxes
        self._render_fn = render_fn
        self._view_fn = view_fn

    def draw(self, screen: pygame.Surface, debug_hitboxes: bool = False) -> None:
        self._render_fn(screen, self._view_fn())
        for hitbox in self.hitboxes:
            hitbox.draw(screen, debug_hitboxes)

    def handle_click(self, position: tuple[int, int]) -> Hitbox | None:
        for hitbox in self.hitboxes:
            if hitbox.contains(position):
                return hitbox
        return None

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hitbox = self.handle_click(event.pos)
            if hitbox is not None:
                return hitbox.target or hitbox.action
        return None

    def update(self) -> None:
        return None
