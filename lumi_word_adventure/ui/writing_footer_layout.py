"""Centered footer layout for Writing Castle action buttons."""
from __future__ import annotations

WRITING_FOOTER_Y_PCT = 0.76
WRITING_FOOTER_H_PCT = 0.11
WRITING_FOOTER_W_PCT = 0.22
WRITING_FOOTER_GAP_PCT = 0.025


def writing_footer_slots(count: int = 4) -> list[tuple[float, float, float, float]]:
    w = WRITING_FOOTER_W_PCT
    h = WRITING_FOOTER_H_PCT
    y = WRITING_FOOTER_Y_PCT
    gap = WRITING_FOOTER_GAP_PCT
    total = count * w + max(0, count - 1) * gap
    start = (1.0 - total) / 2
    return [(start + index * (w + gap), y, w, h) for index in range(count)]
