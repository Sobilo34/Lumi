"""Letter Island speak screen wiring."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel
from ui.chunk_composer import ChunkComposer
from ui.chunk_manifest import get_screen_spec
from ui.scene_view import SceneView

PROJECT_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture()
def engine(tmp_path: Path) -> GameEngine:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    from engine.settings_manager import SettingsManager

    game = GameEngine(screen)
    game.settings = SettingsManager(settings_path=tmp_path / "settings.json")
    game.learner = LearnerModel(profile_path=tmp_path / "player_1.json")
    game._apply_loaded_settings(game.settings.load_settings())
    return game


def test_letter_island_speak_uses_letter_voice_screen(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.is_stt_ready", lambda: True)

    engine.set_screen("letter_island_game")
    engine.state.current_task_target = "M"
    engine._handle_letter_island_action("voice_or_speak_mode")

    assert engine.state.current_screen_id == "letter_voice_challenge"
    assert engine.state.current_task_target == "M"
    assert engine.state.current_task_prompt == "What letter is this?"


def test_letter_voice_manifest_uses_island_background_and_letter_focus() -> None:
    spec = get_screen_spec("letter_voice_challenge", fallback_image="14_voice_say_apple.png")
    assert spec.asset_root == "letter_island_game"
    assert any(layer.file == "speak_background.png" for layer in spec.layers)
    focus = spec.dynamic.get("say_letter")
    assert focus is not None
    assert focus.get("type") == "letter_focus_png"
    assert focus.get("field") == "target_letter"


def test_letter_voice_renders_normal_letter_tile(engine: GameEngine) -> None:
    speak_bg = PROJECT_DIR / "assets" / "ui_chunks" / "letter_island_game" / "speak_background.png"
    letter_tile = PROJECT_DIR / "assets" / "ui_chunks" / "letter_island_game" / "letters" / "t.png"
    if not speak_bg.is_file() or not letter_tile.is_file():
        pytest.skip("Letter Island speak assets are not installed")

    spec = get_screen_spec("letter_voice_challenge", fallback_image="14_voice_say_apple.png")
    view = SceneView(screen_id="letter_voice_challenge", target_letter="T")
    surface = pygame.Surface((1280, 720))
    ChunkComposer(engine.asset_manager).compose(surface, spec, view)
    assert surface.get_at((640, 300)).a > 0


def test_letter_voice_wrong_shows_try_again_popup(engine: GameEngine) -> None:
    engine.set_screen("letter_voice_challenge")
    engine.state.current_task_target = "T"
    engine._process_letter_voice_capture_result("wrong-letter")
    assert engine.state.current_screen_id == "letter_voice_challenge"
    assert engine.state.answer_popup_kind == "wrong"
    assert engine.state.answer_popup_next_screen == "letter_voice_challenge"


def test_word_voice_wrong_shows_try_again_popup(engine: GameEngine) -> None:
    engine.learner.completed_worlds = ["letter_island"]
    engine.learner.save_profile()
    engine.set_screen("voice_challenge")
    engine.state.current_task_target = "cat"
    engine.state.word_choice_slots = ["cat", "dog", "sun", "ball"]
    engine._process_voice_capture_result("wrong-word")
    assert engine.state.current_screen_id == "voice_challenge"
    assert engine.state.answer_popup_kind == "wrong"
    assert engine.state.answer_popup_next_screen == "voice_challenge"


def test_word_voice_correct_shows_success_popup(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.check_badge_unlocks", lambda profile: [])
    engine.set_screen("voice_challenge")
    engine.state.current_task_target = "cat"
    engine.state.word_choice_slots = ["cat", "dog", "sun", "ball"]
    engine._process_voice_capture_result("cat")
    assert engine.state.current_screen_id == "voice_challenge"
    assert engine.state.answer_popup_kind == "correct"
    assert engine.state.answer_popup_next_screen == "word_garden_game"


def test_word_voice_close_shows_try_again_popup(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine.learner.completed_worlds = ["letter_island"]
    engine.learner.save_profile()
    monkeypatch.setattr("engine.game_engine.check_spoken_answer", lambda spoken, target: "close")
    engine.set_screen("voice_challenge")
    engine.state.current_task_target = "cat"
    engine.state.word_choice_slots = ["cat", "dog", "sun", "ball"]
    engine._process_voice_capture_result("ca")
    assert engine.state.current_screen_id == "voice_challenge"
    assert engine.state.answer_popup_kind == "wrong"
    assert engine.state.answer_popup_next_screen == "voice_challenge"


def test_letter_voice_close_shows_try_again_popup(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.check_spoken_answer", lambda spoken, target: "close")
    engine.set_screen("letter_voice_challenge")
    engine.state.current_task_target = "T"
    engine._process_letter_voice_capture_result("tea")
    assert engine.state.current_screen_id == "letter_voice_challenge"
    assert engine.state.answer_popup_kind == "wrong"
    assert engine.state.answer_popup_next_screen == "letter_voice_challenge"
