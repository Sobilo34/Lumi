"""Shared chrome: HUD, buttons, logo, mascot — matched to reference_interfaces."""
from __future__ import annotations

import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import (
    BUTTON_PINK,
    GREEN_PLUS,
    HUD_CREAM,
    HUD_PINK,
    HUD_PINK_DARK,
    STAR_YELLOW,
    TEXT_DARK,
    blit_outlined_text,
    draw_circle_button,
    draw_dashed_rounded_rect,
    draw_icon_gear,
    draw_icon_home,
    draw_rect_shadow,
    draw_rounded_rect,
    draw_sparkle,
    font,
    pct_rect,
)


def draw_corner_nav(surface: pygame.Surface, *, show_home: bool = True, show_settings: bool = True) -> None:
    """Corner nav is drawn from shipped control art via hitbox overlay in game_engine."""
    return


def draw_lumi_hud(
    surface: pygame.Surface,
    *,
    child_name: str,
    energy: int,
    energy_max: int,
    stars_filled: int,
    progress_text: str = "",
) -> None:
    hud = pct_rect(0.075, 0.018, 0.195, 0.095)
    draw_rounded_rect(surface, hud, HUD_CREAM, radius=20, border=HUD_PINK, border_width=2)
    avatar = pygame.Rect(hud.x + 8, hud.y + 10, 42, 42)
    draw_rounded_rect(surface, avatar, STAR_YELLOW, radius=12, border=(255, 255, 255), border_width=2)
    mini = font(22, bold=True).render("★", True, (255, 255, 255))
    surface.blit(mini, mini.get_rect(center=avatar.center))
    surface.blit(font(19, bold=True).render(child_name, True, HUD_PINK_DARK), (hud.x + 58, hud.y + 12))
    surface.blit(font(15, bold=True).render(f"⚡ {energy}/{energy_max}", True, TEXT_DARK), (hud.x + 58, hud.y + 36))
    bar = pygame.Rect(hud.x + 58, hud.y + 58, 100, 9)
    pygame.draw.rect(surface, (255, 255, 255), bar, border_radius=5)
    fill_w = int(bar.width * min(1.0, energy / max(1, energy_max)))
    if fill_w:
        pygame.draw.rect(surface, HUD_PINK, pygame.Rect(bar.x, bar.y, fill_w, bar.height), border_radius=5)
    plus_c = (hud.right - 22, hud.centery + 8)
    pygame.draw.circle(surface, GREEN_PLUS, plus_c, 12)
    pygame.draw.line(surface, (255, 255, 255), (plus_c[0] - 5, plus_c[1]), (plus_c[0] + 5, plus_c[1]), 2)
    pygame.draw.line(surface, (255, 255, 255), (plus_c[0], plus_c[1] - 5), (plus_c[0], plus_c[1] + 5), 2)

    if progress_text:
        progress = pct_rect(0.34, 0.018, 0.32, 0.055)
        draw_rounded_rect(surface, progress, (255, 255, 255), radius=16, border=HUD_PINK, border_width=2)
        plabel = font(16, bold=True).render(progress_text, True, TEXT_DARK)
        surface.blit(plabel, plabel.get_rect(center=progress.center))

    stars_rect = pct_rect(0.735, 0.018, 0.125, 0.055)
    draw_rounded_rect(surface, stars_rect, (255, 255, 255), radius=16, border=HUD_PINK, border_width=2)
    for i in range(3):
        sx = stars_rect.x + 22 + i * 32
        color = STAR_YELLOW if i < stars_filled else (225, 205, 215)
        star = font(24, bold=True).render("★", True, color)
        surface.blit(star, star.get_rect(center=(sx, stars_rect.centery)))


def draw_logo_banner(surface: pygame.Surface, *, y_pct: float = 0.12) -> None:
    banner = pct_rect(0.22, y_pct, 0.56, 0.14)
    draw_rect_shadow(surface, banner, radius=24, offset=(0, 6), alpha=30)
    draw_rounded_rect(surface, banner, (255, 252, 235), radius=24, border=HUD_PINK, border_width=4)
    inner = banner.inflate(-12, -12)
    draw_dashed_rounded_rect(surface, inner, (255, 255, 255), radius=18, dash=6, gap=4, width=2)
    for sx, sy in ((banner.x + 18, banner.y + 14), (banner.right - 18, banner.y + 14), (banner.right - 22, banner.bottom - 16)):
        draw_sparkle(surface, sx, sy, size=5, color=STAR_YELLOW if sy < banner.centery else HUD_PINK)
    cx, cy = banner.centerx, banner.centery
    blit_outlined_text(surface, "Lumi's", (cx - 118, cy - 8), 30, HUD_PINK_DARK, outline=(255, 255, 255), outline_width=2)
    blit_outlined_text(surface, "Word Adventure", (cx + 42, cy + 10), 28, (175, 120, 210), outline=(255, 255, 255), outline_width=2)


