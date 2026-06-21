"""Progress complete screen rendering."""
from __future__ import annotations

import os

import pygame
import pytest

from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel
from ui.scene_view import SceneView
from ui.scenes.renderers import render_progress_complete


@pytest.fixture()
def engine(tmp_path, monkeypatch: pytest.MonkeyPatch) -> GameEngine:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    game = GameEngine(screen)
    game.learner = LearnerModel(profile_path=tmp_path / "player_1.json")
    return game


def test_progress_complete_renders_image_buttons() -> None:
    from pathlib import Path

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()

    btn_dir = Path(__file__).resolve().parents[1] / "assets" / "ui_chunks" / "progress_complete"
    assert (btn_dir / "next_world.png").is_file()
    assert (btn_dir / "practice_again.png").is_file()
    assert (btn_dir / "view_report.png").is_file()

    surface = pygame.Surface((1280, 720))
    view = SceneView(
        screen_id="progress_complete",
        stars_filled=2,
        total_stars=14,
        progress_text="Great work today!",
    )
    render_progress_complete(surface, view)
    assert surface.get_at((640, 360)).a == 255


def test_progress_complete_hitboxes_at_bottom() -> None:
    from engine.screen_registry import ScreenRegistry

    boxes = {box.name: box for box in ScreenRegistry().get_hitboxes("progress_complete")}
    assert boxes["Next World"].rect.y / 720 >= 0.75
    assert boxes["Practice Again"].rect.y / 720 >= 0.75
    assert boxes["View Report"].rect.y / 720 >= 0.75
