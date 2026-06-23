"""E1 end-session celebration flow tests (headless pygame)."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pygame
import pytest

from config import END_SESSION_MESSAGE
from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel
from engine.screen_registry import ScreenRegistry


def e1_demo_profile() -> dict:
    return {
        "child_name": "Player 1",
        "total_stars": 6,
        "attempts": 8,
        "correct_answers": 6,
        "mastered_letters": ["A", "B"],
        "mastered_words": ["dog"],
        "weak_letters": {"B": 2, "D": 1},
        "weak_words": {"cat": 2},
    }


@pytest.fixture()
def headless_engine(tmp_path: Path) -> GameEngine:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    engine = GameEngine(screen)
    profile_path = tmp_path / "player_1.json"
    engine.learner = LearnerModel(profile_path=profile_path, profile_data=e1_demo_profile())
    return engine


def _click_named_hitbox(engine: GameEngine, hitbox_name: str) -> str | None:
    hitboxes = engine.registry.get_hitboxes(engine.state.current_screen_id)
    hitbox = next(box for box in hitboxes if box.name == hitbox_name)
    center = hitbox.rect.center
    clicked = engine.current_screen.handle_click(center)
    if clicked is None:
        return None
    return clicked.target or clicked.action


def test_configure_end_session_generates_and_saves_report(headless_engine: GameEngine) -> None:
    engine = headless_engine
    engine.set_screen("end_session")

    assert engine.state.current_screen_id == "end_session"
    report = engine.state.teacher_report
    assert report is not None
    assert report["stars_earned"] > 0
    assert engine.state.session_end_report_path
    assert Path(engine.state.session_end_report_path).exists()


def test_end_session_speaks_celebration_message(headless_engine: GameEngine) -> None:
    engine = headless_engine
    engine.voice = MagicMock()
    engine.state.voice_enabled = True

    engine.set_screen("end_session")

    args, kwargs = engine.voice.speak.call_args
    assert args[0] == END_SESSION_MESSAGE


def test_progress_view_report_back_routes_to_end_session(headless_engine: GameEngine) -> None:
    engine = headless_engine
    engine.set_screen("progress_complete")
    engine._handle_action("view_report")

    assert engine.state.current_screen_id == "teacher_report"
    assert engine.state.end_session_pending is True

    engine._handle_action("back")
    assert engine.state.current_screen_id == "end_session"
    assert engine.state.end_session_pending is False


def test_teacher_report_home_without_pending_goes_to_main_menu(headless_engine: GameEngine) -> None:
    engine = headless_engine
    engine.set_screen("teacher_report")
    assert engine.state.end_session_pending is False

    engine._handle_action("home")
    assert engine.state.current_screen_id == "main_menu"


def test_end_session_play_again_goes_to_world_map(headless_engine: GameEngine) -> None:
    engine = headless_engine
    engine.set_screen("end_session")

    action = _click_named_hitbox(engine, "Play Again")
    assert action == "world_map"
    engine._handle_action(action)
    assert engine.state.current_screen_id == "world_map"


def test_end_session_view_report_goes_to_teacher_report(headless_engine: GameEngine) -> None:
    engine = headless_engine
    engine.set_screen("end_session")

    action = _click_named_hitbox(engine, "View Report")
    assert action == "teacher_report"
    engine._handle_action(action)
    assert engine.state.current_screen_id == "teacher_report"


def test_finish_session_action_from_teacher_report(headless_engine: GameEngine) -> None:
    engine = headless_engine
    engine.set_screen("teacher_report")
    engine._handle_action("finish_session")

    assert engine.state.current_screen_id == "end_session"
    assert engine.state.end_session_pending is False


def test_end_session_hitboxes_match_expected_targets() -> None:
    registry = ScreenRegistry()
    actions = {box.name: (box.action or box.target) for box in registry.get_hitboxes("end_session")}
    assert actions["Play Again"] == "world_map"
    assert actions["View Report"] == "teacher_report"
