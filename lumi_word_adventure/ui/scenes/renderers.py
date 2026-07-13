"""Component renderers for every Lumi Word Adventure screen."""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.letter_island_scene import (
    LetterIslandView,
    render_letter_island_gameplay,
)
from ui.components.primitives import (
    BOARD_BORDER,
    BOARD_STITCH,
    BUTTON_BLUE,
    BUTTON_PINK,
    BUTTON_PURPLE,
    BUTTON_YELLOW,
    CARD_STYLES,
    HUD_PINK,
    HUD_PINK_DARK,
    PROMPT_ACCENT,
    PROMPT_BROWN,
    SAND,
    STAR_YELLOW,
    TEXT_DARK,
    blit_fitted_text,
    blit_outlined_text,
    draw_circle_button,
    draw_dashed_rounded_rect,
    display_font,
    draw_icon_bulb,
    draw_icon_home,
    draw_icon_mic,
    draw_icon_refresh,
    draw_icon_speaker,
    draw_rounded_rect,
    draw_rect_shadow,
    font,
    pct_rect,
)
from ui.scene_view import SceneView
from ui.themes.chrome import (
    draw_corner_nav,
    draw_cta_button,
    draw_logo_banner,
    draw_lumi_hud,
    draw_lumi_mascot_large,
    draw_menu_button,
    draw_pink_cta_button,
    draw_speech_bubble,
    draw_stitched_panel,
)
from ui.themes.menu_bg import paint_loading_bar, paint_pink_sky

SceneRenderer = Callable[[pygame.Surface, SceneView], None]

_PROGRESS_BTN_DIR = Path(__file__).resolve().parents[2] / "assets" / "ui_chunks" / "progress_complete"
_PROGRESS_BUTTONS: dict[str, pygame.Surface] = {}

# Bottom row: three pill buttons evenly centered.
_PROGRESS_BTN_RECTS = (
    ("next_world.png", pct_rect(0.105, 0.80, 0.24, 0.12)),
    ("practice_again.png", pct_rect(0.38, 0.80, 0.24, 0.12)),
    ("view_report.png", pct_rect(0.655, 0.80, 0.24, 0.12)),
)


