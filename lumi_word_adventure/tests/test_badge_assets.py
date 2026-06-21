"""Badge icon asset mapping and badge unlock screen wiring."""
from __future__ import annotations

import pygame

from engine.scoring import BADGE_ICON_FILES, badge_icon_filename
from ui.badge_overlay import draw_badge_unlock_overlay
from ui.chunk_manifest import get_screen_spec


def test_all_known_badges_map_to_icon_files() -> None:
    expected = {
        "Badge A",
        "Badge B",
        "Badge C",
        "Letter Island Complete",
        "B and D Master",
        "Word Explorer",
        "Brave Speaker",
        "Great Learner",
    }
    assert set(BADGE_ICON_FILES) == expected
    for name in expected:
        filename = badge_icon_filename(name)
        assert filename.endswith(".png")
        assert filename == BADGE_ICON_FILES[name]


def test_badge_overlay_uses_subtitle_without_background_box() -> None:
    pygame.init()
    surface = pygame.Surface((1280, 720))
    surface.fill((120, 60, 160))
    draw_badge_unlock_overlay(surface, badge_names=("Badge A",))
    ribbon = pygame.Rect(int(1280 * 0.26), int(720 * 0.532), int(1280 * 0.48), int(720 * 0.068))
    sample = surface.get_at(ribbon.center)
    assert sample[0] > 100 or sample[1] > 60


def test_process_badge_icon_removes_white_export_square() -> None:
    from engine.asset_manager import _process_badge_icon

    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    size = 120
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    surface.fill((255, 255, 255, 255))
    pygame.draw.circle(surface, (255, 80, 120, 255), (size // 2, size // 2), 36)
    processed = _process_badge_icon(surface)
    pw, ph = processed.get_size()
    assert pw < size
    assert ph < size
    assert processed.get_at((pw // 2, ph // 2)).a > 200


def test_badge_unlock_manifest_has_background_and_icon_layer() -> None:
    spec = get_screen_spec("badge_unlock", fallback_image="21_badge_unlock.png")
    assert spec.asset_root == "badge_unlock"
    assert any(layer.file == "background.png" for layer in spec.layers)
    badge_layer = spec.dynamic.get("badge_icon")
    assert badge_layer is not None
    assert badge_layer.get("type") == "badge_icon_png"
    assert badge_layer.get("field") == "badge_names"
