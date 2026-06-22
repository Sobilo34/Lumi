"""Letter Island — component-built scene matching reference_interfaces/07."""
from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import (
    BOARD_BORDER,
    BOARD_FILL,
    BOARD_STITCH,
    BUTTON_BLUE,
    BUTTON_PINK,
    BUTTON_PURPLE,
    BUTTON_YELLOW,
    CARD_STYLES,
    GREEN_PLUS,
    HUD_CREAM,
    HUD_PINK,
    HUD_PINK_DARK,
    OCEAN,
    OCEAN_LIGHT,
    PROMPT_ACCENT,
    PROMPT_BROWN,
    SAND,
    SAND_SHADOW,
    SKY_BOTTOM,
    SKY_MID,
    SKY_TOP,
    STAR_FACE,
    STAR_YELLOW,
    TEXT_DARK,
    WOOD,
    WOOD_DARK,
    draw_circle_button,
    draw_dashed_rounded_rect,
    draw_icon_bulb,
    draw_icon_gear,
    draw_icon_home,
    draw_icon_mic,
    draw_icon_refresh,
    draw_rounded_rect,
    draw_vertical_gradient,
    font,
    blit_fitted_text,
    blit_outlined_text,
    content_rect,
    draw_3d_block,
    draw_rect_shadow,
    draw_simple_flower,
    draw_sparkle,
    fit_font_size,
    pct_rect,
)

# Layout locked to screen_registry hitboxes @ 1280×720
BOARD_OUTER = pct_rect(0.195, 0.115, 0.61, 0.555)
BOARD_INNER = BOARD_OUTER.inflate(-16, -16)
# Reference 07 — sunset sky, square-ish cards overlapping board bottom slightly
SKY_SUNSET_TOP = (255, 195, 175)
SKY_SUNSET_MID = (255, 215, 200)
CARD_RECTS = (
    pct_rect(0.29, 0.435, 0.13, 0.22),
    pct_rect(0.43, 0.435, 0.13, 0.22),
    pct_rect(0.57, 0.435, 0.13, 0.22),
    pct_rect(0.71, 0.435, 0.13, 0.22),
)
ACTION_CENTERS = (
    (int(SCREEN_WIDTH * 0.36), int(SCREEN_HEIGHT * 0.855)),
    (int(SCREEN_WIDTH * 0.50), int(SCREEN_HEIGHT * 0.855)),
    (int(SCREEN_WIDTH * 0.64), int(SCREEN_HEIGHT * 0.855)),
)

_BACKGROUND: pygame.Surface | None = None


@dataclass(frozen=True)
class LetterIslandView:
    target_letter: str
    slot_letters: tuple[str, ...]
    progress_text: str
    stars_filled: int = 2
    lumi_energy: int = 100
    lumi_energy_max: int = 100
    feedback_message: str = ""
    held_letter: str = ""


def _background_surface() -> pygame.Surface:
    global _BACKGROUND
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    _paint_static_scenery(surf)
    _BACKGROUND = surf
    return _BACKGROUND


