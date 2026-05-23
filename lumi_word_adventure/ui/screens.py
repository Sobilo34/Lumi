"""Image-backed screen rendering."""
from __future__ import annotations

import pygame

from config import BABY_PINK, DEBUG_HITBOXES, REFERENCE_INTERFACES_DIR, SCREEN_HEIGHT, SCREEN_WIDTH
from engine.asset_manager import AssetManager
from ui.hitboxes import Hitbox


class BaseScreen:
    def __init__(
        self,
        image_filename: str | None = None,
        hitboxes: list[Hitbox] | None = None,
        asset_manager: AssetManager | None = None,
    ) -> None:
        self.image_filename = image_filename
        self.hitboxes = hitboxes or []
        self.asset_manager = asset_manager or AssetManager()
        self.image = self._load_background()

    def _load_background(self) -> pygame.Surface:
        if self.image_filename is not None:
            return self.asset_manager.load_image(self.image_filename)
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.fill(pygame.Color(BABY_PINK))
        return surface

    def draw(self, screen: pygame.Surface, debug_hitboxes: bool = False) -> None:
        screen.blit(self.image, (0, 0))
        for hitbox in self.hitboxes:
            hitbox.draw(screen, debug_hitboxes or DEBUG_HITBOXES)

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


def create_screen(image_filename: str, asset_manager: AssetManager | None = None) -> BaseScreen:
    return BaseScreen(image_filename=image_filename, hitboxes=[], asset_manager=asset_manager)
