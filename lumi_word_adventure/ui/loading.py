"""Reusable loading spinners and overlays for pygame screens."""
from __future__ import annotations

import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import blit_outlined_text, draw_rounded_rect, font


def spinner_angle_deg(started_at_ms: int, *, speed_deg_per_sec: float = 220.0) -> float:
    elapsed = max(0, pygame.time.get_ticks() - int(started_at_ms or 0))
    return (elapsed * speed_deg_per_sec / 1000.0) % 360.0


def draw_spinner(
    surface: pygame.Surface,
    center: tuple[int, int],
    *,
    radius: int = 34,
    started_at_ms: int = 0,
    color: tuple[int, int, int] = (255, 170, 90),
    track_color: tuple[int, int, int] = (255, 230, 210),
    width: int = 7,
) -> None:
    """Animated arc spinner — no external dependencies."""
    angle = math.radians(spinner_angle_deg(started_at_ms))
    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = center
    pygame.draw.arc(surface, track_color, rect, 0, math.tau, max(3, width - 2))
    pygame.draw.arc(surface, color, rect, angle, angle + math.tau * 0.62, width)
    pygame.draw.circle(surface, (255, 220, 120), center, max(4, radius // 5))


def draw_loading_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    message: str,
    *,
    started_at_ms: int = 0,
    dim_alpha: int = 150,
) -> None:
    """Dim a region and show a centered spinner with a short label."""
    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    overlay.fill((255, 245, 250, dim_alpha))
    surface.blit(overlay, rect.topleft)

    panel = pygame.Rect(0, 0, min(rect.width - 24, 320), min(rect.height - 24, 150))
    panel.center = rect.center
    draw_rounded_rect(surface, panel, (255, 255, 255), radius=22, border=(245, 155, 175), border_width=3)

    draw_spinner(surface, (panel.centerx, panel.centery - 18), radius=28, started_at_ms=started_at_ms)
    label = str(message or "Loading...").strip() or "Loading..."
    blit_outlined_text(
        surface,
        label,
        (panel.centerx, panel.centery + 42),
        22,
        (92, 58, 110),
        outline=(255, 255, 255),
        outline_width=2,
    )


def draw_fullscreen_loading(
    surface: pygame.Surface,
    message: str,
    *,
    started_at_ms: int = 0,
) -> None:
    """Full-screen translucent veil with spinner — use during async work."""
    veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    veil.fill((255, 240, 245, 120))
    surface.blit(veil, (0, 0))
    panel_rect = pygame.Rect(0, 0, 360, 170)
    panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    draw_loading_panel(surface, panel_rect, message, started_at_ms=started_at_ms, dim_alpha=0)