def _paint_static_scenery(surface: pygame.Surface) -> None:
    draw_vertical_gradient(surface, SKY_SUNSET_TOP, SKY_SUNSET_MID, SKY_BOTTOM)

    for cx, cy, rx, ry, alpha in (
        (200, 75, 95, 36, 130),
        (480, 48, 125, 42, 150),
        (760, 85, 85, 32, 110),
        (980, 55, 100, 38, 125),
        (1120, 100, 70, 26, 90),
    ):
        cloud = pygame.Surface((rx * 2 + 40, ry * 2 + 20), pygame.SRCALPHA)
        for ox, oy, rxx, ryy in ((20, 10, rx, ry), (rx, 0, rx - 15, ry - 5), (rx + 10, 15, rx - 20, ry - 8)):
            pygame.draw.ellipse(cloud, (255, 255, 255, alpha), (ox, oy, rxx * 2, ryy * 2))
        surface.blit(cloud, (cx - rx - 10, cy - ry))

    for sx, sy in (
        (140, 90), (310, 140), (550, 70), (720, 120), (890, 55), (1040, 130),
        (420, 180), (650, 160), (950, 175),
    ):
        draw_sparkle(surface, sx, sy, size=4 if (sx + sy) % 2 else 3)

    for lx, ly, letter, alpha, sz in (
        (160, 110, "A", 55, 42),
        (1020, 95, "C", 50, 38),
        (1140, 170, "E", 45, 34),
    ):
        glyph = font(sz, bold=True).render(letter, True, (255, 240, 245))
        glyph.set_alpha(alpha)
        surface.blit(glyph, (lx, ly))

    _draw_hot_air_balloon(surface, int(SCREEN_WIDTH * 0.07), int(SCREEN_HEIGHT * 0.05))

    water_y = int(SCREEN_HEIGHT * 0.515)
    pygame.draw.rect(surface, OCEAN, (0, water_y, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.055)))
    for i in range(0, SCREEN_WIDTH + 80, 70):
        pygame.draw.ellipse(surface, OCEAN_LIGHT, pygame.Rect(i - 20, water_y + 8, 90, 18))
    foam_y = water_y + int(SCREEN_HEIGHT * 0.045)
    for fx in range(0, SCREEN_WIDTH, 45):
        pygame.draw.arc(surface, (255, 255, 255), pygame.Rect(fx, foam_y - 6, 36, 14), 0, math.pi, 2)

    sand_top = int(SCREEN_HEIGHT * 0.565)
    pygame.draw.rect(surface, SAND, (0, sand_top, SCREEN_WIDTH, SCREEN_HEIGHT - sand_top))
    pygame.draw.ellipse(surface, SAND_SHADOW, pct_rect(-0.02, 0.555, 1.04, 0.04))

    _draw_palm_tree(surface, int(SCREEN_WIDTH * 0.02), int(SCREEN_HEIGHT * 0.30), flip=False, scale=1.1)
    _draw_palm_tree(surface, int(SCREEN_WIDTH * 0.875), int(SCREEN_HEIGHT * 0.28), flip=True, scale=1.15)

    for fx, fy in ((240, 640), (380, 665), (920, 655), (1020, 680), (180, 690)):
        draw_simple_flower(surface, fx, fy, petal=(255, 165, 190), radius=6)
    for sx, sy, col in ((320, 652, (255, 200, 210)), (860, 668, (255, 185, 200))):
        pygame.draw.ellipse(surface, col, pygame.Rect(sx, sy, 14, 10))
    for sx, sy in ((350, 678), (890, 692)):
        _draw_starfish(surface, sx, sy)

    post_x = int(SCREEN_WIDTH * 0.055)
    pygame.draw.rect(surface, WOOD_DARK, (post_x, int(SCREEN_HEIGHT * 0.62), 10, int(SCREEN_HEIGHT * 0.16)), border_radius=3)
    sign = pct_rect(0.035, 0.745, 0.155, 0.105)
    draw_rect_shadow(surface, sign, radius=10, offset=(2, 4), alpha=30)
    draw_rounded_rect(surface, sign, WOOD, radius=10, border=WOOD_DARK, border_width=3)
    sign_text = font(20, bold=True).render("Letter Island", True, (255, 255, 255))
    surface.blit(sign_text, sign_text.get_rect(center=(sign.centerx, sign.centery + 4)))

    for xp, yp, letter, col in (
        (0.838, 0.665, "A", (255, 130, 145)),
        (0.858, 0.615, "B", (175, 140, 255)),
        (0.878, 0.565, "C", (255, 215, 95)),
    ):
        draw_3d_block(surface, pct_rect(xp, yp, 0.052, 0.078), letter, col, depth=7)


