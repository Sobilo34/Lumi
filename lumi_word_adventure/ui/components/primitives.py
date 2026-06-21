"""Shared drawing helpers and theme tokens matched to reference_interfaces/07."""
from __future__ import annotations

import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH

# --- Reference palette (07_letter_island_gameplay.png) ---
SKY_TOP = (255, 210, 225)
SKY_MID = (255, 228, 238)
SKY_BOTTOM = (255, 238, 245)
OCEAN = (152, 210, 228)
OCEAN_LIGHT = (178, 225, 240)
SAND = (248, 225, 175)
SAND_SHADOW = (235, 205, 155)
BOARD_FILL = (255, 255, 252)
BOARD_BORDER = (235, 150, 165)
BOARD_STITCH = (220, 130, 145)
PROMPT_BROWN = (108, 68, 42)
PROMPT_ACCENT = (245, 105, 125)
TEXT_DARK = (68, 52, 82)
HUD_CREAM = (255, 248, 210)
HUD_PINK = (245, 155, 175)
HUD_PINK_DARK = (230, 120, 145)
BUTTON_PINK = (245, 145, 165)
BUTTON_PURPLE = (168, 130, 225)
BUTTON_YELLOW = (255, 200, 85)
BUTTON_BLUE = (95, 175, 235)
STAR_YELLOW = (255, 210, 70)
STAR_FACE = (255, 220, 100)
GREEN_PLUS = (120, 200, 120)
WOOD = (168, 115, 65)
WOOD_DARK = (120, 78, 42)

# Per-slot card styling — bg + letter colour (reference uses matching tints)
CARD_STYLES = (
    {"bg": (225, 210, 245), "fg": (155, 95, 195), "border": (190, 160, 220)},
    {"bg": (210, 235, 210), "fg": (85, 165, 105), "border": (170, 210, 170)},
    {"bg": (250, 215, 230), "fg": (225, 105, 145), "border": (235, 180, 200)},
    {"bg": (255, 225, 190), "fg": (230, 145, 70), "border": (245, 200, 160)},
)


def pct_rect(x_pct: float, y_pct: float, w_pct: float, h_pct: float) -> pygame.Rect:
    return pygame.Rect(
        int(SCREEN_WIDTH * x_pct),
        int(SCREEN_HEIGHT * y_pct),
        int(SCREEN_WIDTH * w_pct),
        int(SCREEN_HEIGHT * h_pct),
    )


_FONT_CACHE: dict[tuple[int, bool], pygame.font.Font] = {}


def font(size: int, *, bold: bool = True) -> pygame.font.Font:
    cache_key = (size, bold)
    cached = _FONT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    for name in (
        "fredokaone",
        "fredoka one",
        "baloo2",
        "nunito",
        "quicksand",
        "comicsansms",
        "dejavusans",
        "arial",
    ):
        try:
            loaded = pygame.font.SysFont(name, size, bold=bold)
            _FONT_CACHE[cache_key] = loaded
            return loaded
        except Exception:
            continue
    loaded = pygame.font.SysFont(None, size)
    _FONT_CACHE[cache_key] = loaded
    return loaded


_DISPLAY_FONT_CACHE: dict[int, pygame.font.Font] = {}


def display_font(size: int) -> pygame.font.Font:
    """Larger celebratory headings for completion screens."""
    cached = _DISPLAY_FONT_CACHE.get(size)
    if cached is not None:
        return cached
    for name in (
        "luckiest guy",
        "impact",
        "cooper black",
        "arial black",
        "fredokaone",
        "fredoka one",
        "baloo2",
        "nunito",
    ):
        try:
            loaded = pygame.font.SysFont(name, size, bold=True)
            _DISPLAY_FONT_CACHE[size] = loaded
            return loaded
        except Exception:
            continue
    loaded = font(size, bold=True)
    _DISPLAY_FONT_CACHE[size] = loaded
    return loaded


