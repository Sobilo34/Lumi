"""Component-built screens that replace reference PNGs for Letter Island."""
from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.components.letter_island_scene import (
    LetterIslandView,
    render_letter_island_correct,
    render_letter_island_gameplay,
    render_letter_island_mistake,
)
from ui.hitboxes import Hitbox


class ComponentScreen:
    """Screen with programmatic rendering and transparent hitboxes."""

    def __init__(
        self,
        hitboxes: list[Hitbox],
        render_fn: Callable[[pygame.Surface, LetterIslandView], None],
        view_fn: Callable[[], LetterIslandView],
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


def create_letter_island_gameplay_screen(
    hitboxes: list[Hitbox],
    view_fn: Callable[[], LetterIslandView],
) -> ComponentScreen:
    return ComponentScreen(hitboxes, render_letter_island_gameplay, view_fn)


def create_letter_correct_screen(
    hitboxes: list[Hitbox],
    view_fn: Callable[[], LetterIslandView],
) -> ComponentScreen:
    return ComponentScreen(hitboxes, render_letter_island_correct, view_fn)


def create_letter_mistake_screen(
    hitboxes: list[Hitbox],
    view_fn: Callable[[], LetterIslandView],
) -> ComponentScreen:
    return ComponentScreen(hitboxes, render_letter_island_mistake, view_fn)
