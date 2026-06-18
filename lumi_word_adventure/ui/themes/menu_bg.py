"""Pink sky menu / splash backgrounds — reference 01-05, 28."""
from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import SKY_BOTTOM, SKY_MID, SKY_TOP, draw_rect_shadow, draw_rounded_rect, draw_sparkle, draw_vertical_gradient, font, pct_rect


def _draw_flashcard(surface: pygame.Surface, rect: pygame.Rect, emoji: str, word: str) -> None:
    draw_rounded_rect(surface, rect, (255, 252, 240), radius=14, border=(245, 155, 175), border_width=2)
    inner = rect.inflate(-8, -8)
    draw_rounded_rect(surface, inner, (255, 255, 255), radius=10, border=(235, 190, 200), border_width=1)
    label = font(28).render(emoji, True, (80, 60, 90))
    surface.blit(label, label.get_rect(center=(rect.centerx, rect.centery - 10)))
    word_label = font(16, bold=True).render(word, True, (108, 68, 42))
    surface.blit(word_label, word_label.get_rect(center=(rect.centerx, rect.bottom - 18)))


def paint_pink_sky(surface: pygame.Surface) -> None:
    draw_vertical_gradient(surface, (255, 200, 210), SKY_MID, SKY_BOTTOM)
    for cx, cy, rx, ry in ((180, 70, 100, 38), (520, 45, 120, 42), (950, 80, 90, 32), (1080, 120, 70, 28)):
        cloud = pygame.Surface((rx * 2 + 30, ry * 2 + 16), pygame.SRCALPHA)
        pygame.draw.ellipse(cloud, (255, 255, 255, 120), (10, 8, rx * 2 - 10, ry * 2))
        pygame.draw.ellipse(cloud, (255, 255, 255, 90), (rx // 2, 0, rx + 20, ry * 2))
        surface.blit(cloud, (cx - rx, cy - ry))
    for sx, sy in ((200, 100), (400, 60), (700, 90), (900, 50), (1100, 110)):
        draw_sparkle(surface, sx, sy, size=3)
    # castle silhouette (reference 02)
    castle = pct_rect(0.0, 0.52, 0.22, 0.28)
    pygame.draw.rect(surface, (255, 200, 215), pygame.Rect(castle.x + 40, castle.bottom - 90, 50, 90), border_radius=6)
    pygame.draw.rect(surface, (255, 190, 210), pygame.Rect(castle.x + 100, castle.bottom - 120, 60, 120), border_radius=8)
    for tx in (castle.x + 52, castle.x + 112):
        points = [(tx + 20, castle.bottom - 130), (tx, castle.bottom - 100), (tx + 40, castle.bottom - 100)]
        pygame.draw.polygon(surface, (255, 175, 195), points)
    for lx, ly, letter, col in (
        (120, 130, "A", (255, 180, 200)),
        (1050, 100, "B", (200, 180, 255)),
        (150, 520, "C", (180, 220, 255)),
        (980, 480, "cat", (255, 200, 210)),
    ):
        g = font(28 if len(letter) == 1 else 22, bold=True).render(letter, True, col)
        g.set_alpha(90)
        surface.blit(g, (lx, ly))
    _draw_flashcard(surface, pct_rect(0.04, 0.14, 0.11, 0.18), "🍎", "apple")
    _draw_flashcard(surface, pct_rect(0.84, 0.12, 0.11, 0.18), "🐱", "cat")
    _draw_flashcard(surface, pct_rect(0.82, 0.62, 0.11, 0.18), "⛵", "boat")
    # rainbow corner
    for col in ((255, 120, 120), (255, 200, 80), (120, 220, 120), (120, 180, 255), (200, 140, 255)):
        pygame.draw.arc(surface, col, pct_rect(0.78, 0.55, 0.22, 0.35), 3.14, 0, 8)
    # alphabet blocks corner
    for i, (letter, col) in enumerate(zip(("A", "B", "C"), ((255, 120, 120), (120, 175, 255), (255, 210, 90)))):
        b = pct_rect(0.04 + i * 0.03, 0.62 - i * 0.03, 0.05, 0.07)
        draw_rounded_rect(surface, b, col, radius=8)
        glyph = font(20, bold=True).render(letter, True, (255, 255, 255))
        surface.blit(glyph, glyph.get_rect(center=b.center))


def paint_loading_bar(surface: pygame.Surface, progress: float) -> None:
    bar_outer = pct_rect(0.28, 0.84, 0.44, 0.045)
    draw_rounded_rect(surface, bar_outer, (255, 255, 255), radius=12, border=(245, 155, 175), border_width=2)
    fill = bar_outer.inflate(-6, -6)
    fill.width = int(fill.width * max(0.05, min(1.0, progress)))
    if fill.width:
        draw_rounded_rect(surface, fill, (255, 210, 90), radius=10)
    label = font(20, bold=True).render("Loading...", True, (72, 58, 88))
    surface.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, int(bar_outer.y - 22))))
