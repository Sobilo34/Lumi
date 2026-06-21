"""Procedural placeholder buttons for chunk screens that lost their baked-in
control art after the global background change.

These render labeled, tappable-looking buttons exactly over each control
hitbox so every screen keeps working while real button art is added later.
"""
from __future__ import annotations

import pygame

from ui.components.primitives import (
    BUTTON_BLUE,
    BUTTON_PINK,
    BUTTON_PURPLE,
    BUTTON_YELLOW,
    draw_icon_bulb,
    draw_icon_gear,
    draw_icon_home,
    draw_icon_mic,
    draw_icon_refresh,
    draw_icon_speaker,
    draw_rounded_rect,
    font,
)
from ui.hitboxes import Hitbox

# Screens that are composed from chunks over the global background and need
# placeholder controls drawn on top. (Procedural menu screens draw their own
# buttons; badge_unlock draws its own celebration card.)
PLACEHOLDER_CONTROL_SCREENS: frozenset[str] = frozenset(
    {
        "letter_island_game",
        "word_garden_game",
        "voice_challenge",
        "letter_voice_challenge",
        "listening_state",
        "letter_listening_state",
        "bd_practice",
    }
)

# Hitboxes already rendered as letter/word tiles by the dynamic layers.
_SKIP_ACTION_PREFIXES = ("select_letter_slot_", "select_word_slot_")

_RED = (235, 110, 110)
_GREEN = (130, 200, 140)


def _style_for(box: Hitbox) -> tuple[str, tuple[int, int, int]]:
    """Return (icon_key, fill_color) for a control hitbox."""
    action = (box.action or "").lower()
    name = (box.name or "").lower()
    target = (box.target or "").lower()

    if target == "world_map" or name == "home":
        return "home", BUTTON_PINK
    if target == "settings" or name == "settings":
        return "gear", BUTTON_PURPLE
    if action.startswith("repeat") or name.startswith("repeat"):
        return "refresh", BUTTON_PURPLE
    if "hint" in action or "help" in action or name in {"hint", "help"}:
        return "bulb", BUTTON_YELLOW
    if "listening" in action or name in {"microphone", "mic"}:
        return "mic", BUTTON_BLUE
    if action in {"voice_or_speak_mode", "voice_mode"} or name == "speak":
        return "speaker", BUTTON_BLUE
    if "stop" in action or name == "stop":
        return "label", _RED
    if "skip" in action or name == "skip":
        return "label", BUTTON_PURPLE
    if name.startswith("answer"):
        return "label", BUTTON_BLUE
    return "label", BUTTON_PINK


def _draw_icon(surface: pygame.Surface, key: str, center: tuple[int, int]) -> None:
    if key == "home":
        draw_icon_home(surface, center)
    elif key == "gear":
        draw_icon_gear(surface, center)
    elif key == "refresh":
        draw_icon_refresh(surface, center)
    elif key == "bulb":
        draw_icon_bulb(surface, center)
    elif key == "mic":
        draw_icon_mic(surface, center)
    elif key == "speaker":
        draw_icon_speaker(surface, center)


def _draw_label(surface: pygame.Surface, text: str, center: tuple[int, int], max_width: int) -> None:
    size = 30
    glyphs = font(size)
    rendered = glyphs.render(text, True, (255, 255, 255))
    while rendered.get_width() > max_width and size > 12:
        size -= 2
        glyphs = font(size)
        rendered = glyphs.render(text, True, (255, 255, 255))
    surface.blit(rendered, rendered.get_rect(center=center))


def draw_control_button_placeholders(surface: pygame.Surface, hitboxes: list[Hitbox]) -> None:
    """Draw a labeled placeholder button over each control hitbox."""
    for box in hitboxes:
        action = box.action or ""
        if any(action.startswith(prefix) for prefix in _SKIP_ACTION_PREFIXES):
            continue
        rect = box.rect
        if rect.width <= 0 or rect.height <= 0:
            continue

        key, color = _style_for(box)
        radius = max(8, min(rect.width, rect.height) // 3)
        draw_rounded_rect(surface, rect, color, radius=radius, border=(255, 255, 255), border_width=4)

        show_caption = rect.height >= 80
        if key == "label":
            _draw_label(surface, box.name, rect.center, rect.width - 14)
            continue

        icon_center = (rect.centerx, rect.centery - (10 if show_caption else 0))
        _draw_icon(surface, key, icon_center)
        if show_caption:
            _draw_label(surface, box.name, (rect.centerx, rect.bottom - 22), rect.width - 14)
