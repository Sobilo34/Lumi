"""Draw shipped UI control artwork over gameplay hitboxes."""
from __future__ import annotations

import pygame

from engine.control_assets import ControlAssets
from ui.components.primitives import (
    BUTTON_BLUE,
    BUTTON_PURPLE,
    BUTTON_YELLOW,
    blit_outlined_text,
    font,
)
from ui.hitboxes import Hitbox

_SKIP_ACTION_PREFIXES = ("select_letter_slot_", "select_word_slot_")
_CAPTION_KEYS = frozenset({"repeat", "hint", "speaker", "mic"})
_CAPTION_COLORS: dict[str, tuple[int, int, int]] = {
    "repeat": BUTTON_PURPLE,
    "hint": BUTTON_YELLOW,
    "speaker": BUTTON_BLUE,
    "mic": BUTTON_BLUE,
}


def control_key_for_hitbox(box: Hitbox, *, writing_mode: str = "letters") -> str | None:
    action = (box.action or "").lower()
    name = (box.name or "").lower()
    target = (box.target or "").lower()

    if action == "verify_writing" or name == "verify":
        return "verify"
    if action == "clear_writing" or name == "clear":
        return "clear"
    if action == "toggle_writing_mode" or name == "switch mode":
        if str(writing_mode or "letters").strip().lower() == "words":
            return "switch_to_letters"
        return "switch_to_word"

    if target == "letter_island_game" or name == "letter island":
        return "letter_island_world"
    if target == "word_garden_game" or name == "word garden":
        return "word_garden_world"
    if target == "writing_castle_game" or name == "writing castle":
        return "writing_castle_world"

    if target == "main_menu" or name == "home" or action == "home":
        return "home"
    if target == "settings" or name == "settings":
        return "settings"
    if action.startswith("repeat") or name.startswith("repeat"):
        return "repeat"
    if "hint" in action or "help" in action or name in {"hint", "help"}:
        return "hint"
    if action in {"start_letter_listening", "start_listening"} or name in {"microphone", "mic", "listen"}:
        return "mic"
    if action in {"next_letter_voice", "next_word_voice"} or name == "speak":
        return "speaker"
    if action in {"voice_or_speak_mode", "voice_mode", "replay_main_menu_audio"} or name == "speaker":
        return "speaker"
    if "skip" in action or name == "skip":
        return "skip"
    return None


def caption_for_control(box: Hitbox, key: str) -> str | None:
    """Short, child-friendly labels for learning action buttons."""
    if key not in _CAPTION_KEYS:
        return None
    action = (box.action or "").lower()
    name = (box.name or "").lower()
    if key == "repeat":
        return "Hear Again"
    if key == "hint":
        return "Get a Hint"
    if key == "mic":
        return "Listen"
    if key == "speaker":
        if action in {"next_letter_voice"}:
            return "New Letter"
        if action in {"next_word_voice"}:
            return "Speak"
        if action in {"voice_mode", "voice_or_speak_mode"}:
            return "Speak"
        return "Listen"
    return None


def _fit_caption_size(text: str, max_width: int, max_height: int) -> int:
    size = min(22, max(13, max_width // 5))
    glyphs = font(size, bold=True)
    while size > 11 and glyphs.size(text)[0] > max_width - 4:
        size -= 1
        glyphs = font(size, bold=True)
    if glyphs.size(text)[1] > max_height:
        size = max(11, min(size, max_height - 2))
    return size


def blit_control(
    surface: pygame.Surface,
    image: pygame.Surface,
    rect: pygame.Rect,
    *,
    caption: str | None = None,
    caption_color: tuple[int, int, int] = (68, 52, 82),
) -> None:
    w, h = rect.width, rect.height
    caption_band = 0
    if caption:
        caption_band = min(40, max(26, int(h * 0.34)))
    icon_h = max(1, h - caption_band)
    icon_rect = pygame.Rect(rect.x, rect.y, w, icon_h)
    sw, sh = image.get_size()
    scale = min(icon_rect.width / sw, icon_rect.height / sh)
    nw = max(1, int(sw * scale))
    nh = max(1, int(sh * scale))
    if (nw, nh) != (sw, sh):
        image = pygame.transform.smoothscale(image, (nw, nh))
    x = icon_rect.x + (icon_rect.width - nw) // 2
    y = icon_rect.y + (icon_rect.height - nh) // 2
    surface.blit(image, (x, y))
    if caption and caption_band > 0:
        caption_rect = pygame.Rect(rect.x, rect.bottom - caption_band, w, caption_band)
        size = _fit_caption_size(caption, caption_rect.width, caption_rect.height)
        blit_outlined_text(
            surface,
            caption,
            caption_rect.center,
            size,
            caption_color,
            outline=(255, 255, 255),
            outline_width=2,
        )


def draw_control_buttons(
    surface: pygame.Surface,
    hitboxes: list[Hitbox],
    controls: ControlAssets | None = None,
    *,
    writing_mode: str = "letters",
) -> None:
    assets = controls or ControlAssets()
    if not assets.available():
        return
    for box in hitboxes:
        action = box.action or ""
        if any(action.startswith(prefix) for prefix in _SKIP_ACTION_PREFIXES):
            continue
        key = control_key_for_hitbox(box, writing_mode=writing_mode)
        if key is None:
            continue
        rect = box.rect
        if rect.width <= 0 or rect.height <= 0:
            continue
        image = assets.scaled(key, rect.width, rect.height)
        if image is not None:
            caption = caption_for_control(box, key)
            color = _CAPTION_COLORS.get(key, (68, 52, 82))
            blit_control(surface, image, rect, caption=caption, caption_color=color)
