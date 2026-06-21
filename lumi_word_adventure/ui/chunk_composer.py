"""Compose a screen from PNG chunks + dynamic overlays."""
from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from engine.asset_manager import AssetManager
from ui.app_background import paint_app_background, screen_uses_app_background
from ui.chunk_manifest import LayerSpec, ScreenChunkSpec, slot_rect
from ui.dynamic_layers import draw_dynamic_layers
from ui.scene_view import SceneView

# Full-screen art replaced by the shared app background on non-exempt screens.
_BACKGROUND_LAYER_FILES = frozenset(
    {
        "background.png",
        "speak_background.png",
        "success_background.png",
        "failure_background.png",
    }
)


class ChunkComposer:
    def __init__(self, asset_manager: AssetManager) -> None:
        self.assets = asset_manager
        self._static_cache: dict[str, pygame.Surface] = {}
        self._foreground_cache: dict[str, pygame.Surface] = {}

    def warm_static(self, spec: ScreenChunkSpec) -> None:
        self._static_surface(spec)

    def _has_any_chunk(self, spec: ScreenChunkSpec) -> bool:
        asset_root = spec.asset_root or spec.screen_id
        screen_dir = self.assets.chunks_dir / asset_root
        if not screen_dir.is_dir():
            return False
        for layer in spec.layers:
            if layer.file and self.assets.chunk_exists(asset_root, layer.file):
                return True
        return False

    def compose(self, surface: pygame.Surface, spec: ScreenChunkSpec, view: SceneView) -> None:
        if screen_uses_app_background(spec.screen_id) and paint_app_background(surface):
            # Shared background painted; layer only the foreground chunks on top so
            # the new background shows through behind every component.
            if self._has_any_chunk(spec):
                surface.blit(self._foreground_surface(spec), (0, 0))
        elif self._has_any_chunk(spec):
            surface.blit(self._static_surface(spec), (0, 0))
        elif spec.fallback_image:
            surface.blit(self.assets.load_image(spec.fallback_image), (0, 0))
        else:
            surface.fill(pygame.Color("#F4C2C2"))

        draw_dynamic_layers(
            surface,
            view,
            spec.dynamic,
            assets=self.assets,
            screen_id=spec.asset_root or spec.screen_id,
        )

    def _static_surface(self, spec: ScreenChunkSpec) -> pygame.Surface:
        cached = self._static_cache.get(spec.screen_id)
        if cached is not None:
            return cached
        asset_root = spec.asset_root or spec.screen_id
        static = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for layer in spec.layers:
            if layer.repeat == "letter_slots":
                self._blit_card_frames(static, spec, asset_root)
            elif layer.repeat == "profile_slots":
                self._blit_profile_frames(static, spec, asset_root)
            else:
                self._blit_layer(static, asset_root, layer)
        self._static_cache[spec.screen_id] = static
        return static

    def _foreground_surface(self, spec: ScreenChunkSpec) -> pygame.Surface:
        """Static chunks minus full-screen backgrounds, on a transparent surface."""
        cached = self._foreground_cache.get(spec.screen_id)
        if cached is not None:
            return cached
        asset_root = spec.asset_root or spec.screen_id
        foreground = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for layer in spec.layers:
            if layer.repeat == "letter_slots":
                self._blit_card_frames(foreground, spec, asset_root)
            elif layer.repeat == "profile_slots":
                self._blit_profile_frames(foreground, spec, asset_root)
            elif layer.file in _BACKGROUND_LAYER_FILES:
                continue
            else:
                self._blit_layer(foreground, asset_root, layer)
        self._foreground_cache[spec.screen_id] = foreground
        return foreground

    def _blit_layer(self, surface: pygame.Surface, asset_root: str, layer: LayerSpec) -> None:
        image = self.assets.load_chunk(asset_root, layer.file)
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
        scaled = self.assets.scaled_chunk(asset_root, layer.file, w, h, fit=fit)
        if scaled is None:
            return
        draw_x = x + (w - scaled.get_width()) // 2
        draw_y = y + (h - scaled.get_height()) // 2
        surface.blit(scaled, (draw_x, draw_y))

    def _blit_card_frames(self, surface: pygame.Surface, spec: ScreenChunkSpec, asset_root: str) -> None:
        cards_spec = spec.dynamic.get("letter_cards") or spec.dynamic.get("word_cards") or {}
        if not isinstance(cards_spec, dict):
            return
        frame_file = str(cards_spec.get("card_frame") or "card_frame.png")
        for slot in cards_spec.get("slots") or []:
            if not isinstance(slot, dict):
                continue
            x, y, w, h = slot_rect(slot)
            scaled = self.assets.scaled_chunk(asset_root, frame_file, w, h, fit="fill")
            if scaled is not None:
                surface.blit(scaled, (x, y))

    def _blit_profile_frames(self, surface: pygame.Surface, spec: ScreenChunkSpec, asset_root: str) -> None:
        cards_spec = spec.dynamic.get("profile_cards") or {}
        if not isinstance(cards_spec, dict):
            return
        frame_file = str(cards_spec.get("card_frame") or "profile_card_frame.png")
        for slot in cards_spec.get("slots") or []:
            if not isinstance(slot, dict):
                continue
            x, y, w, h = slot_rect(slot)
            scaled = self.assets.scaled_chunk(asset_root, frame_file, w, h, fit="fill")
            if scaled is not None:
                surface.blit(scaled, (x, y))
