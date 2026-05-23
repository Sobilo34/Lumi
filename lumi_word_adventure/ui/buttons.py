"""Simple button primitives for future screens."""
from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class Button:
    label: str
    rect: pygame.Rect
    action: str = ""
    target: str = ""

    def contains(self, position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(position)
