"""Shared layout for gameplay footer controls."""
from __future__ import annotations

FOOTER_Y_PCT = 0.79
FOOTER_H_PCT = 0.16
FOOTER_W_PCT = 0.11
FOOTER_GAP_PCT = 0.025


def footer_slots(count: int = 4) -> list[tuple[float, float, float, float]]:
    w = FOOTER_W_PCT
    h = FOOTER_H_PCT
    y = FOOTER_Y_PCT
    gap = FOOTER_GAP_PCT
    total = count * w + max(0, count - 1) * gap
    start = (1.0 - total) / 2
    return [(start + index * (w + gap), y, w, h) for index in range(count)]


def voice_footer_slots() -> list[tuple[float, float, float, float]]:
    return footer_slots(4)
