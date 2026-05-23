"""Animation placeholders for non-disruptive overlays."""
from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class Particle:
    position: pygame.Vector2
    velocity: pygame.Vector2
    life: float


class AnimationLayer:
    def update(self, delta_time: float) -> None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        return None
