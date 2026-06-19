"""Asset loading stability checks."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from config import BABY_PINK, PROJECT_DIR, SCREEN_HEIGHT, SCREEN_WIDTH
from engine.asset_manager import AssetManager


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


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


def test_word_garden_object_chunks_drop_export_padding() -> None:
    source = PROJECT_DIR / "assets" / "ui_chunks" / "word_garden_game" / "objects" / "cat.png"
    if not source.is_file():
        pytest.skip("Word Garden object assets are not installed")

    raw = pygame.image.load(str(source)).convert_alpha()
    manager = AssetManager()
    trimmed = manager.load_chunk("word_garden_game", "objects/cat.png")
    assert trimmed is not None
    assert trimmed.get_width() <= raw.get_width()
    assert trimmed.get_height() <= raw.get_height()


def test_word_garden_prompt_and_object_fit_inside_layout_slots() -> None:
    object_path = PROJECT_DIR / "assets" / "ui_chunks" / "word_garden_game" / "objects" / "cat.png"
    if not object_path.is_file():
        pytest.skip("Word Garden object assets are not installed")

    manager = AssetManager()
    prompt = manager.scaled_word_prompt("word_garden_game", "cat", 109, 26, fit="contain")
    obj = manager.scaled_word_object("word_garden_game", "cat", 182, 227, fit="contain")
    assert prompt is not None
    assert obj is not None
    assert prompt.get_width() <= 109
    assert prompt.get_height() <= 26
    assert obj.get_width() <= 182
    assert obj.get_height() <= 227