def draw_lumi_mascot_large(surface: pygame.Surface, *, x_pct: float = 0.28, y_pct: float = 0.58, scale: float = 1.0) -> None:
    center = (int(SCREEN_WIDTH * x_pct), int(SCREEN_HEIGHT * y_pct))
    r_outer, r_inner = int(48 * scale), int(22 * scale)
    points = []
    for i in range(10):
        angle = i * math.pi / 5 - math.pi / 2
        radius = r_outer if i % 2 == 0 else r_inner
        points.append((center[0] + int(radius * math.cos(angle)), center[1] + int(radius * math.sin(angle))))
    pygame.draw.polygon(surface, STAR_YELLOW, points)
    pygame.draw.polygon(surface, (230, 175, 45), points, width=max(2, int(3 * scale)))
    for ex in (center[0] - int(14 * scale), center[0] + int(14 * scale)):
        pygame.draw.circle(surface, (45, 45, 45), (ex, center[1] - int(6 * scale)), int(6 * scale))
    pygame.draw.arc(surface, (120, 72, 48), pygame.Rect(center[0] - 16, center[1] + 2, 32, 18), 3.4, 6.0, 3)


def draw_speech_bubble(surface: pygame.Surface, text: str, *, x_pct: float = 0.58, y_pct: float = 0.48, w_pct: float = 0.34) -> None:
    bubble = pct_rect(x_pct, y_pct, w_pct, 0.12)
    draw_rounded_rect(surface, bubble, (255, 255, 255), radius=20, border=HUD_PINK, border_width=2)
    tail = [(bubble.x + 30, bubble.bottom), (bubble.x + 10, bubble.bottom + 16), (bubble.x + 60, bubble.bottom)]
    pygame.draw.polygon(surface, (255, 255, 255), tail)
    y = bubble.y + 14
    for line in _wrap(text, bubble.width - 24):
        label = font(18, bold=True).render(line, True, TEXT_DARK)
        surface.blit(label, (bubble.x + 14, y))
        y += label.get_height() + 2


def draw_menu_button(surface: pygame.Surface, rect: pygame.Rect, label: str, *, accent: tuple[int, int, int] = (255, 200, 90)) -> None:
    draw_rounded_rect(surface, rect, accent, radius=18, border=(255, 255, 255), border_width=3)
    text = font(22, bold=True).render(label, True, (255, 255, 255))
    surface.blit(text, text.get_rect(center=rect.center))


def draw_stitched_panel(surface: pygame.Surface, outer: pygame.Rect, *, border_color: tuple[int, int, int]) -> pygame.Rect:
    draw_rounded_rect(surface, outer, border_color, radius=28)
    inner = outer.inflate(-16, -16)
    draw_rounded_rect(surface, inner, (255, 255, 252), radius=22, border=(220, 130, 145), border_width=2)
    return inner


def draw_cta_button(surface: pygame.Surface, rect: pygame.Rect, label: str) -> None:
    draw_rounded_rect(surface, rect, (255, 190, 80), radius=20, border=(255, 255, 255), border_width=3)
    text = font(26, bold=True).render(label, True, (255, 255, 255))
    surface.blit(text, text.get_rect(center=rect.center))


def draw_pink_cta_button(surface: pygame.Surface, rect: pygame.Rect, label: str) -> None:
    draw_rounded_rect(surface, rect, HUD_PINK, radius=22, border=(255, 255, 255), border_width=3)
    text = font(28, bold=True).render(label, True, (255, 255, 255))
    surface.blit(text, text.get_rect(center=rect.center))


def _wrap(text: str, max_width: int) -> list[str]:
    f = font(18, bold=True)
    words = text.split()
    if not words:
        return [""]
    lines, current = [], words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if f.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines
