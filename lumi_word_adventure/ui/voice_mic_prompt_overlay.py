"""Small mic hint badge shown while the voice mic is idle."""
from __future__ import annotations

import pygame

from ui.components.primitives import font

MIC_HINT_MESSAGE = "Click the mic to speak."
_BADGE_RADIUS = 11


def mic_hitbox_from_hitboxes(hitboxes: list) -> pygame.Rect | None:
    for box in hitboxes:
        action = (getattr(box, "action", "") or "").lower()
        name = (getattr(box, "name", "") or "").lower()
        if action in {"start_letter_listening", "start_listening"} or name in {"microphone", "mic"}:
            return pygame.Rect(box.rect)
    return None


def mic_hint_badge_rect(mic_rect: pygame.Rect) -> pygame.Rect:
    center = (mic_rect.right - 6, mic_rect.top + 6)
    return pygame.Rect(0, 0, _BADGE_RADIUS * 2, _BADGE_RADIUS * 2).move(center)


def draw_mic_hint_badge(surface: pygame.Surface, mic_rect: pygame.Rect) -> pygame.Rect:
    """Draw a yellow ! badge at the mic button's top-right corner."""
    badge = mic_hint_badge_rect(mic_rect)
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
