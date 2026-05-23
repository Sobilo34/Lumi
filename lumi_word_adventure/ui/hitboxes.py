"""Transparent hitbox primitives."""
from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class Hitbox:
    name: str
    rect: pygame.Rect
    action: str = ""
    target: str = ""

    def contains(self, position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(position)

    def draw(self, surface: pygame.Surface, debug: bool = False) -> None:
        if not debug:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (255, 0, 0, 70), self.rect, 3)
        surface.blit(overlay, (0, 0))

    @classmethod
    def from_normalized(
        cls,
        name: str,
        screen_size: tuple[int, int],
        x_pct: float,
        y_pct: float,
        w_pct: float,
        h_pct: float,
        action: str = "",
        target: str = "",
    ) -> "Hitbox":
        width, height = screen_size
        rect = pygame.Rect(
            round(width * x_pct),
            round(height * y_pct),
            round(width * w_pct),
            round(height * h_pct),
        )
        return cls(name=name, rect=rect, action=action, target=target)
