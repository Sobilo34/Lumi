"""Writing Castle layout tests."""
from __future__ import annotations

from config import SCREEN_WIDTH
from ui.writing_layout import WRITING_BOARD_RECT


def test_writing_board_spans_most_of_screen_width() -> None:
    assert WRITING_BOARD_RECT.width >= int(SCREEN_WIDTH * 0.78)
    assert WRITING_BOARD_RECT.x <= int(SCREEN_WIDTH * 0.12)
