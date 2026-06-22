"""Interactive Writing Castle screen with mouse drawing support."""
from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.component_screen import ComponentScreen
from ui.hitboxes import Hitbox
from ui.scene_view import SceneView
from ui.writing_layout import WRITING_BOARD_RECT


DrawEventHandler = Callable[[pygame.event.Event], bool]


class WritingCastleScreen(ComponentScreen):
    """Component screen that forwards pointer events inside the draw board."""

    def __init__(
        self,
        hitboxes: list[Hitbox],
        render_fn: Callable[[pygame.Surface, SceneView], None],
        view_fn: Callable[[], SceneView],
        *,
        draw_handler: DrawEventHandler | None = None,
    ) -> None:
        super().__init__(hitboxes, render_fn, view_fn)
        self._draw_handler = draw_handler

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self._draw_handler is not None and self._draw_handler(event):
            return None
        return super().handle_event(event)

    def board_contains(self, position: tuple[int, int]) -> bool:
        return WRITING_BOARD_RECT.collidepoint(position)