def _draw_hot_air_balloon(surface: pygame.Surface, bx: int, by: int) -> None:
    body = pygame.Rect(bx, by, 78, 98)
    draw_rect_shadow(surface, body, radius=40, offset=(3, 6), alpha=25)
    pygame.draw.ellipse(surface, (255, 165, 185), body)
    for stripe_y in (by + 18, by + 38, by + 58, by + 78):
        pygame.draw.line(surface, (255, 210, 225), (bx + 8, stripe_y), (bx + 70, stripe_y), 3)
    pygame.draw.ellipse(surface, (255, 230, 240), pygame.Rect(bx + 14, by + 14, 50, 62))
    pygame.draw.rect(surface, WOOD, pygame.Rect(bx + 28, by + 96, 22, 16), border_radius=3)
    pygame.draw.line(surface, WOOD_DARK, (bx + 34, by + 92), (bx + 34, by + 96), 2)
    pygame.draw.line(surface, WOOD_DARK, (bx + 44, by + 92), (bx + 44, by + 96), 2)


def _draw_starfish(surface: pygame.Surface, x: int, y: int) -> None:
    points: list[tuple[int, int]] = []
    for i in range(5):
        angle = i * math.pi * 2 / 5 - math.pi / 2
        points.append((x + int(math.cos(angle) * 10), y + int(math.sin(angle) * 10)))
        angle += math.pi / 5
        points.append((x + int(math.cos(angle) * 4), y + int(math.sin(angle) * 4)))
    pygame.draw.polygon(surface, (255, 150, 110), points)


def _draw_palm_tree(surface: pygame.Surface, x: int, y: int, *, flip: bool, scale: float = 1.0) -> None:
    trunk_w = int(32 * scale)
    trunk_h = int(SCREEN_HEIGHT * 0.24 * scale)
    trunk = pygame.Rect(x, y, trunk_w, trunk_h)
    pygame.draw.rect(surface, (139, 90, 48), trunk, border_radius=8)
    highlight = trunk.inflate(-10, 0)
    pygame.draw.rect(surface, (175, 115, 62), highlight, border_radius=6)
    cx = x + trunk_w // 2
    crown_y = y + 6
    for i, length in enumerate((62, 58, 54, 50, 46, 42)):
        angle = -0.55 + i * 0.32
        if flip:
            angle = math.pi - angle
        ex = cx + int(math.cos(angle) * length * scale)
        ey = crown_y + int(math.sin(angle) * length * 0.5 * scale)
        width = 11 if i in (2, 3) else 8
        pygame.draw.line(surface, (55, 145, 78), (cx, crown_y), (ex, ey), width)
        pygame.draw.ellipse(surface, (75, 168, 98), pygame.Rect(ex - 12, ey - 6, 24, 14))
    for ox in (-8, 8):
        pygame.draw.circle(surface, (110, 70, 40), (cx + ox, y + trunk_h - 18), int(7 * scale))


