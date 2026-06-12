"""Asset loading stability checks."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from config import BABY_PINK, SCREEN_HEIGHT, SCREEN_WIDTH
from engine.asset_manager import AssetManager


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()


def test_missing_reference_image_uses_placeholder(tmp_path: Path) -> None:
    manager = AssetManager(reference_dir=tmp_path)
    surface = manager.load_image("missing_screen.png")

    assert surface.get_size() == (SCREEN_WIDTH, SCREEN_HEIGHT)
    assert surface.get_at((0, 0)) == pygame.Color(BABY_PINK)


def test_existing_reference_image_is_scaled(tmp_path: Path) -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    source = pygame.Surface((200, 100))
    source.fill((10, 20, 30))
    image_path = tmp_path / "01_splash_loading.png"
    pygame.image.save(source, str(image_path))

    manager = AssetManager(reference_dir=tmp_path)
    surface = manager.load_image("01_splash_loading.png")

    assert surface.get_size() == (SCREEN_WIDTH, SCREEN_HEIGHT)
