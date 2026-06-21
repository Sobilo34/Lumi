"""Remove export checkerboard/white backdrops from letter tile PNGs."""
from __future__ import annotations

import numpy as np
from PIL import Image


def _is_border_backdrop(r: np.ndarray, g: np.ndarray, b: np.ndarray, a: np.ndarray) -> np.ndarray:
    """Backdrop pixels only — never cream tile faces or coloured letter art."""
    peak = np.maximum(np.maximum(r, g), b)
    low = np.minimum(np.minimum(r, g), b)
    spread = peak.astype(np.int16) - low.astype(np.int16)
    neutral = spread <= 16
    return (
        (a < 8)
        | ((r < 10) & (g < 10) & (b < 10))
        | (neutral & (peak >= 248))
        | (neutral & (peak >= 110) & (peak <= 155))
        | (neutral & (peak >= 168) & (peak <= 225))
    )


def knock_out_letter_backdrop_array(rgba: np.ndarray) -> np.ndarray:
    """In-place-safe backdrop removal on an RGBA uint8 array."""
    rgba = np.array(rgba, dtype=np.uint8, copy=True)
    r, g, b, a = rgba[..., 0], rgba[..., 1], rgba[..., 2], rgba[..., 3]
    bg = _is_border_backdrop(r, g, b, a)
    h, w = bg.shape
    visited = np.zeros((h, w), dtype=bool)
    stack: list[tuple[int, int]] = []
    for x in range(w):
        stack.append((x, 0))
        stack.append((x, h - 1))
    for y in range(h):
        stack.append((0, y))
        stack.append((w - 1, y))
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y, x] or not bg[y, x]:
            continue
        visited[y, x] = True
        stack.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    rgba[visited, 3] = 0

    r, g, b, a = rgba[..., 0], rgba[..., 1], rgba[..., 2], rgba[..., 3]
    peak = np.maximum(np.maximum(r, g), b)
    low = np.minimum(np.minimum(r, g), b)
    spread = peak.astype(np.int16) - low.astype(np.int16)
    fringe = (a >= 8) & (spread <= 12) & (peak >= 232)
    outside = np.zeros((h, w), dtype=bool)
    stack = [(x, y) for x in range(w) for y in (0, h - 1) if a[y, x] < 8]
    stack += [(x, y) for y in range(h) for x in (0, w - 1) if a[y, x] < 8]
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or outside[y, x]:
            continue
        if a[y, x] >= 8 and not fringe[y, x]:
            continue
        outside[y, x] = True
        stack.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    rgba[outside & fringe, 3] = 0
    return rgba


def knock_out_letter_backdrop(image: Image.Image) -> Image.Image:
    """Flood-fill export padding from image edges; keep tile box and glow intact."""
    rgba = np.array(image.convert("RGBA"), dtype=np.uint8)
    return Image.fromarray(knock_out_letter_backdrop_array(rgba), mode="RGBA")
