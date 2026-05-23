"""Image-backed screen rendering."""
from __future__ import annotations

from pathlib import Path

import pygame

from config import BABY_PINK, REFERENCE_INTERFACES_DIR, SCREEN_HEIGHT, SCREEN_WIDTH
from ui.hitboxes import Hitbox


class ImageScreen:
    def __init__(self, image_path: Path, hitboxes: list[Hitbox]) -> None:
        self.image_path = Path(image_path)
        self.hitboxes = hitboxes
        self.image = self._load_image()

    def _load_image(self) -> pygame.Surface:
        if self.image_path.exists():
            image = pygame.image.load(str(self.image_path))
            if pygame.display.get_surface() and image.get_alpha() is not None:
                image = image.convert_alpha()
            elif pygame.display.get_surface():
                image = image.convert()
            return pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.fill(pygame.Color(BABY_PINK))
        return surface

    def draw(self, screen: pygame.Surface, debug_hitboxes: bool = False) -> None:
        screen.blit(self.image, (0, 0))
        if debug_hitboxes:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for hitbox in self.hitboxes:
                pygame.draw.rect(overlay, (255, 0, 0, 80), hitbox.rect, 3)
            screen.blit(overlay, (0, 0))

    def handle_click(self, position: tuple[int, int]) -> Hitbox | None:
        for hitbox in self.hitboxes:
            if hitbox.contains(position):
                return hitbox
        return None


def build_screen_from_spec(spec: dict) -> ImageScreen:
    image_path = REFERENCE_INTERFACES_DIR / spec["background_image"]
    hitboxes = [
        Hitbox.from_normalized(
            entry.get("name", entry.get("action", "hitbox")),
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            entry["x_pct"],
            entry["y_pct"],
            entry["w_pct"],
            entry["h_pct"],
            action=entry.get("action", ""),
            target=entry.get("target", ""),
        )
        for entry in spec.get("hitboxes_normalized_for_1280x720", [])
    ]
    return ImageScreen(image_path=image_path, hitboxes=hitboxes)
