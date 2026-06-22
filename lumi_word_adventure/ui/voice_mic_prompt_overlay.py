"""Small mic hint badge shown while the voice mic is idle."""
from __future__ import annotations

import pygame

from ui.components.primitives import font

MIC_HINT_MESSAGE = "Click the mic to speak."
_BADGE_RADIUS = 11
# Distance from the mic button's right edge to the badge center.
_BADGE_X_INSET_LETTER_VOICE = 56
_BADGE_X_INSET_WORD_VOICE = 106


def mic_hint_badge_rect(mic_rect: pygame.Rect, *, x_inset: int = _BADGE_X_INSET_LETTER_VOICE) -> pygame.Rect:
    center = (mic_rect.right - int(x_inset), mic_rect.top + 6)
    return pygame.Rect(0, 0, _BADGE_RADIUS * 2, _BADGE_RADIUS * 2).move(center)


def mic_hint_badge_x_inset(screen_id: str) -> int:
    """Letter Island voice uses the standard inset; Word Garden voice shifts 50px further left."""
    if str(screen_id or "").strip().lower() == "voice_challenge":
        return _BADGE_X_INSET_WORD_VOICE
    return _BADGE_X_INSET_LETTER_VOICE
    for box in hitboxes:
        action = (getattr(box, "action", "") or "").lower()
        name = (getattr(box, "name", "") or "").lower()
        if action in {"start_letter_listening", "start_listening"} or name in {"microphone", "mic"}:
            return pygame.Rect(box.rect)
    return None


def draw_mic_hint_badge(
    surface: pygame.Surface,
    mic_rect: pygame.Rect,
    *,
    x_inset: int = _BADGE_X_INSET_LETTER_VOICE,
) -> pygame.Rect:
    """Draw a yellow ! badge near the mic button's top-right corner."""
    badge = mic_hint_badge_rect(mic_rect, x_inset=x_inset)
    pygame.draw.circle(surface, (255, 210, 70), badge.center, _BADGE_RADIUS)
    pygame.draw.circle(surface, (255, 255, 255), badge.center, _BADGE_RADIUS, 2)
    label = font(16, bold=True).render("!", True, (255, 255, 255))
    surface.blit(label, label.get_rect(center=badge.center))
    return badge


def draw_voice_mic_prompt_overlay(
    screen: pygame.Surface,
    *,
    mic_rect: pygame.Rect | None = None,
    shown_at_ms: int = 0,
    now_ms: int | None = None,
) -> pygame.Rect | None:
    """Back-compat wrapper: draw only the small badge when a mic rect is known."""
    del shown_at_ms, now_ms
    if mic_rect is None:
        return None
    return draw_mic_hint_badge(screen, mic_rect)
