"""Prompt overlay when the voice mic is idle on speak challenge screens."""
from __future__ import annotations

import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import blit_outlined_text, draw_rounded_rect, draw_sparkle


def draw_voice_mic_prompt_overlay(
    screen: pygame.Surface,
    *,
    shown_at_ms: int,
    now_ms: int | None = None,
) -> None:
    """Draw a friendly reminder above the mic button while listening is off."""
    now = int(now_ms if now_ms is not None else pygame.time.get_ticks())
    elapsed = max(0, now - int(shown_at_ms or 0))
    pulse = 0.5 + 0.5 * math.sin(elapsed / 280.0)
    bob = int(6 * math.sin(elapsed / 320.0))

    mic_cx = int(SCREEN_WIDTH * 0.51)
    mic_top = int(SCREEN_HEIGHT * 0.77)
    panel_center = (mic_cx, mic_top - int(SCREEN_HEIGHT * 0.11) + bob)

    panel_w = int(SCREEN_WIDTH * 0.46)
    panel_h = int(SCREEN_HEIGHT * 0.11)
    panel = pygame.Rect(0, 0, panel_w, panel_h)
    panel.center = panel_center

    panel_surface = pygame.Surface((panel.width + 20, panel.height + 28), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(8, 12, panel.width, panel.height)
    draw_rounded_rect(panel_surface, shadow_rect, (0, 0, 0), radius=24)

    inner = pygame.Rect(8, 8, panel.width, panel.height)
    draw_rounded_rect(
        panel_surface,
        inner,
        (232, 244, 255),
        radius=22,
        border=(95, 175, 235),
        border_width=4,
    )
    gloss = pygame.Rect(inner.x + 12, inner.y + 8, inner.width - 24, int(inner.height * 0.38))
    gloss_surf = pygame.Surface((gloss.width, gloss.height), pygame.SRCALPHA)
    gloss_surf.fill((255, 255, 255, 88))
    panel_surface.blit(gloss_surf, gloss.topleft)

    tail_top = panel.bottom - 6 + bob
    tail_points = [
        (mic_cx - 16, tail_top),
        (mic_cx + 16, tail_top),
        (mic_cx, tail_top + 18),
    ]
    pygame.draw.polygon(screen, (95, 175, 235), tail_points)
    pygame.draw.polygon(screen, (232, 244, 255), [
        (mic_cx - 12, tail_top),
        (mic_cx + 12, tail_top),
        (mic_cx, tail_top + 14),
    ])

    screen.blit(panel_surface, (panel.x - 8, panel.y - 8))

    blit_outlined_text(
        screen,
        "Click the Mic to speak",
        (panel.centerx, panel.centery - 6 + bob),
        38,
        (58, 118, 188),
        outline=(255, 255, 255),
        outline_width=3,
    )
    blit_outlined_text(
        screen,
        "Then say your answer",
        (panel.centerx, panel.centery + 28 + bob),
        22,
        (108, 68, 42),
        outline=(255, 255, 255),
        outline_width=2,
    )

    for offset_x, offset_y in ((-58, -18), (58, -14), (-42, 20), (48, 18)):
        draw_sparkle(
            screen,
            panel.centerx + offset_x,
            panel.centery + offset_y + bob,
            size=4 + int(2 * pulse),
            color=(255, 210, 90),
        )

    ring_radius = int(34 + 8 * pulse)
    ring = pygame.Surface((ring_radius * 2 + 4, ring_radius * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(
        ring,
        (245, 145, 165, int(70 + 50 * pulse)),
        (ring_radius + 2, ring_radius + 2),
        ring_radius,
        4,
    )
    screen.blit(ring, (mic_cx - ring_radius - 2, mic_top + int(SCREEN_HEIGHT * 0.04) - ring_radius - 2 + bob))
