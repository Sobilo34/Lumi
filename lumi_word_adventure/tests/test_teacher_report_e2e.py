"""End-to-end Your Report flow tests (headless pygame)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel
from engine.screen_registry import ScreenRegistry
from reports.report_generator import SCREEN_BD_PRACTICE, SCREEN_WORD_GARDEN, generate_report


def b4_demo_profile() -> dict:
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
    engine.learner = LearnerModel(profile_path=profile_path, profile_data=b4_demo_profile())
    return engine


def _click_named_hitbox(engine: GameEngine, hitbox_name: str) -> str | None:
    hitboxes = engine.registry.get_hitboxes("teacher_report")
    hitbox = next(box for box in hitboxes if box.name == hitbox_name)
    center = hitbox.rect.center
    clicked = engine.current_screen.handle_click(center)
    if clicked is None:
        return None
    return clicked.target or clicked.action


def test_open_your_report_builds_live_report(headless_engine: GameEngine) -> None:
    engine = headless_engine
    engine.set_screen("teacher_report")

    assert engine.state.current_screen_id == "teacher_report"
    report = engine.state.teacher_report
    assert report is not None
    assert report["stars_earned"] > 0
    assert report["attempts"] > 0
    assert report["correct_answers"] > 0
    assert report["accuracy_percent"] == 75
    assert report["weak_letters"] == {"B": 2, "D": 1}
    assert report["weak_words"] == {"cat": 2}
    assert report["needs_practice"] == "Letter B (2), Word: Cat (2)"
    assert report["recommended_screen_id"] == SCREEN_BD_PRACTICE
    assert Path(report["session_report_path"]).exists()


def test_home_returns_to_main_menu(headless_engine: GameEngine) -> None:
    engine = headless_engine
    engine.set_screen("teacher_report")

    clicked = _click_named_hitbox(engine, "Home")
    assert clicked == "home"
    engine._handle_action(clicked)
    assert engine.state.current_screen_id == "main_menu"


def test_word_garden_recommendation_when_bd_not_weak_enough(tmp_path: Path) -> None:
    profile = {
        "child_name": "Player 1",
        "total_stars": 4,
        "attempts": 5,
        "correct_answers": 3,
        "weak_letters": {"B": 1, "D": 1},
        "weak_words": {"cat": 2},
        "completed_worlds": ["letter_island"],
    }
    report = generate_report(profile, output_path=tmp_path / "word_report.json")
    assert report["recommended_screen_id"] == SCREEN_WORD_GARDEN
    assert report["needs_practice"] == "Letter B, Word: Cat (2)"


def test_teacher_report_hitboxes_match_expected_actions() -> None:
    registry = ScreenRegistry()
    actions = {box.name: (box.action or box.target) for box in registry.get_hitboxes("teacher_report")}
    assert actions == {"Home": "home"}


def test_saved_session_json_round_trip(tmp_path: Path) -> None:
    output_path = tmp_path / "session_report_b4.json"
    report = generate_report(b4_demo_profile(), output_path=output_path)

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["stars_earned"] == report["stars_earned"]
    assert loaded["recommended_next_activity"] == "B/D Practice"
    assert loaded["recommended_screen_id"] == SCREEN_BD_PRACTICE
    assert loaded["needs_practice"] == "Letter B (2), Word: Cat (2)"
