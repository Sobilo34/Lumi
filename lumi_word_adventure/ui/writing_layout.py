"""Convert OpenCV BGR board arrays into pygame surfaces."""
from __future__ import annotations

import pygame

from ui.components.primitives import pct_rect
from ui.writing_footer_layout import writing_footer_slots


def cv_board_to_surface(board) -> pygame.Surface | None:
    if board is None:
        return None
    try:
        import numpy as np

        if getattr(board, "size", 0) == 0:
            return None
        surf = pygame.surfarray.make_surface(np.rot90(board))
        surf = pygame.transform.rotate(surf, -270)
        surf = pygame.transform.flip(surf, False, True)
        return surf.convert_alpha()
    except (ImportError, ValueError, pygame.error, AttributeError):
        return None


WRITING_MARGIN_PCT = 0.20

# Left drawing board and right preview channel sit inside the 20% margin frame.
WRITING_BOARD_RECT = pct_rect(0.20, 0.20, 0.26, 0.52)
WRITING_PREVIEW_RECT = pct_rect(0.54, 0.20, 0.26, 0.52)
WRITING_PROMPT_Y = int(720 * 0.10)
WRITING_BRUSH_RADIUS = 7
WRITING_INK_COLOR = (25, 25, 35)

_writing_slots = writing_footer_slots()
WRITING_BTN_VERIFY = pct_rect(*_writing_slots[0])
WRITING_BTN_CLEAR = pct_rect(*_writing_slots[1])
WRITING_BTN_SWITCH = pct_rect(*_writing_slots[2])
