"""Compose a screen from PNG chunks + dynamic overlays."""
from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from engine.asset_manager import AssetManager
from ui.chunk_manifest import LayerSpec, ScreenChunkSpec, slot_rect
from ui.dynamic_layers import draw_dynamic_layers
from ui.scene_view import SceneView


class ChunkComposer:
    def __init__(self, asset_manager: AssetManager) -> None:
        self.assets = asset_manager
        self._static_cache: dict[str, pygame.Surface] = {}

    def warm_static(self, spec: ScreenChunkSpec) -> None:
        self._static_surface(spec)

    def _has_any_chunk(self, spec: ScreenChunkSpec) -> bool:
        screen_dir = self.assets.chunks_dir / spec.screen_id
        if not screen_dir.is_dir():
            return False
        for layer in spec.layers:
            if layer.file and self.assets.chunk_exists(spec.screen_id, layer.file):
                return True
        return False

    def compose(self, surface: pygame.Surface, spec: ScreenChunkSpec, view: SceneView) -> None:
        if self._has_any_chunk(spec):
            surface.blit(self._static_surface(spec), (0, 0))
        elif spec.fallback_image:
            surface.blit(self.assets.load_image(spec.fallback_image), (0, 0))
        else:
            surface.fill(pygame.Color("#F4C2C2"))

        draw_dynamic_layers(surface, view, spec.dynamic, assets=self.assets, screen_id=spec.screen_id)

    def _static_surface(self, spec: ScreenChunkSpec) -> pygame.Surface:
        cached = self._static_cache.get(spec.screen_id)
        if cached is not None:
            return cached
        static = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for layer in spec.layers:
            if layer.repeat == "letter_slots":
                self._blit_card_frames(static, spec)
            elif layer.repeat == "profile_slots":
                self._blit_profile_frames(static, spec)
            else:
                self._blit_layer(static, spec.screen_id, layer)
        self._static_cache[spec.screen_id] = static
        return static

    def _blit_layer(self, surface: pygame.Surface, screen_id: str, layer: LayerSpec) -> None:
        image = self.assets.load_chunk(screen_id, layer.file)
        if image is None:
            return
        x, y, w, h = slot_rect(
            {
                "x_pct": layer.x_pct,
                "y_pct": layer.y_pct,
                "w_pct": layer.w_pct,
                "h_pct": layer.h_pct,
                "anchor": layer.anchor,
            }
        )
        if w <= 0 or h <= 0:
            return
        fit = layer.fit or ("fill" if layer.file == "background.png" else "contain")
        scaled = self.assets.scaled_chunk(screen_id, layer.file, w, h, fit=fit)
        if scaled is None:
            return
        draw_x = x + (w - scaled.get_width()) // 2
        draw_y = y + (h - scaled.get_height()) // 2
        surface.blit(scaled, (draw_x, draw_y))

    def _blit_card_frames(self, surface: pygame.Surface, spec: ScreenChunkSpec) -> None:
        cards_spec = spec.dynamic.get("letter_cards") or spec.dynamic.get("word_cards") or {}
        if not isinstance(cards_spec, dict):
            return
        frame_file = str(cards_spec.get("card_frame") or "card_frame.png")
        for slot in cards_spec.get("slots") or []:
            if not isinstance(slot, dict):
                continue
            x, y, w, h = slot_rect(slot)
            scaled = self.assets.scaled_chunk(spec.screen_id, frame_file, w, h, fit="fill")
            if scaled is not None:
                surface.blit(scaled, (x, y))

    def _blit_profile_frames(self, surface: pygame.Surface, spec: ScreenChunkSpec) -> None:
        cards_spec = spec.dynamic.get("profile_cards") or {}
        if not isinstance(cards_spec, dict):
            return
        frame_file = str(cards_spec.get("card_frame") or "profile_card_frame.png")
        for slot in cards_spec.get("slots") or []:
            if not isinstance(slot, dict):
                continue
            x, y, w, h = slot_rect(slot)
            scaled = self.assets.scaled_chunk(spec.screen_id, frame_file, w, h, fit="fill")
            if scaled is not None:
                surface.blit(scaled, (x, y))
