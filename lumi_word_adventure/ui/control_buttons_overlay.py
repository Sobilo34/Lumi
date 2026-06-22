"""Draw shipped UI control artwork over gameplay hitboxes."""
from __future__ import annotations

import pygame

from engine.control_assets import ControlAssets
from ui.control_images import draw_control_buttons
from ui.hitboxes import Hitbox

# Back-compat alias used by game_engine.
PLACEHOLDER_CONTROL_SCREENS = frozenset(
    {
        "letter_island_game",
        "word_garden_game",
        "voice_challenge",
        "letter_voice_challenge",
        "listening_state",
        "letter_listening_state",
        "bd_practice",
        "writing_castle_game",
        "world_map",
    }
)


def draw_control_button_placeholders(
    surface: pygame.Surface,
    hitboxes: list[Hitbox],
    controls: ControlAssets | None = None,
    *,
    writing_mode: str = "letters",
) -> None:
    draw_control_buttons(surface, hitboxes, controls, writing_mode=writing_mode)
