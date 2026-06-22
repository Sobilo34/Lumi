"""Tests for Writing Castle footer button layout."""
from __future__ import annotations

from ui.writing_footer_layout import writing_footer_slots


def test_writing_footer_slots_center_three_buttons() -> None:
    slots = writing_footer_slots()
    assert len(slots) == 3
    widths = [slot[2] for slot in slots]
    assert len(set(widths)) == 1
    total_width = slots[-1][0] + slots[-1][2] - slots[0][0]
    assert round(slots[0][0] + total_width / 2, 3) == 0.5