def draw_rect_shadow(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    radius: int = 16,
    offset: tuple[int, int] = (0, 5),
    alpha: int = 38,
) -> None:
    shadow = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, alpha), shadow.get_rect(), border_radius=radius + 4)
    surface.blit(shadow, (rect.x + offset[0] - 8, rect.y + offset[1] - 4))


def blit_outlined_text(
    surface: pygame.Surface,
    text: str,
    center: tuple[int, int],
    size: int,
    fill: tuple[int, int, int],
    *,
    outline: tuple[int, int, int] = (255, 255, 255),
    outline_width: int = 3,
    bold: bool = True,
) -> None:
    """Rounded kid-game titles with a soft outline (reference welcome / Find B)."""
    f = font(size, bold=bold)
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy > outline_width * outline_width:
                continue
            if dx == 0 and dy == 0:
                continue
            layer = f.render(text, True, outline)
            surface.blit(layer, layer.get_rect(center=(center[0] + dx, center[1] + dy)))
    label = f.render(text, True, fill)
    surface.blit(label, label.get_rect(center=center))


def draw_sparkle(surface: pygame.Surface, x: int, y: int, *, size: int = 5, color: tuple[int, int, int] = (255, 255, 255)) -> None:
    pygame.draw.line(surface, color, (x - size, y), (x + size, y), 2)
    pygame.draw.line(surface, color, (x, y - size), (x, y + size), 2)
    pygame.draw.circle(surface, color, (x, y), max(1, size // 3))


def draw_simple_flower(surface: pygame.Surface, x: int, y: int, *, petal: tuple[int, int, int] = (255, 170, 195), radius: int = 7) -> None:
    for i in range(5):
        angle = i * math.pi * 2 / 5 - math.pi / 2
        px = x + int(math.cos(angle) * radius)
        py = y + int(math.sin(angle) * radius)
        pygame.draw.circle(surface, petal, (px, py), radius)
    pygame.draw.circle(surface, (255, 230, 120), (x, y), radius - 2)


def draw_3d_block(
    surface: pygame.Surface,
    rect: pygame.Rect,
    letter: str,
    face: tuple[int, int, int],
    *,
    depth: int = 8,
) -> None:
    """Toy alphabet block with a side face (reference props)."""
    side = tuple(max(0, c - 35) for c in face)
    depth_rect = pygame.Rect(rect.x + depth, rect.y - depth // 2, rect.width, rect.height)
    draw_rounded_rect(surface, depth_rect, side, radius=10)
    draw_rounded_rect(surface, rect, face, radius=10, border=(255, 255, 255), border_width=2)
    highlight = pygame.Rect(rect.x + 4, rect.y + 4, rect.width - 8, rect.height // 3)
    s = pygame.Surface((highlight.width, highlight.height), pygame.SRCALPHA)
    s.fill((255, 255, 255, 45))
    surface.blit(s, highlight.topleft)
    blit_fitted_text(surface, rect, letter, (255, 255, 255), padding=10, fill_height_ratio=0.62)


def content_rect(rect: pygame.Rect, padding: int = 14) -> pygame.Rect:
    """Inner drawable area inside a bordered card."""
    return rect.inflate(-padding * 2, -padding * 2)


def fit_font_size(
    text: str,
    bounds: pygame.Rect,
    *,
    fill_height_ratio: float = 0.68,
    bold: bool = True,
    min_size: int = 12,
) -> int:
    """Pick the largest font size so text fits inside bounds (reference cards ~65% height)."""
    cleaned = (text or "").strip()
    if not cleaned or bounds.width <= 0 or bounds.height <= 0:
        return min_size
    size = max(min_size, int(bounds.height * fill_height_ratio))
    while size >= min_size:
        w, h = font(size, bold=bold).size(cleaned)
        if w <= bounds.width and h <= bounds.height:
            return size
        size -= 1
    return min_size


def fit_font_size_for_label(text: str, bounds: pygame.Rect, *, bold: bool = True) -> int:
    """Height/width-aware sizing for single letters vs short words."""
    cleaned = (text or "").strip()
    length = max(1, len(cleaned))
    if length == 1:
        return fit_font_size(cleaned, bounds, fill_height_ratio=0.68, bold=bold)
    if length <= 4:
        return fit_font_size(cleaned, bounds, fill_height_ratio=0.52, bold=bold)
    return fit_font_size(cleaned, bounds, fill_height_ratio=0.42, bold=bold)


def blit_fitted_text(
    surface: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    color: tuple[int, int, int],
    *,
    padding: int = 14,
    fill_height_ratio: float | None = None,
    bold: bool = True,
    shadow: tuple[int, int, int] | None = None,
    shadow_offset: tuple[int, int] = (2, 2),
) -> None:
    """Center text inside rect, auto-scaled to fit with even padding."""
    inner = content_rect(rect, padding) if padding else rect
    if fill_height_ratio is None:
        size = fit_font_size_for_label(text, inner, bold=bold)
    else:
        size = fit_font_size(text, inner, fill_height_ratio=fill_height_ratio, bold=bold)
    cleaned = (text or "").strip()
    if shadow and cleaned:
        shadow_surf = font(size, bold=bold).render(cleaned, True, shadow)
        surface.blit(
            shadow_surf,
            shadow_surf.get_rect(
                center=(rect.centerx + shadow_offset[0], rect.centery + shadow_offset[1]),
            ),
        )
    if cleaned:
        glyph = font(size, bold=bold).render(cleaned, True, color)
        surface.blit(glyph, glyph.get_rect(center=rect.center))


def draw_vertical_gradient(
    surface: pygame.Surface,
    top: tuple[int, int, int],
    mid: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> None:
    height = surface.get_height()
    width = surface.get_width()
    mid_y = int(height * 0.45)
    for y in range(height):
        if y <= mid_y:
            ratio = y / max(1, mid_y)
            color = tuple(int(top[i] + (mid[i] - top[i]) * ratio) for i in range(3))
        else:
            ratio = (y - mid_y) / max(1, height - mid_y - 1)
            color = tuple(int(mid[i] + (bottom[i] - mid[i]) * ratio) for i in range(3))
        pygame.draw.line(surface, color, (0, y), (width, y))


def draw_rounded_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    *,
    radius: int = 16,
    border: tuple[int, int, int] | None = None,
    border_width: int = 3,
) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border is not None:
        pygame.draw.rect(surface, border, rect, width=border_width, border_radius=radius)


def draw_dashed_rounded_rect(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    *,
    radius: int = 16,
    dash: int = 8,
    gap: int = 6,
    width: int = 2,
) -> None:
    """Approximate dashed border for the stitched board/card look."""
    inner = rect.inflate(-width, -width)
    segments = [
        ((inner.left + radius, inner.top), (inner.right - radius, inner.top)),
        ((inner.right, inner.top + radius), (inner.right, inner.bottom - radius)),
        ((inner.right - radius, inner.bottom), (inner.left + radius, inner.bottom)),
        ((inner.left, inner.bottom - radius), (inner.left, inner.top + radius)),
    ]
    for start, end in segments:
        _draw_dashed_line(surface, color, start, end, dash, gap, width)


def _draw_dashed_line(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    start: tuple[int, int],
    end: tuple[int, int],
    dash: int,
    gap: int,
    width: int,
) -> None:
    x1, y1 = start
    x2, y2 = end
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    dx = (x2 - x1) / length
    dy = (y2 - y1) / length
    pos = 0.0
    draw = True
    while pos < length:
        seg = min(dash if draw else gap, length - pos)
        if draw:
            sx = int(x1 + dx * pos)
            sy = int(y1 + dy * pos)
            ex = int(x1 + dx * (pos + seg))
            ey = int(y1 + dy * (pos + seg))
            pygame.draw.line(surface, color, (sx, sy), (ex, ey), width)
        pos += seg
        draw = not draw


def draw_circle_button(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    fill: tuple[int, int, int],
    *,
    border: tuple[int, int, int] = (255, 255, 255),
    border_width: int = 4,
    shadow: bool = True,
) -> None:
    if shadow:
        shadow_surf = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0, 0, 0, 40), (radius + 4, radius + 6), radius)
        surface.blit(shadow_surf, (center[0] - radius - 4, center[1] - radius - 2))
    pygame.draw.circle(surface, fill, center, radius)
    pygame.draw.circle(surface, border, center, radius, width=border_width)
    highlight = (min(255, fill[0] + 30), min(255, fill[1] + 30), min(255, fill[2] + 30))
    pygame.draw.arc(
        surface,
        highlight,
        pygame.Rect(center[0] - radius + 4, center[1] - radius + 4, (radius - 4) * 2, (radius - 4) * 2),
        math.pi * 0.85,
        math.pi * 1.85,
        3,
    )


def draw_icon_home(surface: pygame.Surface, center: tuple[int, int], size: int = 22) -> None:
    x, y = center
    roof = [(x, y - size // 2), (x - size // 2, y - 2), (x + size // 2, y - 2)]
    pygame.draw.polygon(surface, (255, 255, 255), roof)
    body = pygame.Rect(x - size // 3, y - 2, size * 2 // 3, size // 2 + 2)
    pygame.draw.rect(surface, (255, 255, 255), body, border_radius=2)
    pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(x - 4, y + 2, 8, 8), border_radius=1)


def draw_icon_gear(surface: pygame.Surface, center: tuple[int, int], radius: int = 12) -> None:
    x, y = center
    pygame.draw.circle(surface, (255, 255, 255), center, radius - 4)
    for i in range(8):
        angle = i * math.pi / 4
        ox = int(x + math.cos(angle) * radius)
        oy = int(y + math.sin(angle) * radius)
        pygame.draw.circle(surface, (255, 255, 255), (ox, oy), 4)


def draw_icon_refresh(surface: pygame.Surface, center: tuple[int, int], radius: int = 14) -> None:
    rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
    pygame.draw.arc(surface, (255, 255, 255), rect, math.pi * 0.2, math.pi * 1.5, 3)
    pygame.draw.arc(surface, (255, 255, 255), rect, math.pi * 1.2, math.pi * 2.5, 3)
    tip_x = center[0] + int(math.cos(math.pi * 0.2) * radius)
    tip_y = center[1] + int(math.sin(math.pi * 0.2) * radius)
    pygame.draw.polygon(
        surface,
        (255, 255, 255),
        [(tip_x, tip_y), (tip_x - 6, tip_y - 4), (tip_x - 2, tip_y - 10)],
    )


def draw_icon_bulb(surface: pygame.Surface, center: tuple[int, int]) -> None:
    x, y = center
    pygame.draw.ellipse(surface, (255, 255, 255), pygame.Rect(x - 10, y - 16, 20, 22))
    pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(x - 6, y + 4, 12, 8), border_radius=2)
    pygame.draw.line(surface, (255, 240, 180), (x, y - 8), (x, y + 2), 2)


def draw_icon_mic(surface: pygame.Surface, center: tuple[int, int]) -> None:
    x, y = center
    pygame.draw.ellipse(surface, (255, 255, 255), pygame.Rect(x - 7, y - 14, 14, 20))
    pygame.draw.arc(surface, (255, 255, 255), pygame.Rect(x - 12, y - 4, 24, 20), 0, math.pi, 2)
    pygame.draw.line(surface, (255, 255, 255), (x, y + 14), (x, y + 20), 3)
    pygame.draw.line(surface, (255, 255, 255), (x - 8, y + 20), (x + 8, y + 20), 3)


def draw_icon_speaker(surface: pygame.Surface, center: tuple[int, int]) -> None:
    x, y = center
    pygame.draw.polygon(surface, (255, 255, 255), [(x - 10, y - 6), (x - 2, y - 6), (x + 6, y - 12), (x + 6, y + 12), (x - 2, y + 6), (x - 10, y + 6)])
    for arc_r in (8, 12):
        pygame.draw.arc(surface, (255, 255, 255), pygame.Rect(x - arc_r // 2, y - arc_r, arc_r + 8, arc_r * 2), -0.6, 0.6, 2)
