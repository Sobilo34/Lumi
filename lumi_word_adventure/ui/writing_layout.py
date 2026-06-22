"""Writing Castle board geometry and drawing constants."""
from __future__ import annotations

from ui.components.primitives import pct_rect
from ui.writing_footer_layout import writing_footer_slots

# One large board (~80% width) between the prompt and footer controls.
WRITING_BOARD_RECT = pct_rect(0.10, 0.17, 0.80, 0.54)
WRITING_PROMPT_Y = int(720 * 0.10)
WRITING_BRUSH_RADIUS = 9
WRITING_INK_COLOR = (25, 25, 35)

_writing_slots = writing_footer_slots()
WRITING_BTN_VERIFY = pct_rect(*_writing_slots[0])
WRITING_BTN_CLEAR = pct_rect(*_writing_slots[1])
WRITING_BTN_SWITCH = pct_rect(*_writing_slots[2])
