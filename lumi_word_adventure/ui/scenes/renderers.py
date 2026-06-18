"""Component renderers for every Lumi Word Adventure screen."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.letter_island_scene import (
    LetterIslandView,
    render_letter_island_correct,
    render_letter_island_gameplay,
    render_letter_island_mistake,
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
    draw_circle_button,
    draw_dashed_rounded_rect,
    draw_icon_bulb,
    draw_icon_home,
    draw_icon_mic,
    draw_icon_refresh,
    draw_icon_speaker,
    draw_rounded_rect,
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
    fallback = ("cat", "dog", "sun", "ball")
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


def _paint_castle_background(surface: pygame.Surface) -> None:
    paint_pink_sky(surface)
    sky_tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    sky_tint.fill((165, 120, 205, 65))
    surface.blit(sky_tint, (0, 0))
    ground = pct_rect(0.0, 0.56, 1.0, 0.44)
    pygame.draw.rect(surface, (207, 177, 237), ground)
    tower_left = pct_rect(0.08, 0.23, 0.14, 0.40)
    tower_right = pct_rect(0.78, 0.24, 0.14, 0.38)
    for tower in (tower_left, tower_right):
        draw_rounded_rect(surface, tower, (223, 204, 244), radius=12, border=(190, 155, 222), border_width=3)
        top = pygame.Rect(tower.x + 4, tower.y - 24, tower.width - 8, 34)
        draw_rounded_rect(surface, top, (190, 150, 230), radius=10, border=(175, 134, 214), border_width=2)
    gate = pct_rect(0.39, 0.30, 0.22, 0.33)
    draw_rounded_rect(surface, gate, (213, 188, 238), radius=18, border=(180, 142, 220), border_width=3)
    door = pygame.Rect(gate.centerx - 54, gate.bottom - 122, 108, 122)
    draw_rounded_rect(surface, door, (166, 125, 212), radius=22, border=(148, 106, 198), border_width=3)
    for x_pct in (0.12, 0.86):
        flag = [(int(SCREEN_WIDTH * x_pct), int(SCREEN_HEIGHT * 0.16)), (int(SCREEN_WIDTH * x_pct), int(SCREEN_HEIGHT * 0.28))]
        pygame.draw.line(surface, PROMPT_BROWN, flag[0], flag[1], 4)
        pennant = [
            (flag[0][0], flag[0][1] + 8),
            (flag[0][0] + 54, flag[0][1] + 24),
            (flag[0][0], flag[0][1] + 42),
        ]
        pygame.draw.polygon(surface, (255, 190, 86), pennant)


def _paint_room_background(surface: pygame.Surface) -> None:
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


def _draw_sentence_slot(surface: pygame.Surface, rect: pygame.Rect, text_value: str) -> None:
    fill = (255, 255, 255) if not text_value else (255, 240, 206)
    draw_rounded_rect(surface, rect, fill, radius=14, border=BOARD_STITCH, border_width=3)
    if text_value:
        blit_fitted_text(surface, rect, text_value, PROMPT_BROWN, padding=10)


def _draw_toggle(surface: pygame.Surface, rect: pygame.Rect, enabled: bool) -> None:
    back = (125, 202, 134) if enabled else (208, 190, 205)
    knob_x = rect.right - rect.height // 2 if enabled else rect.x + rect.height // 2
    draw_rounded_rect(surface, rect, back, radius=rect.height // 2)
    pygame.draw.circle(surface, (255, 255, 255), (knob_x, rect.centery), rect.height // 2 - 3)


def _report_value(report: dict[str, Any], key: str, fallback: str) -> str:
    value = report.get(key, fallback)
    return str(value if value not in (None, "") else fallback)


def render_splash_loading(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.20)
    draw_lumi_mascot_large(surface, x_pct=0.5, y_pct=0.48, scale=1.2)
    bubble_text = view.feedback_message or "Warming up your learning adventure..."
    draw_speech_bubble(surface, bubble_text, x_pct=0.36, y_pct=0.62, w_pct=0.30)
    paint_loading_bar(surface, float(view.loading_progress or 0.0))


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


def render_main_menu(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.08)
    draw_lumi_mascot_large(surface, x_pct=0.26, y_pct=0.58, scale=1.3)
    draw_menu_button(surface, pct_rect(0.57, 0.19, 0.33, 0.17), "Play", accent=(255, 196, 91))
    draw_menu_button(surface, pct_rect(0.57, 0.40, 0.33, 0.16), "Practice", accent=(168, 201, 244))
    draw_menu_button(surface, pct_rect(0.57, 0.59, 0.33, 0.15), "Report", accent=(196, 174, 241))
    draw_menu_button(surface, pct_rect(0.57, 0.76, 0.33, 0.15), "Settings", accent=(255, 166, 186))
    draw_circle_button(surface, (int(SCREEN_WIDTH * 0.05), int(SCREEN_HEIGHT * 0.09)), 30, BUTTON_PINK)
    draw_icon_refresh(surface, (int(SCREEN_WIDTH * 0.05), int(SCREEN_HEIGHT * 0.09)))
    draw_circle_button(surface, (int(SCREEN_WIDTH * 0.92), int(SCREEN_HEIGHT * 0.08)), 30, BUTTON_PINK)
    draw_icon_home(surface, (int(SCREEN_WIDTH * 0.92), int(SCREEN_HEIGHT * 0.08)))
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
    draw_cta_button(surface, pct_rect(0.34, 0.82, 0.31, 0.13), "Let's Go")
    draw_circle_button(surface, (int(SCREEN_WIDTH * 0.74), int(SCREEN_HEIGHT * 0.885)), 28, BUTTON_PURPLE)
    draw_icon_refresh(surface, (int(SCREEN_WIDTH * 0.74), int(SCREEN_HEIGHT * 0.885)))


def render_world_map(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_corner_nav(surface, show_home=True, show_settings=False)
    _draw_soft_hills(surface, ((145, 194, 233), (167, 212, 245), (197, 232, 255)))
    path = [
        (int(SCREEN_WIDTH * 0.16), int(SCREEN_HEIGHT * 0.60)),
        (int(SCREEN_WIDTH * 0.34), int(SCREEN_HEIGHT * 0.52)),
        (int(SCREEN_WIDTH * 0.52), int(SCREEN_HEIGHT * 0.57)),
        (int(SCREEN_WIDTH * 0.70), int(SCREEN_HEIGHT * 0.50)),
        (int(SCREEN_WIDTH * 0.84), int(SCREEN_HEIGHT * 0.57)),
    ]
    pygame.draw.lines(surface, (255, 255, 255), False, path, 10)
    pygame.draw.lines(surface, (247, 194, 141), False, path, 4)
    _draw_world_node(surface, 0.24, 0.52, "Letter Island", (255, 202, 136))
    _draw_world_node(surface, 0.50, 0.52, "Word Garden", (178, 230, 164))
    _draw_world_node(surface, 0.76, 0.52, "Sentence Castle", (202, 179, 246))
    words_chip = pct_rect(0.87, 0.12, 0.08, 0.13)
    draw_rounded_rect(surface, words_chip, (255, 255, 255), radius=16, border=HUD_PINK, border_width=3)
    _text(surface, "My\nWords", 18, words_chip.center, HUD_PINK_DARK)
    if view.progress_text:
        chip = pct_rect(0.30, 0.86, 0.40, 0.07)
        draw_rounded_rect(surface, chip, (255, 255, 255), radius=16, border=HUD_PINK, border_width=2)
        _text(surface, view.progress_text, 24, chip.center, TEXT_DARK)


def render_letter_island_game(surface: pygame.Surface, view: SceneView) -> None:
    render_letter_island_gameplay(surface, _letter_island_view(view))


def render_letter_correct_feedback(surface: pygame.Surface, view: SceneView) -> None:
    render_letter_island_correct(surface, _letter_island_view(view))
    draw_cta_button(surface, pct_rect(0.36, 0.79, 0.29, 0.15), "Next")


def render_letter_mistake_hint(surface: pygame.Surface, view: SceneView) -> None:
    render_letter_island_mistake(surface, _letter_island_view(view))


def render_bd_practice(surface: pygame.Surface, view: SceneView) -> None:
    render_letter_island_gameplay(surface, _letter_island_view(view))
    panel = pct_rect(0.21, 0.21, 0.58, 0.24)
    draw_rounded_rect(surface, panel, (255, 255, 255), radius=18, border=BOARD_STITCH, border_width=3)
    _text(surface, "B has a belly. D has a drum.", 36, (panel.centerx, panel.y + 54), PROMPT_BROWN)
    answer_b = pct_rect(0.26, 0.78, 0.24, 0.13)
    answer_d = pct_rect(0.53, 0.78, 0.24, 0.13)
    draw_cta_button(surface, answer_b, "B")
    draw_menu_button(surface, answer_d, "D", accent=(160, 202, 133))
    draw_circle_button(surface, (int(SCREEN_WIDTH * 0.855), int(SCREEN_HEIGHT * 0.11)), 28, BUTTON_PURPLE)
    draw_icon_refresh(surface, (int(SCREEN_WIDTH * 0.855), int(SCREEN_HEIGHT * 0.11)))
    draw_circle_button(surface, (int(SCREEN_WIDTH * 0.945), int(SCREEN_HEIGHT * 0.11)), 28, BUTTON_YELLOW)
    draw_icon_bulb(surface, (int(SCREEN_WIDTH * 0.945), int(SCREEN_HEIGHT * 0.11)))


def render_word_garden_game(surface: pygame.Surface, view: SceneView) -> None:
    _paint_word_garden_background(surface)
    draw_corner_nav(surface, show_home=True, show_settings=False)
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
    prompt_text = f"Touch {str(view.target_word or 'cat').lower()}"
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
    _draw_footer_action_triplet(surface)


def render_word_correct_feedback(surface: pygame.Surface, view: SceneView) -> None:
    _paint_word_garden_background(surface)
    draw_corner_nav(surface, show_home=False, show_settings=True)
    panel_outer = pct_rect(0.27, 0.24, 0.46, 0.38)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(157, 212, 136))
    _text(surface, "Great!", 72, (panel_inner.centerx, panel_inner.y + 66), (109, 178, 93))
    msg = view.feedback_message or f"You found {str(view.target_word or 'cat').lower()}!"
    for i, line in enumerate(_wrap(msg, panel_inner.width - 50, size=30)):
        _text(surface, line, 30, (panel_inner.centerx, panel_inner.y + 138 + i * 36), PROMPT_BROWN)
    draw_cta_button(surface, pct_rect(0.37, 0.82, 0.27, 0.13), "Next")


def render_word_mistake_hint(surface: pygame.Surface, view: SceneView) -> None:
    _paint_word_garden_background(surface)
    panel_outer = pct_rect(0.22, 0.18, 0.56, 0.50)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(243, 160, 171))
    message = view.feedback_message or "Good try. Listen and try again."
    for i, line in enumerate(_wrap(message, panel_inner.width - 52, size=31)):
        _text(surface, line, 31, (panel_inner.centerx, panel_inner.y + 70 + i * 38), PROMPT_BROWN)
    sound_chip = pct_rect(0.28, 0.42, 0.07, 0.11)
    draw_circle_button(surface, sound_chip.center, min(sound_chip.width, sound_chip.height) // 2, BUTTON_BLUE)
    draw_icon_refresh(surface, sound_chip.center)
    draw_menu_button(surface, pct_rect(0.25, 0.78, 0.20, 0.14), "Try Again", accent=(251, 186, 121))
    draw_menu_button(surface, pct_rect(0.48, 0.78, 0.20, 0.14), "Repeat", accent=(172, 196, 245))
    draw_menu_button(surface, pct_rect(0.70, 0.78, 0.16, 0.14), "Hint", accent=(198, 172, 241))


def render_voice_challenge(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.08)
    prompt_outer = pct_rect(0.27, 0.22, 0.46, 0.32)
    prompt_inner = draw_stitched_panel(surface, prompt_outer, border_color=(210, 170, 239))
    target_word = str(view.voice_target or view.target_word or "apple").lower()
    _text(surface, "Say:", 44, (prompt_inner.centerx, prompt_inner.y + 58), PROMPT_BROWN)
    _text(surface, target_word, 84, (prompt_inner.centerx, prompt_inner.centery + 26), PROMPT_ACCENT)
    draw_circle_button(surface, (prompt_inner.centerx, int(SCREEN_HEIGHT * 0.78)), 62, BUTTON_BLUE)
    draw_icon_mic(surface, (prompt_inner.centerx, int(SCREEN_HEIGHT * 0.78)))
    draw_circle_button(surface, (int(SCREEN_WIDTH * 0.335), int(SCREEN_HEIGHT * 0.875)), 34, BUTTON_PURPLE)
    draw_icon_refresh(surface, (int(SCREEN_WIDTH * 0.335), int(SCREEN_HEIGHT * 0.875)))
    draw_circle_button(surface, (int(SCREEN_WIDTH * 0.655), int(SCREEN_HEIGHT * 0.875)), 34, BUTTON_YELLOW)
    draw_icon_bulb(surface, (int(SCREEN_WIDTH * 0.655), int(SCREEN_HEIGHT * 0.875)))
    _text(surface, "Skip", 24, (int(SCREEN_WIDTH * 0.74), int(SCREEN_HEIGHT * 0.88)), TEXT_DARK)


def render_listening_state(surface: pygame.Surface, view: SceneView) -> None:
    render_voice_challenge(surface, view)
    ring_center = (int(SCREEN_WIDTH * 0.50), int(SCREEN_HEIGHT * 0.78))
    for radius, alpha in ((86, 40), (102, 26), (118, 18)):
        pulse = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(pulse, (85, 189, 235, alpha), (radius + 1, radius + 1), radius, 6)
        surface.blit(pulse, (ring_center[0] - radius - 1, ring_center[1] - radius - 1))
    _text(surface, "Listening...", 38, (int(SCREEN_WIDTH * 0.50), int(SCREEN_HEIGHT * 0.63)), (58, 144, 204))
    draw_cta_button(surface, pct_rect(0.35, 0.77, 0.27, 0.15), "Stop")


def render_voice_correct_feedback(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.09)
    panel_outer = pct_rect(0.24, 0.22, 0.52, 0.34)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(163, 218, 145))
    _text(surface, "Awesome!", 70, (panel_inner.centerx, panel_inner.y + 64), (92, 177, 94))
    spoken = view.feedback_message or f"You said {str(view.voice_target or 'apple').lower()}!"
    _text(surface, spoken, 32, (panel_inner.centerx, panel_inner.centery + 40), PROMPT_BROWN)
    draw_cta_button(surface, pct_rect(0.29, 0.80, 0.29, 0.14), "Next")
    draw_menu_button(surface, pct_rect(0.63, 0.80, 0.20, 0.12), "Say Again", accent=(166, 201, 244))


def _render_sentence_base(surface: pygame.Surface, view: SceneView) -> None:
    _paint_castle_background(surface)
    draw_corner_nav(surface, show_home=True, show_settings=False)
    draw_lumi_hud(
        surface,
        child_name=view.child_name or "Lumi",
        energy=view.lumi_energy,
        energy_max=view.lumi_energy_max,
        stars_filled=view.stars_filled,
        progress_text=view.progress_text or "Sentence castle",
    )
    panel_outer = pct_rect(0.17, 0.18, 0.66, 0.46)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(198, 163, 236))
    prompt = view.sentence_prompt or "Build the sentence."
    _text(surface, prompt, 42, (panel_inner.centerx, panel_inner.y + 54), PROMPT_BROWN)
    slot_rects = (
        pct_rect(0.22, 0.55, 0.13, 0.13),
        pct_rect(0.35, 0.55, 0.13, 0.13),
        pct_rect(0.51, 0.55, 0.13, 0.13),
        pct_rect(0.64, 0.55, 0.13, 0.13),
    )
    words = list(view.sentence_slots[:4])
    while len(words) < 4:
        words.append("")
    for idx, rect in enumerate(slot_rects):
        _draw_sentence_slot(surface, rect, words[idx])
    card_rects = (
        pct_rect(0.21, 0.75, 0.14, 0.15),
        pct_rect(0.38, 0.75, 0.16, 0.15),
        pct_rect(0.56, 0.75, 0.14, 0.15),
        pct_rect(0.71, 0.75, 0.16, 0.15),
    )
    words_bank = list(view.sentence_words[:4])
    if not words_bank:
        words_bank = ["I", "see", "a", "cat"]
    while len(words_bank) < 4:
        words_bank.append("")
    for idx, rect in enumerate(card_rects):
        draw_rounded_rect(surface, rect, (255, 255, 255), radius=14, border=(190, 155, 222), border_width=3)
        _text(surface, words_bank[idx], 30, rect.center, PROMPT_BROWN)
    draw_circle_button(surface, (int(SCREEN_WIDTH * 0.865), int(SCREEN_HEIGHT * 0.845)), 28, BUTTON_YELLOW)
    draw_icon_bulb(surface, (int(SCREEN_WIDTH * 0.865), int(SCREEN_HEIGHT * 0.845)))
    draw_circle_button(surface, (int(SCREEN_WIDTH * 0.945), int(SCREEN_HEIGHT * 0.845)), 28, BUTTON_PURPLE)
    draw_icon_refresh(surface, (int(SCREEN_WIDTH * 0.945), int(SCREEN_HEIGHT * 0.845)))


def render_sentence_castle_game(surface: pygame.Surface, view: SceneView) -> None:
    _render_sentence_base(surface, view)


def render_sentence_dragging(surface: pygame.Surface, view: SceneView) -> None:
    _render_sentence_base(surface, view)
    drag_chip = pct_rect(0.41, 0.34, 0.18, 0.08)
    draw_rounded_rect(surface, drag_chip, (255, 255, 255), radius=12, border=(190, 155, 222), border_width=2)
    _text(surface, "Dragging...", 24, drag_chip.center, HUD_PINK_DARK)


def render_sentence_mistake_hint(surface: pygame.Surface, view: SceneView) -> None:
    _render_sentence_base(surface, view)
    panel = pct_rect(0.25, 0.26, 0.50, 0.18)
    draw_rounded_rect(surface, panel, (255, 255, 255), radius=16, border=HUD_PINK, border_width=3)
    message = view.feedback_message or "Good try. Start with I."
    for i, line in enumerate(_wrap(message, panel.width - 40, size=28)):
        _text(surface, line, 28, (panel.centerx, panel.y + 44 + i * 32), PROMPT_BROWN)
    draw_menu_button(surface, pct_rect(0.28, 0.78, 0.18, 0.13), "Try Again", accent=(255, 194, 117))
    draw_menu_button(surface, pct_rect(0.50, 0.78, 0.18, 0.13), "Hint", accent=(172, 196, 245))
    draw_menu_button(surface, pct_rect(0.70, 0.78, 0.18, 0.13), "Repeat", accent=(198, 172, 241))


def render_sentence_correct_feedback(surface: pygame.Surface, view: SceneView) -> None:
    _paint_castle_background(surface)
    panel_outer = pct_rect(0.27, 0.23, 0.46, 0.35)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(164, 219, 147))
    _text(surface, "Sentence Complete!", 56, (panel_inner.centerx, panel_inner.y + 62), (93, 179, 95))
    message = view.feedback_message or "You built it!"
    _text(surface, message, 33, (panel_inner.centerx, panel_inner.centery + 36), PROMPT_BROWN)
    draw_cta_button(surface, pct_rect(0.38, 0.80, 0.24, 0.14), "Next")


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
    draw_cta_button(surface, pct_rect(0.50, 0.78, 0.30, 0.14), "Continue")
    draw_menu_button(surface, pct_rect(0.82, 0.08, 0.14, 0.12), "View Badges", accent=(170, 197, 243))


def render_progress_complete(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    panel_outer = pct_rect(0.20, 0.18, 0.60, 0.50)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(255, 198, 96))
    _text(surface, "Level Complete!", 62, (panel_inner.centerx, panel_inner.y + 64), (227, 144, 56))
    _text(surface, "Stars earned:", 34, (panel_inner.centerx - 70, panel_inner.y + 140), PROMPT_BROWN)
    stars = max(0, min(3, int(view.stars_filled)))
    for i in range(3):
        color = STAR_YELLOW if i < stars else (225, 205, 215)
        _text(surface, "★", 56, (panel_inner.centerx + 54 + i * 58, panel_inner.y + 142), color)
    progress = view.progress_text or "Great work today!"
    _text(surface, progress, 30, (panel_inner.centerx, panel_inner.y + 222), HUD_PINK_DARK)
    draw_menu_button(surface, pct_rect(0.36, 0.73, 0.25, 0.13), "Next World", accent=(255, 195, 111))
    draw_menu_button(surface, pct_rect(0.63, 0.73, 0.25, 0.13), "Practice Again", accent=(172, 196, 245))
    draw_menu_button(surface, pct_rect(0.90, 0.05, 0.16, 0.12), "View Report", accent=(198, 172, 241))


def render_practice_weak_skills(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_logo_banner(surface, y_pct=0.08)
    _text(surface, "Choose a practice card", 34, (SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.24)), PROMPT_BROWN)
    cards = list(view.practice_cards[:4]) if view.practice_cards else ["Practice B", "Practice D", "Practice Word Cat", "Practice Sentence"]
    while len(cards) < 4:
        cards.append(f"Practice {len(cards) + 1}")
    card_specs = (
        (pct_rect(0.195, 0.455, 0.22, 0.20), cards[0], (255, 196, 111)),
        (pct_rect(0.425, 0.455, 0.22, 0.20), cards[1], (172, 196, 245)),
        (pct_rect(0.655, 0.455, 0.22, 0.20), cards[2], (198, 172, 241)),
        (pct_rect(0.36, 0.70, 0.48, 0.18), cards[3], (159, 219, 147)),
    )
    for rect, label, accent in card_specs:
        draw_menu_button(surface, rect, label, accent=accent)


def render_teacher_report(surface: pygame.Surface, view: SceneView) -> None:
    paint_pink_sky(surface)
    draw_corner_nav(surface, show_home=True, show_settings=False)
    title = pct_rect(0.26, 0.08, 0.48, 0.10)
    draw_rounded_rect(surface, title, (255, 255, 255), radius=18, border=HUD_PINK, border_width=3)
    _text(surface, "Teacher Report", 44, title.center, HUD_PINK_DARK)
    left = pct_rect(0.11, 0.22, 0.42, 0.60)
    right = pct_rect(0.58, 0.22, 0.33, 0.62)
    left_inner = draw_stitched_panel(surface, left, border_color=(174, 199, 247))
    right_inner = draw_stitched_panel(surface, right, border_color=(198, 172, 241))
    report = view.teacher_report or {}
    lines = [
        f"Stars earned: {_report_value(report, 'stars_earned', '0')}",
        f"Accuracy: {_report_value(report, 'accuracy_percent', '0')}%",
        f"Strong skill: {_report_value(report, 'strong_skill', 'In progress')}",
        f"Needs practice: {_report_value(report, 'needs_practice', 'None')}",
        f"Recommended: {_report_value(report, 'recommended_next_activity', 'World Map')}",
    ]
    _blit_lines(surface, lines, (left_inner.x + 20, left_inner.y + 24), size=28, line_gap=12, color=PROMPT_BROWN)
    rec_label = _report_value(report, "recommended_next_activity", "Practice")
    rec_btn = pct_rect(0.60, 0.60, 0.28, 0.25)
    draw_menu_button(surface, rec_btn, rec_label, accent=(255, 195, 111))
    refresh_btn = pct_rect(0.87, 0.77, 0.11, 0.12)
    draw_menu_button(surface, refresh_btn, "Refresh", accent=(172, 196, 245))


def render_settings(surface: pygame.Surface, view: SceneView) -> None:
    _paint_room_background(surface)
    draw_corner_nav(surface, show_home=True, show_settings=False)
    panel_outer = pct_rect(0.21, 0.14, 0.58, 0.76)
    panel_inner = draw_stitched_panel(surface, panel_outer, border_color=(215, 183, 233))
    _text(surface, "Settings", 50, (panel_inner.centerx, panel_inner.y + 46), PROMPT_BROWN)
    rows = (
        ("Music", "ON" if view.music_enabled else "OFF", pct_rect(0.72, 0.20, 0.12, 0.08)),
        ("Voice", "ON" if view.voice_enabled else "OFF", pct_rect(0.72, 0.33, 0.12, 0.08)),
        ("Difficulty", str(view.difficulty_mode or "Medium"), pct_rect(0.66, 0.58, 0.16, 0.09)),
    )
    row_y = [0.20, 0.33, 0.58]
    for idx, (title_text, value, control_rect) in enumerate(rows):
        y = int(SCREEN_HEIGHT * row_y[idx])
        _text(surface, title_text, 34, (int(SCREEN_WIDTH * 0.38), y + 30), PROMPT_BROWN)
        if title_text in {"Music", "Voice"}:
            _draw_toggle(surface, control_rect, value == "ON")
            _text(surface, value, 22, (control_rect.centerx, control_rect.centery), (255, 255, 255))
        else:
            draw_menu_button(surface, control_rect, value, accent=(172, 196, 245))
    draw_menu_button(surface, pct_rect(0.63, 0.46, 0.19, 0.08), "Test Mic", accent=(255, 195, 111))
    draw_menu_button(surface, pct_rect(0.69, 0.72, 0.14, 0.08), "Reset", accent=(255, 166, 186))
    if view.settings_status:
        status = pct_rect(0.28, 0.84, 0.44, 0.07)
        draw_rounded_rect(surface, status, (255, 255, 255), radius=12, border=HUD_PINK, border_width=2)
        _text(surface, view.settings_status, 22, status.center, HUD_PINK_DARK)


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


SCENE_RENDERERS: dict[str, SceneRenderer] = {
    "splash_loading": render_splash_loading,
    "welcome": render_welcome,
    "profile_selection": render_profile_selection,
    "main_menu": render_main_menu,
    "how_to_play": render_how_to_play,
    "world_map": render_world_map,
    "letter_island_game": render_letter_island_game,
    "letter_correct_feedback": render_letter_correct_feedback,
    "letter_mistake_hint": render_letter_mistake_hint,
    "bd_practice": render_bd_practice,
    "word_garden_game": render_word_garden_game,
    "word_correct_feedback": render_word_correct_feedback,
    "word_mistake_hint": render_word_mistake_hint,
    "voice_challenge": render_voice_challenge,
    "listening_state": render_listening_state,
    "voice_correct_feedback": render_voice_correct_feedback,
    "sentence_castle_game": render_sentence_castle_game,
    "sentence_dragging": render_sentence_dragging,
    "sentence_mistake_hint": render_sentence_mistake_hint,
    "sentence_correct_feedback": render_sentence_correct_feedback,
    "badge_unlock": render_badge_unlock,
    "progress_complete": render_progress_complete,
    "practice_weak_skills": render_practice_weak_skills,
    "teacher_report": render_teacher_report,
    "settings": render_settings,
    "microphone_check": render_microphone_check,
    "end_session": render_end_session,
    "offline_continue": render_offline_continue,
}
