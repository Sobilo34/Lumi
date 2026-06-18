"""Load per-screen chunk layout from data/ui_chunk_manifest.json."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from config import PROJECT_DIR, SCREEN_HEIGHT, SCREEN_WIDTH


MANIFEST_PATH = PROJECT_DIR / "data" / "ui_chunk_manifest.json"


@dataclass(frozen=True)
class LayerSpec:
    id: str
    file: str
    z: int
    x_pct: float
    y_pct: float
    w_pct: float
    h_pct: float
    repeat: str = ""
    anchor: str = "topleft"  # "topleft" | "center"
    fit: str = ""  # "" | "fill" | "contain"


@dataclass(frozen=True)
class ScreenChunkSpec:
    screen_id: str
    fallback_image: str
    layers: tuple[LayerSpec, ...] = ()
    dynamic: dict[str, Any] = field(default_factory=dict)
    asset_root: str = ""


def _pct_rect(x_pct: float, y_pct: float, w_pct: float, h_pct: float) -> dict[str, float]:
    return {"x_pct": x_pct, "y_pct": y_pct, "w_pct": w_pct, "h_pct": h_pct}


def _default_screen_spec(screen_id: str, fallback_image: str) -> ScreenChunkSpec:
    """Minimal spec: full reference PNG only until you add chunks to the manifest."""
    return ScreenChunkSpec(screen_id=screen_id, fallback_image=fallback_image, layers=(), dynamic={})


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, ScreenChunkSpec]:
    raw: dict[str, Any] = {}
    if MANIFEST_PATH.is_file():
        with MANIFEST_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        raw = payload.get("screens") or {}

    specs: dict[str, ScreenChunkSpec] = {}
    for screen_id, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        layers: list[LayerSpec] = []
        for layer in entry.get("layers") or []:
            if not isinstance(layer, dict):
                continue
            layers.append(
                LayerSpec(
                    id=str(layer.get("id") or layer.get("file") or "layer"),
                    file=str(layer.get("file") or ""),
                    z=int(layer.get("z") or 0),
                    x_pct=float(layer.get("x_pct") or 0),
                    y_pct=float(layer.get("y_pct") or 0),
                    w_pct=float(layer.get("w_pct") or 1),
                    h_pct=float(layer.get("h_pct") or 1),
                    repeat=str(layer.get("repeat") or ""),
                    anchor=str(layer.get("anchor") or "topleft"),
                    fit=str(layer.get("fit") or ""),
                )
            )
        layers.sort(key=lambda item: item.z)
        specs[screen_id] = ScreenChunkSpec(
            screen_id=screen_id,
            fallback_image=str(entry.get("fallback_image") or ""),
            layers=tuple(layers),
            dynamic=dict(entry.get("dynamic") or {}),
            asset_root=str(entry.get("asset_root") or screen_id),
        )
    return specs


def get_screen_spec(screen_id: str, *, fallback_image: str) -> ScreenChunkSpec:
    specs = load_manifest()
    if screen_id in specs:
        spec = specs[screen_id]
        if spec.fallback_image:
            return spec
        return ScreenChunkSpec(
            screen_id=screen_id,
            fallback_image=fallback_image,
            layers=spec.layers,
            dynamic=spec.dynamic,
            asset_root=spec.asset_root or screen_id,
        )
    return _default_screen_spec(screen_id, fallback_image)


def slot_rect(spec: dict[str, Any]) -> tuple[int, int, int, int]:
    w = int(SCREEN_WIDTH * float(spec.get("w_pct") or 0))
    h = int(SCREEN_HEIGHT * float(spec.get("h_pct") or 0))
    anchor = str(spec.get("anchor") or "topleft")
    if anchor == "center":
        cx = int(SCREEN_WIDTH * float(spec.get("x_pct") or 0))
        cy = int(SCREEN_HEIGHT * float(spec.get("y_pct") or 0))
        return cx - w // 2, cy - h // 2, w, h
    x = int(SCREEN_WIDTH * float(spec.get("x_pct") or 0))
    y = int(SCREEN_HEIGHT * float(spec.get("y_pct") or 0))
    return x, y, w, h


def _horizontal_center_px(spec: dict[str, Any]) -> int:
    """Center x within an optional board container, else x_pct on screen."""
    container_w = spec.get("container_w_pct")
    if container_w is not None:
        left = int(SCREEN_WIDTH * float(spec.get("container_x_pct") or 0))
        width = int(SCREEN_WIDTH * float(container_w))
        return left + width // 2
    return int(SCREEN_WIDTH * float(spec.get("x_pct") or 0.5))


def row_tile_slots(spec: dict[str, Any]) -> list[tuple[int, int, int, int]]:
    """Evenly spaced tile rects centered in the board container or at x_pct."""
    count = int(spec.get("count") or 4)
    tile_w = int(SCREEN_WIDTH * float(spec.get("tile_w_pct") or 0.11))
    tile_h = int(SCREEN_HEIGHT * float(spec.get("tile_h_pct") or 0.22))
    gap = int(SCREEN_WIDTH * float(spec.get("gap_pct") or 0.028))
    cx = _horizontal_center_px(spec)
    cy = int(SCREEN_HEIGHT * float(spec.get("y_pct") or 0.56))
    total_w = count * tile_w + max(0, count - 1) * gap
    left = cx - total_w // 2
    top = cy - tile_h // 2
    step = tile_w + gap
    return [(left + index * step, top, tile_w, tile_h) for index in range(count)]
