"""Tests for letter tile backdrop removal."""
from __future__ import annotations

import numpy as np
from PIL import Image

from engine.letter_tile_bg import knock_out_letter_backdrop


def test_knock_out_removes_border_white_keeps_cream_tile() -> None:
    image = Image.new("RGBA", (120, 120), (255, 255, 255, 255))
    for y in range(35, 85):
        for x in range(35, 85):
            image.putpixel((x, y), (240, 228, 205, 255))
    cleaned = knock_out_letter_backdrop(image)
    arr = np.array(cleaned)
    assert arr[0, 0, 3] == 0
    assert arr[60, 60, 3] == 255
    assert arr[60, 60, 0] == 240


def test_knock_out_removes_attached_white_fringe() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for y in range(30, 70):
        for x in range(30, 70):
            image.putpixel((x, y), (240, 228, 205, 255))
    for offset in range(6):
        for x in range(28 - offset, 72 + offset):
            image.putpixel((x, 28 - offset), (250, 250, 250, 255))
            image.putpixel((x, 71 + offset), (250, 250, 250, 255))
        for y in range(28 - offset, 72 + offset):
            image.putpixel((28 - offset, y), (250, 250, 250, 255))
            image.putpixel((71 + offset, y), (250, 250, 250, 255))
    cleaned = knock_out_letter_backdrop(image)
    arr = np.array(cleaned)
    assert arr[20, 50, 3] == 0
    assert arr[50, 50, 3] == 255
