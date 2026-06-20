"""Badge icon asset mapping and badge unlock screen wiring."""
from __future__ import annotations

from engine.scoring import BADGE_ICON_FILES, badge_icon_filename
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
        "Sentence Builder",
        "Great Learner",
    }
    assert set(BADGE_ICON_FILES) == expected
    for name in expected:
        filename = badge_icon_filename(name)
        assert filename.endswith(".png")
        assert filename == BADGE_ICON_FILES[name]


def test_badge_unlock_manifest_has_background_and_icon_layer() -> None:
    spec = get_screen_spec("badge_unlock", fallback_image="21_badge_unlock.png")
    assert spec.asset_root == "badge_unlock"
    assert any(layer.file == "background.png" for layer in spec.layers)
    badge_layer = spec.dynamic.get("badge_icon")
    assert badge_layer is not None
    assert badge_layer.get("type") == "badge_icon_png"
    assert badge_layer.get("field") == "badge_names"
