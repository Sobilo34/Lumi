"""Tests for shipped UI control artwork."""
from __future__ import annotations

import pygame
import pytest

from config import PROJECT_DIR, UI_CONTROLS_DIR
from engine.control_assets import CONTROL_NAMES, ControlAssets
from ui.control_images import caption_for_control, control_key_for_hitbox, draw_control_buttons
from ui.hitboxes import Hitbox


@pytest.fixture(scope="module", autouse=True)
def _init_pygame() -> None:
    pygame.init()
    pygame.display.set_mode((1280, 720))


def test_ui_controls_are_installed() -> None:
    assets = ControlAssets()
    if not assets.available():
        pytest.skip("UI control assets are not installed")
    for name in CONTROL_NAMES:
        surface = assets.load(name)
        assert surface is not None
        assert surface.get_width() > 0
        assert surface.get_at((0, 0)).a == 0


def test_control_key_mapping_for_world_map_nodes() -> None:
    letter = Hitbox(name="Letter Island", rect=pygame.Rect(0, 0, 100, 100), target="letter_island_game")
    garden = Hitbox(name="Word Garden", rect=pygame.Rect(0, 0, 100, 100), target="word_garden_game")
    castle = Hitbox(name="Writing Castle", rect=pygame.Rect(0, 0, 100, 100), target="writing_castle_game")
    assert control_key_for_hitbox(letter) == "letter_island_world"
    assert control_key_for_hitbox(garden) == "word_garden_world"
    assert control_key_for_hitbox(castle) == "writing_castle_world"


def test_control_key_for_writing_castle_switch_buttons() -> None:
    verify = Hitbox(name="Verify", rect=pygame.Rect(0, 0, 100, 100), action="verify_writing")
    clear = Hitbox(name="Clear", rect=pygame.Rect(0, 0, 100, 100), action="clear_writing")
    switch = Hitbox(name="Switch mode", rect=pygame.Rect(0, 0, 100, 100), action="toggle_writing_mode")
    assert control_key_for_hitbox(verify) == "verify"
    assert control_key_for_hitbox(clear) == "clear"
    assert control_key_for_hitbox(clear, writing_try_again=True) == "try_again"
    assert control_key_for_hitbox(switch, writing_mode="letters") == "switch_to_word"
    assert control_key_for_hitbox(switch, writing_mode="words") == "switch_to_letters"


def test_control_captions_are_child_friendly() -> None:
    repeat = Hitbox(name="Repeat", rect=pygame.Rect(0, 0, 100, 100), action="repeat_prompt")
    hint = Hitbox(name="Hint", rect=pygame.Rect(0, 0, 100, 100), action="show_hint")
    speak = Hitbox(name="Listen", rect=pygame.Rect(0, 0, 100, 100), action="start_letter_listening")
    listen = Hitbox(name="Speaker", rect=pygame.Rect(0, 0, 100, 100), action="replay_main_menu_audio")
    mic = Hitbox(name="Listen", rect=pygame.Rect(0, 0, 100, 100), action="start_listening")
    next_word = Hitbox(name="Speak", rect=pygame.Rect(0, 0, 100, 100), action="next_word_voice")
    assert caption_for_control(repeat, "repeat") == "Hear Again"
    assert caption_for_control(hint, "hint") == "Get a Hint"
    assert caption_for_control(speak, "mic") == "Listen"
    assert caption_for_control(listen, "speaker") == "Listen"
    assert caption_for_control(mic, "mic") == "Listen"
    assert caption_for_control(next_word, "speaker") == "Speak"


def test_draw_control_buttons_blits_home() -> None:
    assets = ControlAssets()
    if not assets.available():
        pytest.skip("UI control assets are not installed")
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    home = Hitbox(name="Home", rect=pygame.Rect(20, 20, 80, 80), target="main_menu")
    draw_control_buttons(surface, [home], assets)
    assert surface.get_at((60, 60)).a > 0


def test_how_to_play_lets_go_does_not_draw_control_icon() -> None:
    lets_go = Hitbox(name="Let's Go", rect=pygame.Rect(0, 0, 100, 100), target="world_map")
    assert control_key_for_hitbox(lets_go) is None


def test_how_to_play_is_image_only_without_control_overlay() -> None:
    from ui.screen_factory import IMAGE_ONLY_SCREEN_IDS_NO_CONTROL_OVERLAY

    assert "how_to_play" in IMAGE_ONLY_SCREEN_IDS_NO_CONTROL_OVERLAY