def _draw_lumi_mascot(surface: pygame.Surface, held_letter: str) -> None:
    center = (int(SCREEN_WIDTH * 0.125), int(SCREEN_HEIGHT * 0.58))
    glow = pygame.Surface((140, 140), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 240, 150, 60), (70, 70), 58)
    surface.blit(glow, (center[0] - 70, center[1] - 70))

    def star_points(cx: int, cy: int, outer: int, inner: int, rot: float = -math.pi / 2) -> list[tuple[int, int]]:
        pts: list[tuple[int, int]] = []
        for i in range(10):
            angle = i * math.pi / 5 + rot
            radius = outer if i % 2 == 0 else inner
            pts.append((cx + int(radius * math.cos(angle)), cy + int(radius * math.sin(angle))))
        return pts

    body = star_points(center[0], center[1], 54, 24)
    pygame.draw.polygon(surface, STAR_FACE, body)
    pygame.draw.polygon(surface, (235, 175, 45), body, width=5)
    # Waving arm (extended upper-right point)
    wave_tip = star_points(center[0], center[1], 62, 26, rot=-math.pi / 2 + 0.15)[1]
    pygame.draw.line(surface, (255, 235, 130), center, wave_tip, 6)

    for ex, highlight_x in ((center[0] - 16, center[0] - 18), (center[0] + 16, center[0] + 14)):
        pygame.draw.circle(surface, (35, 35, 35), (ex, center[1] - 8), 7)
        pygame.draw.circle(surface, (255, 255, 255), (highlight_x, center[1] - 10), 3)
    for cheek_x in (center[0] - 24, center[0] + 24):
        blush = pygame.Surface((20, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(blush, (255, 160, 180, 120), blush.get_rect())
        surface.blit(blush, (cheek_x - 10, center[1] + 2))
    pygame.draw.arc(surface, (120, 72, 48), pygame.Rect(center[0] - 18, center[1] + 4, 36, 20), 3.4, 6.0, 3)

    tile = pygame.Rect(center[0] + 38, center[1] - 62, 48, 48)
    draw_rect_shadow(surface, tile, radius=10, offset=(1, 3), alpha=25)
    draw_rounded_rect(surface, tile, (225, 210, 245), radius=12, border=(190, 160, 220), border_width=3)
    blit_fitted_text(surface, tile, (held_letter or "B").upper(), (155, 95, 195), padding=8, fill_height_ratio=0.62)


def _draw_top_hud(surface: pygame.Surface, view: LetterIslandView) -> None:
    # Home and settings are drawn from shipped control art via hitbox overlay.
    hud = pct_rect(0.075, 0.018, 0.195, 0.095)
    draw_rounded_rect(surface, hud, HUD_CREAM, radius=20, border=HUD_PINK, border_width=2)
    avatar = pygame.Rect(hud.x + 8, hud.y + 10, 42, 42)
    draw_rounded_rect(surface, avatar, STAR_YELLOW, radius=12, border=(255, 255, 255), border_width=2)
    mini = font(22, bold=True).render("★", True, (255, 255, 255))
    surface.blit(mini, mini.get_rect(center=avatar.center))
    name = font(19, bold=True).render("Lumi", True, HUD_PINK_DARK)
    surface.blit(name, (hud.x + 58, hud.y + 12))
    energy_text = font(15, bold=True).render(f"⚡ {view.lumi_energy}/{view.lumi_energy_max}", True, TEXT_DARK)
    surface.blit(energy_text, (hud.x + 58, hud.y + 36))
    bar = pygame.Rect(hud.x + 58, hud.y + 58, 100, 9)
    pygame.draw.rect(surface, (255, 255, 255), bar, border_radius=5)
    fill_w = int(bar.width * min(1.0, view.lumi_energy / max(1, view.lumi_energy_max)))
    if fill_w:
        pygame.draw.rect(surface, HUD_PINK, pygame.Rect(bar.x, bar.y, fill_w, bar.height), border_radius=5)
    plus_c = (hud.right - 22, hud.centery + 8)
    pygame.draw.circle(surface, GREEN_PLUS, plus_c, 12)
    pygame.draw.line(surface, (255, 255, 255), (plus_c[0] - 5, plus_c[1]), (plus_c[0] + 5, plus_c[1]), 2)
    pygame.draw.line(surface, (255, 255, 255), (plus_c[0], plus_c[1] - 5), (plus_c[0], plus_c[1] + 5), 2)

    # Journey progress (centre top)
    progress = pct_rect(0.34, 0.018, 0.32, 0.055)
    draw_rounded_rect(surface, progress, (255, 255, 255), radius=16, border=HUD_PINK, border_width=2)
    progress_label = font(16, bold=True).render(view.progress_text, True, TEXT_DARK)
    surface.blit(progress_label, progress_label.get_rect(center=progress.center))

    # Star rating
    stars_rect = pct_rect(0.735, 0.018, 0.125, 0.055)
    draw_rounded_rect(surface, stars_rect, (255, 255, 255), radius=16, border=HUD_PINK, border_width=2)
    for i in range(3):
        sx = stars_rect.x + 22 + i * 32
        sy = stars_rect.centery
        filled = i < view.stars_filled
        color = STAR_YELLOW if filled else (225, 205, 215)
        star = font(24, bold=True).render("★", True, color)
        surface.blit(star, star.get_rect(center=(sx, sy)))


def _draw_game_board(surface: pygame.Surface, view: LetterIslandView) -> None:
    draw_rect_shadow(surface, BOARD_OUTER, radius=32, offset=(0, 8), alpha=35)
    draw_rounded_rect(surface, BOARD_OUTER, BOARD_BORDER, radius=32)
    draw_rounded_rect(surface, BOARD_INNER, BOARD_FILL, radius=26)
    stitch = BOARD_INNER.inflate(-10, -10)
    draw_dashed_rounded_rect(surface, stitch, BOARD_STITCH, radius=22, dash=7, gap=5)

    for px, py, kind in ((0.06, 0.06, "star"), (0.90, 0.06, "flower"), (0.06, 0.88, "flower"), (0.90, 0.88, "star")):
        cx = BOARD_INNER.x + int(BOARD_INNER.width * px)
        cy = BOARD_INNER.y + int(BOARD_INNER.height * py)
        if kind == "star":
            draw_sparkle(surface, cx, cy, size=6, color=STAR_YELLOW)
        else:
            draw_simple_flower(surface, cx, cy, petal=(255, 170, 195), radius=5)

    _draw_find_prompt(surface, view.target_letter)
    for index, card_rect in enumerate(CARD_RECTS):
        if index >= len(view.slot_letters):
            break
        style = CARD_STYLES[index % len(CARD_STYLES)]
        _draw_letter_card(surface, card_rect, view.slot_letters[index], style)


def _draw_find_prompt(surface: pygame.Surface, target_letter: str) -> None:
    cx = BOARD_INNER.centerx
    cy = BOARD_INNER.y + int(BOARD_INNER.height * 0.13)
    letter = target_letter.upper()
    find_label = font(44, bold=True).render("Find", True, PROMPT_BROWN)
    letter_bounds = pygame.Rect(0, 0, int(BOARD_INNER.width * 0.16), int(BOARD_INNER.height * 0.20))
    letter_size = fit_font_size(letter, letter_bounds, fill_height_ratio=0.90, bold=True)
    gap = 14
    letter_w = font(letter_size, bold=True).size(letter)[0]
    total_w = find_label.get_width() + gap + letter_w
    x = cx - total_w // 2
    surface.blit(find_label, (x, cy + 6))
    blit_outlined_text(
        surface,
        letter,
        (x + find_label.get_width() + gap + letter_w // 2, cy),
        letter_size,
        PROMPT_ACCENT,
        outline=(255, 255, 255),
        outline_width=2,
    )


def _draw_letter_card(surface: pygame.Surface, rect: pygame.Rect, letter: str, style: dict) -> None:
    draw_rect_shadow(surface, rect, radius=20, offset=(0, 4), alpha=28)
    draw_rounded_rect(surface, rect, style["bg"], radius=20, border=style["border"], border_width=4)
    inner = rect.inflate(-8, -8)
    highlight = pygame.Rect(inner.x + 4, inner.y + 4, inner.width - 8, inner.height // 3)
    hi_surf = pygame.Surface((highlight.width, highlight.height), pygame.SRCALPHA)
    hi_surf.fill((255, 255, 255, 35))
    surface.blit(hi_surf, highlight.topleft)
    draw_dashed_rounded_rect(surface, inner, style["border"], radius=16, dash=6, gap=4, width=2)
    blit_fitted_text(
        surface,
        content_rect(rect, padding=16),
        letter.upper(),
        style["fg"],
        padding=0,
        fill_height_ratio=0.72,
        shadow=(50, 38, 48),
    )


def _draw_action_buttons(surface: pygame.Surface) -> None:
    """Repeat, hint, and speak buttons are drawn via hitbox overlay."""
    return


def _draw_speech_bubble(surface: pygame.Surface, message: str) -> None:
    bubble = pct_rect(0.055, 0.045, 0.34, 0.13)
    draw_rounded_rect(surface, bubble, (255, 255, 255), radius=20, border=HUD_PINK, border_width=2)
    tail = [(bubble.x + 50, bubble.bottom), (bubble.x + 30, bubble.bottom + 18), (bubble.x + 80, bubble.bottom)]
    pygame.draw.polygon(surface, (255, 255, 255), tail)
    pygame.draw.lines(surface, HUD_PINK, False, [(tail[0][0], tail[0][1]), tail[1], tail[2]], 2)
    y = bubble.y + 12
    for line in _wrap(font(17, bold=True), message, bubble.width - 24):
        label = font(17, bold=True).render(line, True, TEXT_DARK)
        surface.blit(label, (bubble.x + 14, y))
        y += label.get_height() + 2


def _draw_bd_hint_panel(surface: pygame.Surface) -> None:
    """B-vs-D belly hint panel (reference 09_letter_mistake_hint.png)."""
    panel = pct_rect(0.22, 0.62, 0.56, 0.14)
    draw_rounded_rect(surface, panel, (255, 255, 255), radius=16, border=BOARD_STITCH, border_width=2)
    b_rect = pygame.Rect(panel.x + 30, panel.centery - 28, 56, 56)
    d_rect = pygame.Rect(panel.right - 86, panel.centery - 28, 56, 56)
    for r, letter, col in ((b_rect, "B", (155, 95, 195)), (d_rect, "D", (85, 165, 105))):
        draw_rounded_rect(surface, r, (245, 240, 250), radius=10, border=col, border_width=2)
        blit_fitted_text(surface, r, letter, col, padding=8, fill_height_ratio=0.65)
    hint = font(18, bold=True).render("B has a belly.", True, TEXT_DARK)
    surface.blit(hint, hint.get_rect(center=(panel.centerx, panel.centery + 38)))


def _draw_success_panel(surface: pygame.Surface, view: LetterIslandView) -> None:
    panel = pct_rect(0.30, 0.32, 0.40, 0.22)
    draw_rounded_rect(surface, panel, (255, 255, 255), radius=22, border=STAR_YELLOW, border_width=4)
    letter_area = pygame.Rect(panel.x + 40, panel.y + 16, panel.width - 80, int(panel.height * 0.55))
    blit_fitted_text(
        surface,
        letter_area,
        view.target_letter.upper(),
        PROMPT_ACCENT,
        padding=0,
        fill_height_ratio=0.82,
    )
    message = view.feedback_message or f"Great job! This is {view.target_letter.upper()}."
    for i, line in enumerate(_wrap(font(18, bold=True), message, panel.width - 30)):
        msg = font(18, bold=True).render(line, True, TEXT_DARK)
        surface.blit(msg, msg.get_rect(center=(panel.centerx, panel.bottom - 36 + i * 22)))


def _draw_mistake_footer_buttons(surface: pygame.Surface) -> None:
    for x_pct, label in ((0.26, "Try Again"), (0.45, "Repeat"), (0.64, "Hint")):
        btn = pct_rect(x_pct, 0.795, 0.17, 0.085)
        draw_rounded_rect(surface, btn, BUTTON_PINK, radius=16, border=(255, 255, 255), border_width=2)
        text = font(17, bold=True).render(label, True, (255, 255, 255))
        surface.blit(text, text.get_rect(center=btn.center))


def _wrap(text_font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if text_font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _render_base(surface: pygame.Surface, view: LetterIslandView) -> None:
    from ui.app_background import paint_app_background

    if not paint_app_background(surface):
        surface.blit(_background_surface(), (0, 0))
    _draw_lumi_mascot(surface, view.held_letter or view.target_letter)
    _draw_top_hud(surface, view)
    _draw_game_board(surface, view)
    _draw_action_buttons(surface)


def render_letter_island_gameplay(surface: pygame.Surface, view: LetterIslandView) -> None:
    _render_base(surface, view)


def render_letter_island_correct(surface: pygame.Surface, view: LetterIslandView) -> None:
    _render_base(surface, view)
    _draw_success_panel(surface, view)


def render_letter_island_mistake(surface: pygame.Surface, view: LetterIslandView) -> None:
    _render_base(surface, view)
    if view.feedback_message:
        _draw_speech_bubble(surface, view.feedback_message)
    if "belly" in view.feedback_message.lower():
        _draw_bd_hint_panel(surface)
    _draw_mistake_footer_buttons(surface)
