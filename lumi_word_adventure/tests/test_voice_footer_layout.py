"""Tests for voice footer button layout."""
from __future__ import annotations

from ui.voice_footer_layout import footer_slots


def test_voice_footer_slots_are_evenly_spaced() -> None:
    slots = footer_slots(4)
    assert len(slots) == 4
    widths = [slot[2] for slot in slots]
    heights = [slot[3] for slot in slots]
    assert len(set(widths)) == 1
    assert len(set(heights)) == 1
    gaps = [slots[index + 1][0] - (slots[index][0] + slots[index][2]) for index in range(3)]
    assert len(set(round(gap, 4) for gap in gaps)) == 1
    total_width = slots[-1][0] + slots[-1][2] - slots[0][0]
    assert round(slots[0][0] + total_width / 2, 3) == 0.5


def test_game_footer_slots_center_three_buttons() -> None:
    slots = footer_slots(3)
    assert len(slots) == 3
    total_width = slots[-1][0] + slots[-1][2] - slots[0][0]
    assert round(slots[0][0] + total_width / 2, 3) == 0.5