def _dramatic_text(
    surface: pygame.Surface,
    value: str,
    size: int,
    center: tuple[int, int],
    color: tuple[int, int, int],
    *,
    outline: tuple[int, int, int] = (180, 95, 40),
) -> None:
    f = display_font(size)
    outline_width = max(3, size // 18)
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy > outline_width * outline_width:
                continue
            if dx == 0 and dy == 0:
                continue
            layer = f.render(value, True, outline)
            surface.blit(layer, layer.get_rect(center=(center[0] + dx, center[1] + dy)))
    label = f.render(value, True, color)
    surface.blit(label, label.get_rect(center=center))


def _progress_button_surface(filename: str) -> pygame.Surface | None:
    cached = _PROGRESS_BUTTONS.get(filename)
    if cached is not None:
        return cached
    path = _PROGRESS_BTN_DIR / filename
    if not path.is_file():
        return None
    try:
        image = pygame.image.load(str(path)).convert_alpha()
    except (pygame.error, FileNotFoundError, OSError):
        return None
    _PROGRESS_BUTTONS[filename] = image
    return image


def _blit_progress_button(surface: pygame.Surface, rect: pygame.Rect, filename: str) -> bool:
    image = _progress_button_surface(filename)
    if image is None:
        return False
    source_w, source_h = image.get_size()
    if source_w <= 0 or source_h <= 0:
        return False
    scale = min(rect.width / source_w, rect.height / source_h)
    target_w = max(1, int(source_w * scale))
    target_h = max(1, int(source_h * scale))
    if target_w != source_w or target_h != source_h:
        image = pygame.transform.smoothscale(image, (target_w, target_h))
    surface.blit(image, image.get_rect(center=rect.center))
    return True


def _draw_outline_star(surface: pygame.Surface, center: tuple[int, int], size: int) -> None:
    cx, cy = center
    points: list[tuple[int, int]] = []
    for i in range(10):
        angle = i * math.pi / 5 - math.pi / 2
        radius = size if i % 2 == 0 else size // 2
        points.append((cx + int(radius * math.cos(angle)), cy + int(radius * math.sin(angle))))
    pygame.draw.polygon(surface, (225, 205, 215), points)
    pygame.draw.polygon(surface, (190, 170, 185), points, width=max(2, size // 12))


def _draw_progress_complete_stars(surface: pygame.Surface, center: tuple[int, int], filled: int) -> None:
    from ui.dynamic_layers import _draw_filled_star

    size = 36
    gap = int(size * 1.18)
    start_x = center[0] - gap
    filled = max(0, min(3, int(filled)))
    for index in range(3):
        cx = start_x + index * gap
        if index < filled:
            _draw_filled_star(surface, (cx, center[1]), size)
        else:
            _draw_outline_star(surface, (cx, center[1]), size)


def _text(surface: pygame.Surface, value: str, size: int, center: tuple[int, int], color: tuple[int, int, int], *, bold: bool = True) -> None:
    label = font(size, bold=bold).render(value, True, color)
    surface.blit(label, label.get_rect(center=center))


def _blit_lines(
    surface: pygame.Surface,
    lines: list[str],
    start: tuple[int, int],
    *,
    size: int = 26,
    color: tuple[int, int, int] = TEXT_DARK,
    line_gap: int = 8,
    bold: bool = True,
) -> None:
    y = start[1]
    for line in lines:
        label = font(size, bold=bold).render(line, True, color)
        surface.blit(label, (start[0], y))
        y += label.get_height() + line_gap


def _wrap(text: str, max_width: int, *, size: int = 24, bold: bool = True) -> list[str]:
    words = (text or "").split()
    if not words:
        return [""]
    wrapped: list[str] = []
    active = words[0]
    draw_font = font(size, bold=bold)
    for word in words[1:]:
        trial = f"{active} {word}"
        if draw_font.size(trial)[0] <= max_width:
            active = trial
        else:
            wrapped.append(active)
            active = word
    wrapped.append(active)
    return wrapped


def _safe_word_slots(slot_words: tuple[str, ...]) -> tuple[str, str, str, str]:
    fallback = ("sun", "apple", "fish", "bird")
    if len(slot_words) >= 4:
        return tuple(str(word or "").lower() for word in slot_words[:4])  # type: ignore[return-value]
    merged = list(str(word or "").lower() for word in slot_words)
    while len(merged) < 4:
        merged.append(fallback[len(merged)])
    return tuple(merged[:4])  # type: ignore[return-value]


def _letter_island_view(view: SceneView) -> LetterIslandView:
    slots = tuple(str(letter or "").upper() for letter in view.slot_letters[:4])
    if not slots:
        slots = ("B", "D", "P", "A")
    return LetterIslandView(
        target_letter=str(view.target_letter or "A").upper(),
        slot_letters=slots,
        progress_text=view.progress_text or "Letter journey",
        stars_filled=max(0, min(3, int(view.stars_filled))),
        lumi_energy=max(0, int(view.lumi_energy)),
        lumi_energy_max=max(1, int(view.lumi_energy_max)),
        feedback_message=str(view.feedback_message or ""),
        held_letter=str(view.held_letter or view.target_letter or "A").upper(),
    )


def _draw_soft_hills(surface: pygame.Surface, palette: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]) -> None:
    left = pct_rect(-0.05, 0.49, 0.52, 0.30)
    mid = pct_rect(0.20, 0.52, 0.56, 0.32)
    right = pct_rect(0.60, 0.50, 0.45, 0.28)
    pygame.draw.ellipse(surface, palette[0], left)
    pygame.draw.ellipse(surface, palette[1], mid)
    pygame.draw.ellipse(surface, palette[2], right)


def _draw_world_node(surface: pygame.Surface, x_pct: float, y_pct: float, label: str, color: tuple[int, int, int]) -> None:
    center = (int(SCREEN_WIDTH * x_pct), int(SCREEN_HEIGHT * y_pct))
    radius = int(SCREEN_HEIGHT * 0.095)
    pygame.draw.circle(surface, color, center, radius)
    pygame.draw.circle(surface, (255, 255, 255), center, radius, 4)
    pygame.draw.circle(surface, (255, 255, 255), (center[0] - 18, center[1] - 16), 8)
    pygame.draw.circle(surface, (255, 255, 255), (center[0] + 18, center[1] - 16), 8)
    pygame.draw.arc(surface, PROMPT_BROWN, pygame.Rect(center[0] - 26, center[1] - 2, 52, 24), 3.30, 6.10, 3)
    panel = pct_rect(x_pct - 0.09, y_pct + 0.12, 0.18, 0.07)
    draw_rounded_rect(surface, panel, (255, 255, 255), radius=12, border=HUD_PINK, border_width=2)
    _text(surface, label, 22, panel.center, HUD_PINK_DARK)


def _draw_footer_action_triplet(surface: pygame.Surface) -> None:
    centers = (
        (int(SCREEN_WIDTH * 0.36), int(SCREEN_HEIGHT * 0.855)),
        (int(SCREEN_WIDTH * 0.50), int(SCREEN_HEIGHT * 0.855)),
        (int(SCREEN_WIDTH * 0.64), int(SCREEN_HEIGHT * 0.855)),
    )
    specs = (
        (centers[0], BUTTON_PURPLE, draw_icon_refresh),
        (centers[1], BUTTON_YELLOW, draw_icon_bulb),
        (centers[2], BUTTON_BLUE, draw_icon_mic),
    )
    for center, color, icon_fn in specs:
        draw_circle_button(surface, center, 42, color)
        icon_fn(surface, center)


def _paint_word_garden_background(surface: pygame.Surface) -> None:
    paint_pink_sky(surface)
    _draw_soft_hills(surface, ((175, 224, 168), (138, 206, 153), (196, 236, 184)))
    path = pct_rect(0.05, 0.62, 0.90, 0.33)
    pygame.draw.ellipse(surface, SAND, path)
    pygame.draw.ellipse(surface, (245, 211, 159), path.inflate(-180, -80))
    hedge_left = pct_rect(-0.04, 0.56, 0.33, 0.25)
    hedge_right = pct_rect(0.73, 0.58, 0.33, 0.23)
    pygame.draw.ellipse(surface, (131, 190, 123), hedge_left)
    pygame.draw.ellipse(surface, (131, 190, 123), hedge_right)
    for x_pct, y_pct, color in (
        (0.12, 0.67, (255, 146, 170)),
        (0.16, 0.71, (255, 195, 94)),
        (0.86, 0.70, (255, 146, 170)),
        (0.81, 0.66, (255, 195, 94)),
    ):
        pygame.draw.circle(surface, color, (int(SCREEN_WIDTH * x_pct), int(SCREEN_HEIGHT * y_pct)), 12)


def _paint_room_background(surface: pygame.Surface) -> None:
    from ui.app_background import paint_app_background

    if paint_app_background(surface):
        return
    surface.fill((248, 236, 246))
    wall = pct_rect(0.0, 0.0, 1.0, 0.70)
    floor = pct_rect(0.0, 0.70, 1.0, 0.30)
    pygame.draw.rect(surface, (244, 226, 240), wall)
    pygame.draw.rect(surface, (233, 205, 196), floor)
    pygame.draw.line(surface, (217, 187, 205), (0, floor.y), (SCREEN_WIDTH, floor.y), 3)
    window = pct_rect(0.08, 0.12, 0.22, 0.24)
    draw_rounded_rect(surface, window, (207, 232, 252), radius=14, border=(190, 165, 200), border_width=3)
    pygame.draw.line(surface, (190, 165, 200), (window.centerx, window.y), (window.centerx, window.bottom), 2)
    pygame.draw.line(surface, (190, 165, 200), (window.x, window.centery), (window.right, window.centery), 2)
    shelf = pct_rect(0.70, 0.20, 0.20, 0.03)
    pygame.draw.rect(surface, (191, 150, 122), shelf, border_radius=5)
    for i, color in enumerate(((255, 180, 166), (166, 198, 255), (255, 219, 130))):
        book = pygame.Rect(shelf.x + 18 + i * 36, shelf.y - 42, 24, 42)
        pygame.draw.rect(surface, color, book, border_radius=4)


def _draw_profile_card(surface: pygame.Surface, rect: pygame.Rect, name: str, *, accent: tuple[int, int, int]) -> None:
    draw_rounded_rect(surface, rect, (255, 255, 255), radius=22, border=accent, border_width=4)
    avatar = pygame.Rect(rect.centerx - 52, rect.y + 36, 104, 104)
    draw_rounded_rect(surface, avatar, accent, radius=20, border=(255, 255, 255), border_width=3)
    _text(surface, "★", 54, avatar.center, (255, 255, 255))
    _text(surface, name, 28, (rect.centerx, rect.bottom - 56), HUD_PINK_DARK)


def _draw_word_card(surface: pygame.Surface, rect: pygame.Rect, text_value: str, style: dict[str, Any]) -> None:
    draw_rounded_rect(surface, rect, style["bg"], radius=18, border=style["border"], border_width=3)
    draw_dashed_rounded_rect(surface, rect.inflate(-6, -6), style["border"], radius=14, dash=6, gap=4, width=2)
    blit_fitted_text(
        surface,
        rect,
        text_value.lower(),
        style["fg"],
        padding=16,
        shadow=(60, 45, 55),
    )


def _draw_toggle(surface: pygame.Surface, rect: pygame.Rect, enabled: bool) -> None:
    back = (125, 202, 134) if enabled else (208, 190, 205)
    knob_x = rect.right - rect.height // 2 if enabled else rect.x + rect.height // 2
    draw_rounded_rect(surface, rect, back, radius=rect.height // 2)
    pygame.draw.circle(surface, (255, 255, 255), (knob_x, rect.centery), rect.height // 2 - 3)


def _report_value(report: dict[str, Any], key: str, fallback: str) -> str:
    value = report.get(key, fallback)
    return str(value if value not in (None, "") else fallback)


def _draw_section_title(
    surface: pygame.Surface,
    text: str,
    center: tuple[int, int],
    *,
    size: int = 30,
    color: tuple[int, int, int] = HUD_PINK_DARK,
) -> None:
    blit_outlined_text(
        surface,
        text,
        center,
        size,
        color,
        outline=(255, 255, 255),
        outline_width=3,
    )


def _draw_report_stat_row(
    surface: pygame.Surface,
    panel: pygame.Rect,
    y: int,
    label: str,
    value: str,
    *,
    accent: tuple[int, int, int],
) -> None:
    row = pygame.Rect(panel.x + 16, y, panel.width - 32, 58)
    draw_rect_shadow(surface, row, radius=14, offset=(0, 3), alpha=22)
    draw_rounded_rect(surface, row, (255, 255, 255), radius=14, border=accent, border_width=2)
    label_font = font(20, bold=True)
    value_font = font(22, bold=True)
    label_surf = label_font.render(label, True, PROMPT_BROWN)
    value_surf = value_font.render(value, True, HUD_PINK_DARK)
    surface.blit(label_surf, (row.x + 16, row.centery - label_surf.get_height() // 2))
    surface.blit(value_surf, (row.right - value_surf.get_width() - 16, row.centery - value_surf.get_height() // 2))


def _draw_settings_row(
    surface: pygame.Surface,
    panel: pygame.Rect,
    row_rect: pygame.Rect,
    title: str,
    subtitle: str,
    control_rect: pygame.Rect,
    *,
    accent: tuple[int, int, int],
    control_value: str | None = None,
    toggle_on: bool | None = None,
) -> None:
    draw_rect_shadow(surface, row_rect, radius=16, offset=(0, 3), alpha=18)
    draw_rounded_rect(surface, row_rect, (255, 255, 255), radius=16, border=accent, border_width=2)
    title_font = font(24, bold=True)
    subtitle_font = font(16, bold=False)
    title_surf = title_font.render(title, True, HUD_PINK_DARK)
    subtitle_surf = subtitle_font.render(subtitle, True, PROMPT_BROWN)
    text_x = row_rect.x + 20
    title_y = row_rect.centery - (title_surf.get_height() + subtitle_surf.get_height() + 4) // 2
    surface.blit(title_surf, (text_x, title_y))
    surface.blit(subtitle_surf, (text_x, title_y + title_surf.get_height() + 4))
    if toggle_on is not None:
        _draw_toggle(surface, control_rect, toggle_on)
        state = "ON" if toggle_on else "OFF"
        _text(surface, state, 18, control_rect.center, (255, 255, 255))
    elif control_value is not None:
        draw_menu_button(surface, control_rect, control_value, accent=accent)


def render_splash_loading(surface: pygame.Surface, view: SceneView) -> None:
    from ui.loading import draw_spinner

    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.20)
    draw_lumi_mascot_large(surface, x_pct=0.5, y_pct=0.48, scale=1.2)
    bubble_text = view.feedback_message or "Warming up your learning adventure..."
    draw_speech_bubble(surface, bubble_text, x_pct=0.36, y_pct=0.62, w_pct=0.30)
    paint_loading_bar(surface, float(view.loading_progress or 0.0))
    draw_spinner(
        surface,
        (SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.72)),
        radius=24,
        started_at_ms=pygame.time.get_ticks(),
    )


def render_welcome(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.10)
    draw_lumi_mascot_large(surface, x_pct=0.22, y_pct=0.56, scale=1.15)
    bubble = view.feedback_message or "Hi! I'm Lumi! Let's learn together!"
    draw_speech_bubble(surface, bubble, x_pct=0.44, y_pct=0.36, w_pct=0.42)
    speaker_c = (int(SCREEN_WIDTH * 0.05), int(SCREEN_HEIGHT * 0.09))
    draw_circle_button(surface, speaker_c, 30, BUTTON_PINK)
    draw_icon_speaker(surface, speaker_c)
    for x_pct in (0.91, 0.96):
        c = (int(SCREEN_WIDTH * x_pct), int(SCREEN_HEIGHT * 0.09))
        draw_circle_button(surface, c, 26, BUTTON_PINK)
    draw_pink_cta_button(surface, pct_rect(0.38, 0.78, 0.24, 0.13), "Start")


def render_profile_selection(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_corner_nav(surface, show_home=True, show_settings=True)
    header = pct_rect(0.25, 0.11, 0.50, 0.10)
    draw_rounded_rect(surface, header, (255, 255, 255), radius=20, border=HUD_PINK, border_width=3)
    _text(surface, "Choose Your Profile", 40, header.center, HUD_PINK_DARK)
    _draw_profile_card(surface, pct_rect(0.22, 0.28, 0.18, 0.45), "Player 1", accent=(255, 198, 96))
    _draw_profile_card(surface, pct_rect(0.43, 0.28, 0.18, 0.45), "Player 2", accent=(170, 192, 255))
    _draw_profile_card(surface, pct_rect(0.65, 0.28, 0.18, 0.45), "New Player", accent=(202, 170, 240))
    if view.feedback_message:
        draw_speech_bubble(surface, view.feedback_message, x_pct=0.34, y_pct=0.76, w_pct=0.34)


def _draw_disabled_menu_button(surface: pygame.Surface, rect: pygame.Rect, label: str) -> None:
    draw_rounded_rect(surface, rect, (196, 198, 210), radius=18, border=(225, 228, 238), border_width=3)
    text = font(22, bold=True).render(label, True, (130, 136, 152))
    surface.blit(text, text.get_rect(center=rect.center))
    soon = font(14, bold=True).render("Coming soon", True, (150, 156, 170))
    surface.blit(soon, soon.get_rect(center=(rect.centerx, rect.bottom - 14)))


def render_main_menu(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.08)
    draw_lumi_mascot_large(surface, x_pct=0.26, y_pct=0.58, scale=1.3)
    draw_menu_button(surface, pct_rect(0.57, 0.19, 0.33, 0.17), "Play", accent=(255, 196, 91))
    _draw_disabled_menu_button(surface, pct_rect(0.57, 0.40, 0.33, 0.16), "Practice")
    draw_menu_button(surface, pct_rect(0.57, 0.59 - (20 / 720), 0.33, 0.15), "Report", accent=(196, 174, 241))
    draw_menu_button(surface, pct_rect(0.57, 0.76 - (60 / 720), 0.33, 0.15), "Settings", accent=(255, 166, 186))
    if view.feedback_message:
        draw_speech_bubble(surface, view.feedback_message, x_pct=0.10, y_pct=0.20, w_pct=0.34)


def render_how_to_play(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.07)
    panel_outer = pct_rect(0.15, 0.24, 0.70, 0.50)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(235, 150, 165))
    instructions = view.feedback_message or (
        "1. Listen to Lumi.\n"
        "2. Tap the right answer card.\n"
        "3. Use Hint or Repeat when needed.\n"
        "4. Collect stars and badges!"
    )
    wrapped_lines: list[str] = []
    for raw in instructions.splitlines():
        wrapped_lines.extend(_wrap(raw, panel_inner.width - 70, size=31))
    _blit_lines(surface, wrapped_lines, (panel_inner.x + 40, panel_inner.y + 34), size=31, line_gap=12, color=PROMPT_BROWN)
    draw_cta_button(surface, pct_rect(0.28, 0.76, 0.44, 0.16), "Let's Go!")


def render_world_map(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    chip = pct_rect(0.34, 0.016, 0.32, 0.085)
    radius = chip.height // 2
    draw_rounded_rect(
        surface,
        chip,
        (255, 255, 255),
        radius=radius,
        border=(255, 198, 96),
        border_width=4,
    )
    points_label = f"{view.points_emoji} {int(view.total_points)} Points"
    blit_outlined_text(
        surface,
        points_label,
        chip.center,
        34,
        (227, 120, 48),
        outline=(255, 255, 255),
        outline_width=3,
    )
    # Bottom progress banner removed — world unlock hints are shown via transient toasts.


def render_writing_castle_game(surface: pygame.Surface, view: SceneView) -> None:
    from ui.app_background import paint_app_background
    from ui.loading import draw_loading_panel
    from ui.writing_layout import WRITING_BOARD_RECT, WRITING_PROMPT_Y

    if not paint_app_background(surface, "writing_castle_game"):
        paint_pink_sky(surface)

    prompt = str(view.writing_prompt or view.current_task_prompt or "Write on the board.")
    _dramatic_text(
        surface,
        prompt,
        56,
        (SCREEN_WIDTH // 2, WRITING_PROMPT_Y),
        (255, 255, 255),
        outline=(92, 48, 120),
    )

    label_outline = (70, 35, 95)
    outer = WRITING_BOARD_RECT.inflate(14, 14)
    from ui.components.primitives import draw_rect_shadow

    draw_rect_shadow(surface, outer, radius=24, offset=(0, 6), alpha=42)
    draw_stitched_panel(surface, outer, border_color=(255, 198, 96))
    inner = WRITING_BOARD_RECT.inflate(-10, -10)
    draw_rounded_rect(surface, inner, (255, 255, 255), radius=22, border=BOARD_BORDER, border_width=3)

    if view.writing_canvas is not None:
        canvas = view.writing_canvas
        target = canvas.get_rect()
        target.size = (
            max(1, inner.width - 8),
            max(1, inner.height - 8),
        )
        if canvas.get_size() != target.size:
            canvas = pygame.transform.smoothscale(canvas, target.size)
        surface.blit(canvas, canvas.get_rect(center=inner.center))

    if view.writing_loading:
        draw_loading_panel(
            surface,
            inner,
            "Reading your writing...",
            started_at_ms=int(getattr(view, "app_loading_started_at", 0) or 0),
        )

    if view.writing_result_text and not view.writing_loading:
        strip = pygame.Rect(inner.x + 12, inner.bottom - 52, inner.width - 24, 40)
        draw_rounded_rect(surface, strip, (255, 248, 235), radius=14, border=(255, 198, 96), border_width=2)
        result_label = font(24, bold=True).render(f"Read: {view.writing_result_text}", True, (227, 120, 48))
        surface.blit(result_label, result_label.get_rect(center=strip.center))

    if view.writing_hint_text and not view.writing_loading:
        hint_lines = _wrap(str(view.writing_hint_text), WRITING_BOARD_RECT.width - 48, size=18)[:2]
        y = WRITING_BOARD_RECT.bottom + 8
        for line in hint_lines:
            hint = font(18).render(line, True, (255, 255, 255))
            rx = WRITING_BOARD_RECT.centerx
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                shadow = font(18).render(line, True, label_outline)
                surface.blit(shadow, shadow.get_rect(midtop=(rx + dx, y + dy)))
            surface.blit(hint, hint.get_rect(midtop=(rx, y)))
            y += 22


def render_letter_island_game(surface: pygame.Surface, view: SceneView) -> None:
    render_letter_island_gameplay(surface, _letter_island_view(view))


def render_bd_practice(surface: pygame.Surface, view: SceneView) -> None:
    render_letter_island_gameplay(surface, _letter_island_view(view))
    panel = pct_rect(0.21, 0.21, 0.58, 0.24)
    draw_rounded_rect(surface, panel, (255, 255, 255), radius=18, border=BOARD_STITCH, border_width=3)
    _text(surface, "B has a belly. D has a drum.", 36, (panel.centerx, panel.y + 54), PROMPT_BROWN)
    answer_b = pct_rect(0.26, 0.78, 0.24, 0.13)
    answer_d = pct_rect(0.53, 0.78, 0.24, 0.13)
    draw_cta_button(surface, answer_b, "B")
    draw_menu_button(surface, answer_d, "D", accent=(160, 202, 133))


def render_word_garden_game(surface: pygame.Surface, view: SceneView) -> None:
    _paint_word_garden_background(surface)
    draw_lumi_hud(
        surface,
        child_name=view.child_name or "Lumi",
        energy=view.lumi_energy,
        energy_max=view.lumi_energy_max,
        stars_filled=view.stars_filled,
        progress_text=view.progress_text or "Word garden",
    )
    outer = pct_rect(0.18, 0.18, 0.66, 0.50)
    inner = draw_stitched_panel(surface, outer, border_color=BOARD_BORDER)
    prompt_text = f"Touch the {str(view.target_word or 'sun').capitalize()}"
    _text(surface, prompt_text, 48, (inner.centerx, inner.y + 56), PROMPT_BROWN)
    slot_words = _safe_word_slots(view.slot_words)
    card_rects = (
        pct_rect(0.24, 0.39, 0.14, 0.27),
        pct_rect(0.40, 0.39, 0.14, 0.27),
        pct_rect(0.56, 0.39, 0.14, 0.27),
        pct_rect(0.72, 0.39, 0.14, 0.27),
    )
    for idx, rect in enumerate(card_rects):
        style = CARD_STYLES[idx % len(CARD_STYLES)]
        _draw_word_card(surface, rect, slot_words[idx], style)


def render_voice_challenge(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.08)
    prompt_outer = pct_rect(0.27, 0.22, 0.46, 0.32)
    prompt_inner = draw_stitched_panel(surface, prompt_outer, border_color=(210, 170, 239))
    target_word = str(view.voice_target or view.target_word or "apple").lower()
    _text(surface, "Say:", 44, (prompt_inner.centerx, prompt_inner.y + 58), PROMPT_BROWN)
    _text(surface, target_word, 84, (prompt_inner.centerx, prompt_inner.centery + 26), PROMPT_ACCENT)


def render_listening_state(surface: pygame.Surface, view: SceneView) -> None:
    render_voice_challenge(surface, view)
    ring_center = (int(SCREEN_WIDTH * 0.50), int(SCREEN_HEIGHT * 0.78))
    for radius, alpha in ((86, 40), (102, 26), (118, 18)):
        pulse = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(pulse, (85, 189, 235, alpha), (radius + 1, radius + 1), radius, 6)
        surface.blit(pulse, (ring_center[0] - radius - 1, ring_center[1] - radius - 1))
    _text(surface, "Listening...", 38, (int(SCREEN_WIDTH * 0.50), int(SCREEN_HEIGHT * 0.63)), (58, 144, 204))
    draw_cta_button(surface, pct_rect(0.35, 0.77, 0.27, 0.15), "Stop")


def render_badge_unlock(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.08)
    panel_outer = pct_rect(0.25, 0.20, 0.50, 0.50)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(255, 198, 96))
    _text(surface, "Badge Unlocked!", 56, (panel_inner.centerx, panel_inner.y + 54), (227, 144, 56))
    badges = list(view.badge_names[:3]) if view.badge_names else ["Rising Reader"]
    for i, badge in enumerate(badges):
        badge_rect = pygame.Rect(panel_inner.x + 66 + i * 150, panel_inner.y + 110, 110, 110)
        draw_rounded_rect(surface, badge_rect, (255, 224, 150), radius=18, border=(255, 255, 255), border_width=3)
        _text(surface, "★", 54, badge_rect.center, (255, 255, 255))
        _text(surface, badge, 18, (badge_rect.centerx, badge_rect.bottom + 22), HUD_PINK_DARK)
    draw_cta_button(surface, pct_rect(0.28, 0.76, 0.22, 0.13), "Continue")
    draw_menu_button(surface, pct_rect(0.55, 0.76, 0.24, 0.13), "View Badges", accent=(170, 197, 243))


def render_progress_complete(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    panel_outer = pct_rect(0.20, 0.18, 0.60, 0.50)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(255, 198, 96))
    _dramatic_text(
        surface,
        "Level Complete!",
        74,
        (panel_inner.centerx, panel_inner.y + 66),
        (255, 196, 72),
        outline=(210, 110, 35),
    )
    stars_earned = max(0, min(3, int(view.stars_filled)))
    label = font(30, bold=True).render("Stars earned:", True, PROMPT_BROWN)
    surface.blit(label, label.get_rect(center=(panel_inner.centerx, panel_inner.y + 138)))
    _draw_progress_complete_stars(surface, (panel_inner.centerx, panel_inner.y + 198), stars_earned)
    progress = view.progress_text or "Great work today!"
    _dramatic_text(
        surface,
        progress,
        40,
        (panel_inner.centerx, panel_inner.y + 278),
        HUD_PINK_DARK,
        outline=(160, 90, 120),
    )
    fallbacks = (
        ("Next World", (255, 195, 111)),
        ("Practice Again", (172, 196, 245)),
        ("View Report", (198, 172, 241)),
    )
    for (filename, rect), (label_text, accent) in zip(_PROGRESS_BTN_RECTS, fallbacks, strict=True):
        if not _blit_progress_button(surface, rect, filename):
            draw_menu_button(surface, rect, label_text, accent=accent)


def render_practice_weak_skills(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.08)
    _text(surface, "Choose a practice card", 34, (SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.24)), PROMPT_BROWN)
    cards = list(view.practice_cards[:3]) if view.practice_cards else ["Practice B", "Practice D", "Practice Word Cat"]
    while len(cards) < 3:
        cards.append(f"Practice {len(cards) + 1}")
    card_specs = (
        (pct_rect(0.195, 0.455, 0.22, 0.20), cards[0], (255, 196, 111)),
        (pct_rect(0.425, 0.455, 0.22, 0.20), cards[1], (172, 196, 245)),
        (pct_rect(0.655, 0.455, 0.22, 0.20), cards[2], (198, 172, 241)),
    )
    for rect, label, accent in card_specs:
        draw_menu_button(surface, rect, label, accent=accent)


def render_teacher_report(surface: pygame.Surface, view: SceneView) -> None:
    _paint_room_background(surface)
    title = pct_rect(0.26, 0.06, 0.48, 0.11)
    draw_rect_shadow(surface, title, radius=20, offset=(0, 5), alpha=28)
    draw_rounded_rect(surface, title, (255, 255, 255), radius=20, border=HUD_PINK, border_width=3)
    _draw_section_title(surface, "Your Report", title.center, size=42)

    panel = pct_rect(0.22, 0.20, 0.56, 0.62)
    panel_inner = draw_stitched_panel(surface, panel, border_color=(174, 199, 247))
    _draw_section_title(
        surface,
        "Your Progress",
        (panel_inner.centerx, panel_inner.y + 34),
        size=30,
        color=PROMPT_BROWN,
    )

    report = view.teacher_report or {}
    stats = (
        ("Stars earned", _report_value(report, "stars_earned", "0"), STAR_YELLOW),
        ("Accuracy", f"{_report_value(report, 'accuracy_percent', '0')}%", BUTTON_BLUE),
        ("Strong skill", _report_value(report, "strong_skill", "Practice in progress"), (125, 202, 134)),
        ("Needs practice", _report_value(report, "needs_practice", "None"), BUTTON_PURPLE),
    )
    row_gap = 16
    row_height = 64
    total_rows_height = len(stats) * row_height + (len(stats) - 1) * row_gap
    row_y = panel_inner.centery - total_rows_height // 2 + 18
    for label, value, accent in stats:
        _draw_report_stat_row(surface, panel_inner, row_y, label, value, accent=accent)
        row_y += row_height + row_gap


def render_settings(surface: pygame.Surface, view: SceneView) -> None:
    _paint_room_background(surface)
    panel_outer = pct_rect(0.18, 0.10, 0.64, 0.80)
    draw_rect_shadow(surface, panel_outer, radius=24, offset=(0, 6), alpha=26)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(215, 183, 233))
    _draw_section_title(surface, "Settings", (panel_inner.centerx, panel_inner.y + 40), size=48)
    hint_font = font(20, bold=False)
    hint = hint_font.render("Tap a row to change it", True, PROMPT_BROWN)
    surface.blit(hint, hint.get_rect(center=(panel_inner.centerx, panel_inner.y + 82)))

    row_height = 72
    row_gap = 14
    row_width = panel_inner.width - 48
    row_x = panel_inner.x + 24
    first_row_y = panel_inner.y + 108
    control_w = int(row_width * 0.28)
    control_h = 46

    rows = (
        ("Music", "Play cheerful background music", (255, 166, 186), "toggle", bool(view.music_enabled)),
        ("Voice", "Let Lumi speak hints and praise", (172, 196, 245), "toggle", bool(view.voice_enabled)),
        ("Microphone", "Check that speech input works", (255, 195, 111), "button", "Test Mic"),
        ("Difficulty", "Adjust challenge for your learner", (198, 172, 241), "button", str(view.difficulty_mode or "Medium")),
        ("Reset Progress", "Start fresh but keep settings", (255, 146, 170), "button", "Reset"),
    )

    for index, (title, subtitle, accent, kind, control_state) in enumerate(rows):
        row_y = first_row_y + index * (row_height + row_gap)
        row_rect = pygame.Rect(row_x, row_y, row_width, row_height)
        control_rect = pygame.Rect(row_rect.right - control_w - 12, row_rect.centery - control_h // 2, control_w, control_h)
        if kind == "toggle":
            _draw_settings_row(
                surface,
                panel_inner,
                row_rect,
                title,
                subtitle,
                control_rect,
                accent=accent,
                toggle_on=bool(control_state),
            )
        else:
            _draw_settings_row(
                surface,
                panel_inner,
                row_rect,
                title,
                subtitle,
                control_rect,
                accent=accent,
                control_value=str(control_state),
            )

    if view.settings_status:
        status = pygame.Rect(panel_inner.x + 24, panel_inner.bottom - 56, panel_inner.width - 48, 42)
        draw_rect_shadow(surface, status, radius=12, offset=(0, 3), alpha=24)
        draw_rounded_rect(surface, status, (255, 255, 255), radius=12, border=HUD_PINK, border_width=2)
        _text(surface, view.settings_status, 20, status.center, HUD_PINK_DARK)


def render_microphone_check(surface: pygame.Surface, view: SceneView) -> None:
    _paint_room_background(surface)
    draw_corner_nav(surface, show_home=False, show_settings=True)
    panel_outer = pct_rect(0.22, 0.18, 0.56, 0.54)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(172, 196, 245))
    _text(surface, "Microphone Check", 52, (panel_inner.centerx, panel_inner.y + 62), PROMPT_BROWN)
    status = view.microphone_status or "Let's make sure your microphone is ready."
    wrapped = _wrap(status, panel_inner.width - 60, size=29)
    for idx, line in enumerate(wrapped[:3]):
        _text(surface, line, 29, (panel_inner.centerx, panel_inner.y + 142 + idx * 34), HUD_PINK_DARK)
    draw_cta_button(surface, pct_rect(0.30, 0.75, 0.30, 0.15), "Test Mic")
    draw_menu_button(surface, pct_rect(0.64, 0.78, 0.13, 0.10), "Skip", accent=(255, 166, 186))


def render_end_session(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.09)
    draw_lumi_mascot_large(surface, x_pct=0.50, y_pct=0.40, scale=1.25)
    panel = pct_rect(0.24, 0.56, 0.52, 0.16)
    draw_rounded_rect(surface, panel, (255, 255, 255), radius=18, border=HUD_PINK, border_width=3)
    message = view.feedback_message or "Amazing work today! See you next time."
    _text(surface, message, 31, panel.center, PROMPT_BROWN)
    draw_menu_button(surface, pct_rect(0.25, 0.73, 0.23, 0.13), "Play Again", accent=(255, 195, 111))
    draw_menu_button(surface, pct_rect(0.53, 0.73, 0.25, 0.13), "View Report", accent=(172, 196, 245))


def render_offline_continue(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dim.fill((90, 58, 102, 110))
    surface.blit(dim, (0, 0))
    modal = pct_rect(0.20, 0.22, 0.60, 0.44)
    draw_rounded_rect(surface, modal, (255, 255, 255), radius=24, border=HUD_PINK, border_width=4)
    _text(surface, "Offline Mode", 56, (modal.centerx, modal.y + 62), HUD_PINK_DARK)
    message = view.offline_message or "No internet or microphone right now. You can keep learning offline."
    for idx, line in enumerate(_wrap(message, modal.width - 80, size=30)):
        _text(surface, line, 30, (modal.centerx, modal.y + 150 + idx * 36), PROMPT_BROWN)
    draw_cta_button(surface, pct_rect(0.36, 0.65, 0.29, 0.13), "Continue Offline")


def _draw_points_stat_card(
    surface: pygame.Surface,
    rect: pygame.Rect,
    label: str,
    value: str,
    accent: tuple[int, int, int],
) -> None:
    draw_rounded_rect(surface, rect, (255, 255, 255), radius=20, border=accent, border_width=4)
    chip = pygame.Rect(rect.x, rect.y, rect.width, int(rect.height * 0.34))
    draw_rounded_rect(surface, chip, accent, radius=20)
    _text(surface, label, 24, (chip.centerx, chip.centery), (255, 255, 255))
    _text(surface, value, 46, (rect.centerx, rect.y + int(rect.height * 0.66)), PROMPT_BROWN)


def render_points_page(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_corner_nav(surface, show_home=True, show_settings=False)

    header = pct_rect(0.30, 0.04, 0.40, 0.10)
    draw_rounded_rect(surface, header, (255, 255, 255), radius=20, border=HUD_PINK, border_width=3)
    _text(surface, "My Points", 44, header.center, HUD_PINK_DARK)

    # Big points medallion.
    medal = pct_rect(0.08, 0.20, 0.40, 0.34)
    draw_rounded_rect(surface, medal, (255, 255, 255), radius=26, border=(255, 198, 96), border_width=5)
    _text(surface, f"{view.points_emoji}  {view.points_rank}", 30, (medal.centerx, medal.y + 44), (227, 144, 56))
    _text(surface, str(int(view.total_points)), 96, (medal.centerx, medal.centery + 24), STAR_YELLOW)
    _text(surface, "points", 26, (medal.centerx, medal.bottom - 34), PROMPT_BROWN)

    # Progress bar toward next rank.
    bar_label_y = int(SCREEN_HEIGHT * 0.60)
    if view.next_rank_name:
        msg = f"{view.points_to_next} points to {view.next_rank_name}"
    else:
        msg = "Top rank reached! You're amazing!"
    _text(surface, msg, 26, (int(SCREEN_WIDTH * 0.28), bar_label_y), PROMPT_BROWN)
    bar_outer = pct_rect(0.08, 0.64, 0.40, 0.05)
    draw_rounded_rect(surface, bar_outer, (255, 255, 255), radius=14, border=HUD_PINK, border_width=3)
    fill = bar_outer.inflate(-8, -8)
    fill.width = max(6, int(fill.width * max(0.0, min(1.0, view.points_progress))))
    draw_rounded_rect(surface, fill, (125, 202, 134), radius=10)

    # Stat cards.
    _draw_points_stat_card(surface, pct_rect(0.54, 0.20, 0.18, 0.22), "Stars", str(int(view.total_stars)), (255, 196, 91))
    _draw_points_stat_card(surface, pct_rect(0.76, 0.20, 0.18, 0.22), "Badges", str(int(view.badges_count)), (198, 172, 241))
    _draw_points_stat_card(surface, pct_rect(0.54, 0.46, 0.18, 0.22), "Best Streak", str(int(view.best_streak)), (172, 196, 245))
    _draw_points_stat_card(surface, pct_rect(0.76, 0.46, 0.18, 0.22), "Now", str(int(view.current_streak)), (255, 166, 186))

    draw_cta_button(surface, pct_rect(0.36, 0.84, 0.28, 0.12), "Play")


SCENE_RENDERERS: dict[str, SceneRenderer] = {
    "points_page": render_points_page,
    "splash_loading": render_splash_loading,
    "welcome": render_welcome,
    "profile_selection": render_profile_selection,
    "main_menu": render_main_menu,
    "how_to_play": render_how_to_play,
    "world_map": render_world_map,
    "writing_castle_game": render_writing_castle_game,
    "letter_island_game": render_letter_island_game,
    "bd_practice": render_bd_practice,
    "word_garden_game": render_word_garden_game,
    "voice_challenge": render_voice_challenge,
    "listening_state": render_listening_state,
    "badge_unlock": render_badge_unlock,
    "progress_complete": render_progress_complete,
    "practice_weak_skills": render_practice_weak_skills,
    "teacher_report": render_teacher_report,
    "settings": render_settings,
    "microphone_check": render_microphone_check,
    "end_session": render_end_session,
    "offline_continue": render_offline_continue,
}
