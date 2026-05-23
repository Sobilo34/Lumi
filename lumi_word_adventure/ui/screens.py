"""Image-backed screen rendering."""
from __future__ import annotations

from pathlib import Path

import pygame

from config import BABY_PINK, DEBUG_HITBOXES, REFERENCE_INTERFACES_DIR, SCREEN_HEIGHT, SCREEN_WIDTH
from engine.asset_manager import AssetManager
from ui.hitboxes import Hitbox


class BaseScreen:
    def __init__(
        self,
        image_path: Path | None = None,
        hitboxes: list[Hitbox] | None = None,
        asset_manager: AssetManager | None = None,
    ) -> None:
        self.image_path = Path(image_path) if image_path is not None else None
        self.hitboxes = hitboxes or []
        self.asset_manager = asset_manager or AssetManager()
        self.image = self._load_background()

    def _load_background(self) -> pygame.Surface:
        if self.image_path is not None and self.image_path.exists():
            return self.asset_manager.load_image(self.image_path.name)
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


def build_screen_from_spec(spec: dict, asset_manager: AssetManager | None = None) -> BaseScreen:
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
    return BaseScreen(image_path=image_path, hitboxes=hitboxes, asset_manager=asset_manager)


def create_temporary_splash_test_screen(asset_manager: AssetManager | None = None) -> BaseScreen:
    splash_image = REFERENCE_INTERFACES_DIR / "01_splash_loading.png"
    return BaseScreen(image_path=splash_image, hitboxes=[], asset_manager=asset_manager)
