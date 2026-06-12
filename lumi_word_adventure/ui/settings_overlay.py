"""Minimal dynamic overlay for the Settings screen."""
from __future__ import annotations

import pygame

from config import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SETTINGS_OVERLAY_COLOR,
    SETTINGS_OVERLAY_PANEL_RGBA,
    SETTINGS_OVERLAY_POSITION,
    SETTINGS_STATUS_OVERLAY_POSITION,
)


def _chip(text: str, font: pygame.font.Font) -> pygame.Surface:
    rendered = font.render(text, True, SETTINGS_OVERLAY_COLOR)
    panel = pygame.Surface((rendered.get_width() + 14, rendered.get_height() + 10), pygame.SRCALPHA)
    panel.fill(SETTINGS_OVERLAY_PANEL_RGBA)
    panel.blit(rendered, (7, 5))
    return panel


def draw_settings_overlay(
    screen: pygame.Surface,
    *,
    music_enabled: bool,
    voice_enabled: bool,
    difficulty_mode: str,
    status_message: str = "",
) -> None:
    try:
        font = pygame.font.SysFont(None, 18)
    except Exception:
        return

    summary_x = int(SETTINGS_OVERLAY_POSITION[0] * SCREEN_WIDTH)
    summary_y = int(SETTINGS_OVERLAY_POSITION[1] * SCREEN_HEIGHT)
    music = "ON" if music_enabled else "OFF"
    voice = "ON" if voice_enabled else "OFF"
    summary = _chip(f"Music: {music}   Voice: {voice}   Difficulty: {difficulty_mode}", font)
    screen.blit(summary, (summary_x, summary_y))

    if status_message:
        status_x = int(SETTINGS_STATUS_OVERLAY_POSITION[0] * SCREEN_WIDTH)
        status_y = int(SETTINGS_STATUS_OVERLAY_POSITION[1] * SCREEN_HEIGHT)
        status = _chip(status_message, font)
        screen.blit(status, (status_x, status_y))
