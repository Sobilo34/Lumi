"""Image-chunk screen: layered PNGs from assets/ui_chunks/ + dynamic values."""
from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.chunk_composer import ChunkComposer
from ui.chunk_manifest import ScreenChunkSpec
from ui.hitboxes import Hitbox
from ui.scene_view import SceneView


class ChunkScreen:
    def __init__(
        self,
        spec: ScreenChunkSpec,
        hitboxes: list[Hitbox],
        composer: ChunkComposer,
        view_fn: Callable[[], SceneView],
    ) -> None:
        self.spec = spec
        self.hitboxes = hitboxes
        self._composer = composer
        self._view_fn = view_fn

    def draw(self, screen: pygame.Surface, debug_hitboxes: bool = False) -> None:
        view = self._view_fn()
        view.screen_id = self.spec.screen_id
        self._composer.compose(screen, self.spec, view)
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
