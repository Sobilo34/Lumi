"""Letter tile variant rules: normal on challenge, selected only on success."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from engine.asset_manager import AssetManager
from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel
from ui.dynamic_layers import letter_tile_uses_selected


@pytest.mark.parametrize(
    ("letter", "index", "screen_id", "variant", "target", "slots", "expected"),
    [
        ("R", 0, "letter_island_game", "normal", "R", ("R", "S", "T", "U"), False),
        ("R", 0, "letter_correct_feedback", "success", "R", ("R", "S", "T", "U"), True),
        ("R", 1, "letter_correct_feedback", "success", "R", ("R", "S", "T", "U"), False),
        ("W", 2, "letter_island_game", "normal", "W", ("U", "V", "W", "X"), False),
        ("W", 2, "letter_correct_feedback", "success", "W", ("U", "V", "W", "X"), True),
        ("W", 3, "letter_correct_feedback", "success", "W", ("U", "V", "W", "X"), False),
    ],
)
def test_letter_tile_uses_selected_rules(
    letter: str,
    index: int,
    screen_id: str,
    variant: str,
    target: str,
    slots: tuple[str, ...],
    expected: bool,
) -> None:
    assert (
        letter_tile_uses_selected(
            screen_id=screen_id,
            tile_variant=variant,
            slot_letter=slots[index],
            target_letter=target,
        )
        is expected
    )


@pytest.fixture()
def engine(tmp_path: Path) -> GameEngine:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    game = GameEngine(screen)
    game.learner = LearnerModel(profile_path=tmp_path / "player_1.json")
    return game


@pytest.mark.parametrize("letter", list("RSTUVWXYZ"))
def test_rw_success_view_highlights_only_target(engine: GameEngine, letter: str) -> None:
    distractors = [item for item in "RSTUVWXYZ" if item != letter][:3]
    slots = [letter] + distractors
    engine.state.current_screen_id = "letter_correct_feedback"
    engine.state.completed_letter_target = letter
    engine.state.completed_letter_choices = slots
    engine.state.letter_choice_slots = slots

    view = engine._scene_view()
    assert view.target_letter == letter
    assert tuple(view.slot_letters) == tuple(slots)
    selected_count = sum(
        1
        for slot in view.slot_letters
        if letter_tile_uses_selected(
            screen_id=view.screen_id,
            tile_variant="success",
            slot_letter=slot,
            target_letter=view.target_letter,
        )
    )
    assert selected_count == 1


@pytest.mark.parametrize("letter", list("RSTUVWXYZ"))
def test_rw_challenge_view_never_uses_selected(engine: GameEngine, letter: str) -> None:
    slots = list("RSTU")
    engine.state.current_screen_id = "letter_island_game"
    engine.state.current_task_target = letter
    engine.state.letter_choice_slots = slots

    view = engine._scene_view()
    assert all(
        not letter_tile_uses_selected(
            screen_id=view.screen_id,
            tile_variant="normal",
            slot_letter=slot,
            target_letter=view.target_letter,
        )
        for slot in view.slot_letters
    )


@pytest.mark.parametrize("letter", list("rstuvwxyz"))
def test_letter_png_paths_resolve_for_rw(engine: GameEngine, letter: str) -> None:
    assets = engine.asset_manager
    assets.invalidate_letter_tiles("letter_island_game")
    normal = assets.load_letter_tile("letter_island_game", letter, selected=False)
    selected = assets.load_letter_tile("letter_island_game", letter, selected=True)
    assert normal is not None, f"missing {letter}.png"
    assert selected is not None, f"missing {letter}_selected.png"
    assert normal.get_size() != (0, 0)
    assert selected.get_size() != (0, 0)
