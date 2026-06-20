"""Dynamic text/cards drawn on top of static PNG chunks (letters, words, HUD values)."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import (
    CARD_STYLES,
    HUD_PINK,
    PROMPT_ACCENT,
    PROMPT_BROWN,
    STAR_YELLOW,
    blit_fitted_text,
    blit_outlined_text,
    content_rect,
    draw_rounded_rect,
    draw_sparkle,
    fit_font_size,
    font,
)
from ui.chunk_manifest import _horizontal_center_px, card_slot_rects, row_tile_slots, slot_rect
from ui.scene_view import SceneView

if TYPE_CHECKING:
    from engine.asset_manager import AssetManager


def _field(view: SceneView, name: str, default: str = "") -> str:
    value = getattr(view, name, default)
    return str(value if value is not None else default)


def _draw_text_banner(surface: pygame.Surface, rect: pygame.Rect, text: str) -> None:
    if not text:
        return
    draw_rounded_rect(surface, rect, (255, 255, 255), radius=16, border=HUD_PINK, border_width=2)
    label = font(16, bold=True).render(text, True, PROMPT_BROWN)
    surface.blit(label, label.get_rect(center=rect.center))


def _draw_find_letter(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    letter = _field(view, str(spec.get("field") or "target_letter"), "A").upper()
    cx = int(SCREEN_WIDTH * (float(spec.get("x_pct") or 0.395) + float(spec.get("w_pct") or 0.21) / 2))
    cy = int(SCREEN_HEIGHT * (float(spec.get("y_pct") or 0.19) + 0.04))
    find_label = font(44, bold=True).render("Find", True, PROMPT_BROWN)
    bounds = pygame.Rect(0, 0, int(SCREEN_WIDTH * 0.08), int(SCREEN_HEIGHT * 0.12))
    letter_size = fit_font_size(letter, bounds, fill_height_ratio=0.9)
    gap = 14
    letter_w = font(letter_size, bold=True).size(letter)[0]
    total_w = find_label.get_width() + gap + letter_w
    x = cx - total_w // 2
    surface.blit(find_label, (x, cy))
    blit_outlined_text(
        surface,
        letter,
        (x + find_label.get_width() + gap + letter_w // 2, cy - 4),
        letter_size,
        PROMPT_ACCENT,
        outline=(255, 255, 255),
        outline_width=2,
    )


def _draw_find_letter_png(
    surface: pygame.Surface,
    spec: dict[str, Any],
    view: SceneView,
    assets: AssetManager | None,
    asset_root: str,
) -> None:
    letter = _field(view, str(spec.get("field") or "target_letter"), "A").upper()
    draw_spec = dict(spec)
    if "container_w_pct" in draw_spec and "x_pct" not in draw_spec:
        cx = _horizontal_center_px(draw_spec)
        draw_spec["anchor"] = "center"
        draw_spec["x_pct"] = cx / SCREEN_WIDTH
    x, y, w, h = slot_rect(draw_spec)
    if assets is not None and asset_root:
        prompt = assets.scaled_find_prompt(asset_root, letter, w, h)
        if prompt is not None:
            draw_x = x + (w - prompt.get_width()) // 2
            draw_y = y + (h - prompt.get_height()) // 2
            surface.blit(prompt, (draw_x, draw_y))
            return
    _draw_find_letter(surface, spec, view)


def _draw_letter_cards(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    letters = tuple(str(item or "").upper() for item in (view.slot_letters or ()))
    slots: list[dict[str, Any]] = list(spec.get("slots") or [])
    for index, slot in enumerate(slots[:4]):
        if index >= len(letters):
            break
        x, y, w, h = slot_rect(slot)
        rect = pygame.Rect(x, y, w, h)
        style = CARD_STYLES[index % len(CARD_STYLES)]
        draw_rounded_rect(surface, rect, style["bg"], radius=18, border=style["border"], border_width=3)
        blit_fitted_text(
            surface,
            content_rect(rect, padding=14),
            letters[index],
            style["fg"],
            padding=0,
            fill_height_ratio=0.72,
            shadow=(50, 38, 48),
        )


def _tile_slot_rects(spec: dict[str, Any]) -> list[tuple[int, int, int, int]]:
    if str(spec.get("layout") or "") == "row":
        return row_tile_slots(spec)
    slots: list[dict[str, Any]] = list(spec.get("slots") or [])
    if slots:
        return [slot_rect(slot) for slot in slots[:4]]
    return row_tile_slots(spec)


def letter_tile_uses_selected(
    *,
    screen_id: str,
    tile_variant: str,
    slot_letter: str,
    target_letter: str,
) -> bool:
    """Challenge tiles are always normal; success highlights only the correct letter."""
    screen = str(screen_id or "").strip()
    variant = str(tile_variant or "normal").strip().lower()
    if screen == "letter_island_game" or variant == "normal":
        return False
    if screen == "letter_correct_feedback" or variant == "success":
        slot = str(slot_letter or "").strip().upper()
        target = str(target_letter or "").strip().upper()
        return bool(slot) and slot == target
    return False


def _draw_letter_tile_cards(
    surface: pygame.Surface,
    spec: dict[str, Any],
    view: SceneView,
    assets: AssetManager | None,
    asset_root: str,
) -> None:
    letters = tuple(str(item or "").upper() for item in (view.slot_letters or ()))
    slot_rects = _tile_slot_rects(spec)
    target_letter = _field(view, "target_letter", "").upper()
    tile_variant = str(spec.get("tile_variant") or "normal")
    screen_id = str(view.screen_id or "")
    for index, (x, y, w, h) in enumerate(slot_rects[:4]):
        if index >= len(letters):
            break
        selected = letter_tile_uses_selected(
            screen_id=screen_id,
            tile_variant=tile_variant,
            slot_letter=letters[index],
            target_letter=target_letter,
        )
        if assets is not None and asset_root:
            selected_scale = float(spec.get("selected_scale") or 1.22)
            tile = assets.scaled_letter_tile(
                asset_root,
                letters[index],
                w,
                h,
                selected=selected,
                selected_scale=selected_scale if selected else 1.0,
            )
            if tile is not None:
                draw_x = x + (w - tile.get_width()) // 2
                draw_y = y + (h - tile.get_height()) // 2
                surface.blit(tile, (draw_x, draw_y))
                continue
        rect = pygame.Rect(x, y, w, h)
        style = CARD_STYLES[index % len(CARD_STYLES)]
        draw_rounded_rect(surface, rect, style["bg"], radius=18, border=style["border"], border_width=3)
        blit_fitted_text(
            surface,
            content_rect(rect, padding=14),
            letters[index],
            style["fg"],
            padding=0,
            fill_height_ratio=0.72,
            shadow=(50, 38, 48),
        )


def _draw_letter_island_hud(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    x, y, w, h = slot_rect(spec)
    rect = pygame.Rect(x, y, w, h)
    name = _field(view, "child_name", "Lumi")
    energy = int(getattr(view, "lumi_energy", 100) or 100)
    energy_max = int(getattr(view, "lumi_energy_max", 100) or 100)
    name_size = max(16, min(22, int(h * 0.34)))
    energy_size = max(13, min(18, int(h * 0.26)))
    name_label = font(name_size, bold=True).render(name, True, HUD_PINK)
    surface.blit(name_label, (rect.x + int(w * 0.34), rect.y + int(h * 0.12)))
    energy_label = font(energy_size, bold=True).render(f"⚡ {energy}/{energy_max}", True, PROMPT_BROWN)
    surface.blit(energy_label, (rect.x + int(w * 0.34), rect.y + int(h * 0.42)))
    bar = pygame.Rect(rect.x + int(w * 0.34), rect.y + int(h * 0.68), int(w * 0.48), max(6, int(h * 0.14)))
    pygame.draw.rect(surface, (255, 255, 255), bar, border_radius=5)
    fill_w = int(bar.width * min(1.0, energy / max(1, energy_max)))
    if fill_w:
        pygame.draw.rect(surface, HUD_PINK, pygame.Rect(bar.x, bar.y, fill_w, bar.height), border_radius=5)


def _draw_letter_island_progress(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    text = _field(view, str(spec.get("field") or "progress_text"), "")
    if not text:
        return
    x, y, w, h = slot_rect(spec)
    rect = pygame.Rect(x, y, w, h)
    label = font(16, bold=True).render(text, True, PROMPT_BROWN)
    surface.blit(label, label.get_rect(center=rect.center))


def _draw_hud_stars_dynamic(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    x, y, w, h = slot_rect(spec)
    filled = max(0, min(3, int(getattr(view, "stars_filled", 0) or 0)))
    _draw_rating_stars(surface, x + w // 2, y + h // 2, filled, size=max(16, int(h * 0.42)))


def _wrap_text(text_font: pygame.font.Font, text: str, max_width: int) -> list[str]:
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


def _draw_mistake_speech(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    x, y, w, h = slot_rect(spec)
    rect = pygame.Rect(x, y, w, h)
    message = _field(view, str(spec.get("field") or "feedback_message"), str(spec.get("default") or ""))
    if not message:
        return
    target = _field(view, "target_letter", "B").upper()
    text_font = font(max(15, min(20, int(h * 0.22))), bold=True)
    lines = _wrap_text(text_font, message, int(w * 0.82))
    line_h = text_font.get_height() + 2
    total_h = line_h * len(lines)
    start_y = rect.centery - total_h // 2 + int(h * 0.04)
    for line in lines:
        if target and target in line:
            parts = line.split(target)
            segments: list[tuple[str, tuple[int, int, int]]] = []
            for part_index, part in enumerate(parts):
                if part:
                    segments.append((part, PROMPT_BROWN))
                if part_index < len(parts) - 1:
                    segments.append((target, (155, 95, 195)))
            line_w = sum(text_font.size(text)[0] for text, _ in segments)
            cursor_x = rect.centerx - line_w // 2
            for text, color in segments:
                label = text_font.render(text, True, color)
                surface.blit(label, (cursor_x, start_y))
                cursor_x += label.get_width()
        else:
            label = text_font.render(line, True, PROMPT_BROWN)
            surface.blit(label, label.get_rect(midtop=(rect.centerx, start_y)))
        start_y += line_h


def _draw_bd_hint_panel(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    message = _field(view, "feedback_message", "")
    if "belly" not in message.lower():
        return
    x, y, w, h = slot_rect(spec)
    panel = pygame.Rect(x, y, w, h)
    draw_rounded_rect(surface, panel, (255, 255, 255), radius=16, border=(210, 185, 155), border_width=2)
    b_rect = pygame.Rect(panel.x + int(w * 0.08), panel.centery - int(h * 0.28), int(h * 0.55), int(h * 0.55))
    d_rect = pygame.Rect(panel.right - int(w * 0.08) - int(h * 0.55), panel.centery - int(h * 0.28), int(h * 0.55), int(h * 0.55))
    for rect, letter, col in ((b_rect, "B", (155, 95, 195)), (d_rect, "D", (85, 165, 105))):
        draw_rounded_rect(surface, rect, (245, 240, 250), radius=10, border=col, border_width=2)
        blit_fitted_text(surface, rect, letter, col, padding=8, fill_height_ratio=0.65)
    hint = font(max(14, int(h * 0.22)), bold=True).render("B has a belly.", True, PROMPT_BROWN)
    surface.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - int(h * 0.22))))


def _draw_word_cards(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    words = tuple(str(item or "").lower() for item in (view.slot_words or ()))
    slots: list[dict[str, Any]] = list(spec.get("slots") or [])
    for index, slot in enumerate(slots[:4]):
        if index >= len(words):
            break
        x, y, w, h = slot_rect(slot)
        rect = pygame.Rect(x, y, w, h)
        style = CARD_STYLES[index % len(CARD_STYLES)]
        draw_rounded_rect(surface, rect, style["bg"], radius=18, border=style["border"], border_width=3)
        blit_fitted_text(surface, content_rect(rect, padding=12), words[index], style["fg"], padding=0)


def _draw_touch_word(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    word = _field(view, str(spec.get("field") or "target_word"), "cat").lower()
    cx = int(SCREEN_WIDTH * (float(spec.get("x_pct") or 0.34) + 0.16))
    cy = int(SCREEN_HEIGHT * (float(spec.get("y_pct") or 0.22) + 0.03))
    text = f"Touch the {word}"
    blit_outlined_text(surface, text, (cx, cy), 42, PROMPT_BROWN, outline=(255, 255, 255), outline_width=2)


def _draw_touch_word_png(
    surface: pygame.Surface,
    spec: dict[str, Any],
    view: SceneView,
    assets: AssetManager | None,
    asset_root: str,
) -> None:
    """Place only the target-word art beside the baked-in 'Touch the' on the background."""
    word = _field(view, str(spec.get("field") or "target_word"), "cat").lower()
    x, y, w, h = slot_rect(spec)
    valign = str(spec.get("valign") or "middle").lower()
    halign = str(spec.get("halign") or "left").lower()
    if assets is not None and asset_root:
        word_surface = assets.scaled_word_prompt(
            asset_root,
            word,
            w,
            h,
            fit=str(spec.get("fit") or "contain"),
        )
        if word_surface is not None:
            if halign == "center":
                draw_x = x + (w - word_surface.get_width()) // 2
            elif halign == "right":
                draw_x = x + w - word_surface.get_width()
            else:
                draw_x = x
            if valign == "bottom":
                draw_y = y + h - word_surface.get_height()
            elif valign == "top":
                draw_y = y
            else:
                draw_y = y + (h - word_surface.get_height()) // 2
            surface.blit(word_surface, (draw_x, draw_y))
            return
    blit_outlined_text(
        surface,
        word,
        (x + w // 2, y + h // 2 - 4),
        fit_font_size(word, pygame.Rect(0, 0, w, h), fill_height_ratio=0.75),
        PROMPT_ACCENT,
        outline=(255, 255, 255),
        outline_width=2,
    )


def _word_object_uses_selected(
    *,
    screen_id: str,
    tile_variant: str,
    slot_word: str,
    target_word: str,
) -> bool:
    variant = str(tile_variant or "normal").lower()
    active = str(screen_id or "").strip()
    if variant == "normal" and active == "word_garden_game":
        return False
    slot = str(slot_word or "").strip().lower()
    target = str(target_word or "").strip().lower()
    return bool(slot) and slot == target


def _draw_word_object_cards(
    surface: pygame.Surface,
    spec: dict[str, Any],
    view: SceneView,
    assets: AssetManager | None,
    asset_root: str,
) -> None:
    words = tuple(str(item or "").lower() for item in (view.slot_words or ()))
    slot_rects = card_slot_rects(spec)
    target_word = _field(view, "target_word", "").lower()
    tile_variant = str(spec.get("tile_variant") or "normal")
    screen_id = str(view.screen_id or "")
    fit = str(spec.get("fit") or "fill")
    pad_x = int(SCREEN_WIDTH * float(spec.get("pad_x_pct") or 0))
    pad_y = int(SCREEN_HEIGHT * float(spec.get("pad_y_pct") or 0))
    raw_offset = spec.get("offset_x_px") or 0
    for index, (x, y, w, h) in enumerate(slot_rects[:4]):
        if index >= len(words):
            break
        if isinstance(raw_offset, list):
            offset_x = int(raw_offset[index] if index < len(raw_offset) else (raw_offset[-1] if raw_offset else 0))
        else:
            offset_x = int(raw_offset or 0)
        selected = _word_object_uses_selected(
            screen_id=screen_id,
            tile_variant=tile_variant,
            slot_word=words[index],
            target_word=target_word,
        )
        inner = pygame.Rect(x + pad_x, y + pad_y, max(1, w - pad_x * 2), max(1, h - pad_y * 2))
        if assets is not None and asset_root:
            selected_scale = float(spec.get("selected_scale") or 1.08)
            tile = assets.scaled_word_object(
                asset_root,
                words[index],
                inner.width,
                inner.height,
                selected=selected,
                selected_scale=selected_scale if selected else 1.0,
                fit=fit,
            )
            if tile is not None:
                draw_x = inner.x + (inner.width - tile.get_width()) // 2 + offset_x
                draw_y = inner.y + (inner.height - tile.get_height()) // 2
                surface.blit(tile, (draw_x, draw_y))


def _draw_speech_bubble(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    x, y, w, h = slot_rect(spec)
    rect = pygame.Rect(x, y, w, h)
    message = _field(view, str(spec.get("field") or "feedback_message"), str(spec.get("default") or ""))
    if not message:
        return
    if spec.get("frame", True):
        draw_rounded_rect(surface, rect, (255, 255, 255), radius=20, border=HUD_PINK, border_width=2)
    label = font(18, bold=True).render(message, True, PROMPT_BROWN)
    surface.blit(label, label.get_rect(center=rect.center))


def _blit_text_segments(
    surface: pygame.Surface,
    segments: list[tuple[str, tuple[int, int, int]]],
    *,
    center_x: int,
    y: int,
    size: int,
) -> None:
    total_w = sum(font(size, bold=True).size(text)[0] for text, _ in segments)
    x = center_x - total_w // 2
    for text, color in segments:
        label = font(size, bold=True).render(text, True, color)
        surface.blit(label, (x, y))
        x += label.get_width()


def _draw_welcome_speech(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    x, y, w, h = slot_rect(spec)
    rect = pygame.Rect(x, y, w, h)
    message = _field(view, str(spec.get("field") or "feedback_message"), str(spec.get("default") or ""))
    if not message:
        message = "Hi! I'm Lumi! Let's learn together!"
    line1_y = rect.y + int(rect.height * 0.28)
    line2_y = rect.y + int(rect.height * 0.62)
    size = max(18, min(28, int(rect.height * 0.28)))
    purple = (155, 95, 195)
    pink = (235, 95, 135)
    if "lumi" in message.lower() and "learn" in message.lower():
        _blit_text_segments(
            surface,
            [("Hi! ", purple), ("I'm ", PROMPT_BROWN), ("Lumi!", pink)],
            center_x=rect.centerx + int(rect.width * 0.04),
            y=line1_y,
            size=size,
        )
        line2 = font(size, bold=True).render("Let's learn together!", True, PROMPT_BROWN)
        surface.blit(line2, line2.get_rect(center=(rect.centerx + int(rect.width * 0.04), line2_y + line2.get_height() // 2)))
    else:
        label = font(size, bold=True).render(message, True, PROMPT_BROWN)
        surface.blit(label, label.get_rect(center=rect.center))


def _draw_loading_bar(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    x, y, w, h = slot_rect(spec)
    outer = pygame.Rect(x, y, w, h)
    draw_rounded_rect(surface, outer, (255, 255, 255), radius=12, border=HUD_PINK, border_width=2)
    progress = max(0.05, min(1.0, float(view.loading_progress or 0)))
    fill = outer.inflate(-6, -6)
    fill.width = int(fill.width * progress)
    if fill.width:
        draw_rounded_rect(surface, fill, (255, 210, 90), radius=10)


def _parse_color(value: object, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return (int(value[0]), int(value[1]), int(value[2]))
    if isinstance(value, str) and value.startswith("#") and len(value) == 7:
        return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))
    return fallback


def _draw_rating_stars(surface: pygame.Surface, center_x: int, center_y: int, filled: int, *, size: int = 22) -> None:
    gap = int(size * 1.15)
    start_x = center_x - gap
    for index in range(3):
        cx = start_x + index * gap
        if index < filled:
            _draw_filled_star(surface, (cx, center_y), size)
        else:
            glyph = font(size, bold=True).render("★", True, (210, 195, 205))
            surface.blit(glyph, glyph.get_rect(center=(cx, center_y)))


def _draw_profile_cards(
    surface: pygame.Surface,
    spec: dict[str, Any],
    view: SceneView,
    assets: AssetManager | None,
    screen_id: str,
) -> None:
    if assets is None:
        return
    for slot in spec.get("slots") or []:
        if not isinstance(slot, dict):
            continue
        x, y, w, h = slot_rect(slot)
        rect = pygame.Rect(x, y, w, h)
        avatar_file = str(slot.get("avatar") or "")
        avatar = assets.scaled_chunk(screen_id, avatar_file, int(w * 0.72), int(h * 0.42), fit="contain")
        if avatar is not None:
            avatar_y = rect.y + int(h * 0.11)
            surface.blit(avatar, avatar.get_rect(midtop=(rect.centerx, avatar_y)))
        name = str(slot.get("name") or "")
        if name:
            name_color = _parse_color(slot.get("name_color"), PROMPT_BROWN)
            name_size = max(18, min(28, int(h * 0.075)))
            label = font(name_size, bold=True).render(name, True, name_color)
            surface.blit(label, label.get_rect(midtop=(rect.centerx, rect.y + int(h * 0.66))))
        stars = max(0, min(3, int(slot.get("stars") or 0)))
        _draw_rating_stars(surface, rect.centerx, rect.y + int(h * 0.84), stars, size=max(14, int(h * 0.06)))


def _draw_filled_star(surface: pygame.Surface, center: tuple[int, int], size: int) -> None:
    cx, cy = center
    points: list[tuple[int, int]] = []
    for i in range(10):
        angle = i * 3.14159265 / 5 - 1.57079633
        radius = size if i % 2 == 0 else size // 2
        points.append((cx + int(radius * math.cos(angle)), cy + int(radius * math.sin(angle))))
    pygame.draw.polygon(surface, STAR_YELLOW, points)
    pygame.draw.polygon(surface, (230, 175, 45), points, width=max(1, size // 10))
    draw_sparkle(surface, cx - size // 3, cy - size // 3, size=max(2, size // 6), color=(255, 255, 255))


def _draw_splash_star_progress(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    x, y, w, h = slot_rect(spec)
    bar = pygame.Rect(x, y, w, h)
    star_count = max(1, int(spec.get("star_count") or 10))
    progress = max(0.0, min(1.0, float(view.loading_progress or 0)))
    filled = min(star_count, int(round(progress * star_count)))
    if filled == 0 and progress > 0:
        filled = 1
    inset_x = int(bar.width * 0.055)
    usable = bar.width - inset_x * 2
    step = usable / max(1, star_count - 1) if star_count > 1 else 0
    star_size = max(8, min(bar.height - 6, int(bar.height * 0.68)))
    cy = bar.centery + 1
    for index in range(filled):
        cx = bar.x + inset_x + int(step * index)
        _draw_filled_star(surface, (cx, cy), star_size)


def _draw_loading_label(surface: pygame.Surface, spec: dict[str, Any], view: SceneView) -> None:
    x, y, w, h = slot_rect(spec)
    rect = pygame.Rect(x, y, w, h)
    label = font(26, bold=True).render("Loading...", True, (235, 95, 135))
    left_star = font(18, bold=True).render("★", True, (235, 95, 135))
    gap = 10
    total_w = left_star.get_width() + gap + label.get_width() + gap + left_star.get_width()
    start_x = rect.centerx - total_w // 2
    surface.blit(left_star, left_star.get_rect(midleft=(start_x, rect.centery)))
    surface.blit(label, label.get_rect(center=rect.center))
    surface.blit(left_star, left_star.get_rect(midright=(start_x + total_w, rect.centery)))


def draw_dynamic_layers(
    surface: pygame.Surface,
    view: SceneView,
    dynamic: dict[str, Any],
    *,
    assets: AssetManager | None = None,
    screen_id: str = "",
) -> None:
    """Paint live game values defined in the chunk manifest for this screen."""
    if not dynamic:
        return
    active_screen = screen_id or view.screen_id
    for spec in dynamic.values():
        if not isinstance(spec, dict):
            continue
        layer_type = str(spec.get("type") or "")
        if layer_type == "text_banner":
            text = _field(view, str(spec.get("field") or ""))
            if text:
                x, y, w, h = slot_rect(spec)
                _draw_text_banner(surface, pygame.Rect(x, y, w, h), text)
        elif layer_type == "find_letter":
            _draw_find_letter(surface, spec, view)
        elif layer_type == "find_letter_png":
            _draw_find_letter_png(surface, spec, view, assets, active_screen)
        elif layer_type == "letter_cards":
            _draw_letter_cards(surface, spec, view)
        elif layer_type == "letter_tile_cards":
            _draw_letter_tile_cards(surface, spec, view, assets, active_screen)
        elif layer_type == "letter_island_hud":
            _draw_letter_island_hud(surface, spec, view)
        elif layer_type == "letter_island_progress":
            _draw_letter_island_progress(surface, spec, view)
        elif layer_type == "hud_stars_dynamic":
            _draw_hud_stars_dynamic(surface, spec, view)
        elif layer_type == "mistake_speech":
            _draw_mistake_speech(surface, spec, view)
        elif layer_type == "bd_hint_panel":
            _draw_bd_hint_panel(surface, spec, view)
        elif layer_type == "word_cards":
            _draw_word_cards(surface, spec, view)
        elif layer_type == "word_object_cards":
            _draw_word_object_cards(surface, spec, view, assets, active_screen)
        elif layer_type == "touch_word":
            _draw_touch_word(surface, spec, view)
        elif layer_type == "touch_word_png":
            _draw_touch_word_png(surface, spec, view, assets, active_screen)
        elif layer_type == "speech_bubble":
            _draw_speech_bubble(surface, spec, view)
        elif layer_type == "welcome_speech":
            _draw_welcome_speech(surface, spec, view)
        elif layer_type == "loading_bar":
            _draw_loading_bar(surface, spec, view)
        elif layer_type == "splash_star_progress":
            _draw_splash_star_progress(surface, spec, view)
        elif layer_type == "loading_label":
            _draw_loading_label(surface, spec, view)
        elif layer_type == "profile_cards":
            _draw_profile_cards(surface, spec, view, assets, active_screen)
