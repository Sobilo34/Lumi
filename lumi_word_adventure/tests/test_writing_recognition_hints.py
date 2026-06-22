"""Shape-based letter disambiguation tests (no model required)."""
from __future__ import annotations

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from writing_recognition.hints import disambiguate_letter, has_crossbar, refine_with_expected_letter


def _f_like_roi() -> np.ndarray:
    roi = np.zeros((120, 90), dtype=np.uint8)
    roi[12:108, 16:28] = 255
    roi[12:24, 16:72] = 255
    roi[48:58, 16:68] = 255
    return roi


def _t_like_roi() -> np.ndarray:
    roi = np.zeros((120, 90), dtype=np.uint8)
    roi[12:108, 40:52] = 255
    roi[12:24, 18:78] = 255
    return roi


def test_f_shape_has_middle_crossbar() -> None:
    assert has_crossbar(_f_like_roi())
    assert not has_crossbar(_t_like_roi())


def test_disambiguate_corrects_t_to_f_when_middle_bar_present() -> None:
    roi = _f_like_roi()
    tops = [("T", 0.76), ("K", 0.20), ("E", 0.12)]
    letter, confidence, updated, note = disambiguate_letter(roi, "T", 0.76, tops)
    assert letter == "F"
    assert note is not None
    assert updated[0][0] == "F"


def test_refine_with_expected_letter_fixes_t_to_f() -> None:
    roi = _f_like_roi()
    tops = [("T", 0.40), ("K", 0.30), ("E", 0.28)]
    letter, _, _, note = refine_with_expected_letter(roi, "T", 0.40, tops, "F")
    assert letter == "F"
    assert note is not None
