"""Big celebratory on-screen feedback for voice pronunciation rounds."""
from __future__ import annotations

import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import blit_outlined_text, draw_rounded_rect, draw_sparkle


def _ease_out_back(t: float) -> float:
    """Overshoot pop-in (0..1)."""
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * pow(t - 1.0, 3) + c1 * pow(t - 1.0, 2)


def _alpha_for_elapsed(elapsed_ms: int, *, hold_ms: int = 1700, fade_ms: int = 700) -> int:
    if elapsed_ms < 0:
        return 0
    if elapsed_ms <= hold_ms:
        return 255
    fade_t = (elapsed_ms - hold_ms) / max(1, fade_ms)
    return max(0, int(255 * (1.0 - fade_t)))


def _draw_star_burst(surface: pygame.Surface, center: tuple[int, int], *, elapsed_ms: int, color: tuple[int, int, int]) -> None:
    cx, cy = center
    for index in range(8):
        angle = (index / 8.0) * math.tau + elapsed_ms / 420.0
        radius = 72 + 10 * math.sin(elapsed_ms / 180.0 + index)
        x = cx + int(math.cos(angle) * radius)
        y = cy + int(math.sin(angle) * radius)
        draw_sparkle(surface, x, y, size=6 + (index % 2), color=color)


def draw_voice_pronunciation_overlay(
    screen: pygame.Surface,
    *,
    feedback: str,
    shown_at_ms: int,
    now_ms: int | None = None,
) -> None:
    """Draw large Correct! / Try Again! styling over voice challenge screens."""
    kind = str(feedback or "").strip().lower()
    if kind not in {"correct", "try_again"}:
        return

    now = int(now_ms if now_ms is not None else pygame.time.get_ticks())
    elapsed = max(0, now - int(shown_at_ms or 0))
    alpha = _alpha_for_elapsed(elapsed)
    if alpha <= 0:
        return

    pop = _ease_out_back(min(1.0, elapsed / 320.0))
    bounce_y = int(8 * math.sin(elapsed / 140.0) * pop) if elapsed > 320 else int((1.0 - pop) * -28)

    veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    veil.fill((30, 18, 48, int(72 * alpha / 255)))
    screen.blit(veil, (0, 0))

    panel_w = int(SCREEN_WIDTH * (0.62 + 0.06 * pop))
    panel_h = int(SCREEN_HEIGHT * (0.28 + 0.04 * pop))
    panel = pygame.Rect(0, 0, panel_w, panel_h)
    panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + bounce_y)

    if kind == "correct":
        panel_fill = (214, 255, 220)
        panel_border = (88, 190, 110)
        title = "Correct!"
        title_fill = (56, 168, 82)
        title_outline = (255, 255, 255)
        accent = (255, 228, 96)
        subtitle = "Great pronunciation!"
    else:
        panel_fill = (255, 228, 210)
        panel_border = (255, 145, 105)
        title = "Try Again!"
        title_fill = (235, 98, 72)
        title_outline = (255, 255, 255)
        accent = (255, 198, 120)
        subtitle = "You can do it!"

    panel_surface = pygame.Surface((panel.width + 24, panel.height + 24), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(10, 14, panel.width, panel.height)
    draw_rounded_rect(panel_surface, shadow_rect, (0, 0, 0), radius=34)
    inner = pygame.Rect(10, 10, panel.width, panel.height)
    draw_rounded_rect(
        panel_surface,
        inner,
        panel_fill,
        radius=32,
        border=panel_border,
        border_width=6,
    )
    gloss = pygame.Rect(inner.x + 14, inner.y + 10, inner.width - 28, int(inner.height * 0.34))
    gloss_surf = pygame.Surface((gloss.width, gloss.height), pygame.SRCALPHA)
    gloss_surf.fill((255, 255, 255, 70))
    panel_surface.blit(gloss_surf, gloss.topleft)
    panel_surface.set_alpha(alpha)
    screen.blit(panel_surface, (panel.x - 10, panel.y - 10))

    title_size = int(108 * (0.88 + 0.12 * pop))
    subtitle_size = int(34 * (0.9 + 0.1 * pop))
    center = (panel.centerx, panel.centery - 8 + bounce_y)

    if kind == "correct":
        _draw_star_burst(screen, center, elapsed_ms=elapsed, color=accent)

    blit_outlined_text(
        screen,
        title,
        center,
        title_size,
        title_fill,
        outline=title_outline,
        outline_width=5,
    )
    blit_outlined_text(
        screen,
        subtitle,
        (center[0], center[1] + int(title_size * 0.62)),
        subtitle_size,
        (108, 68, 42),
        outline=(255, 255, 255),
        outline_width=2,
    )
