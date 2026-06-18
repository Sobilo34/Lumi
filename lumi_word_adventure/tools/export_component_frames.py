"""Export component renders for visual comparison with reference_interfaces/."""
from __future__ import annotations

import os

import pygame

from config import REFERENCE_INTERFACES_DIR, SCREEN_HEIGHT, SCREEN_WIDTH
from engine.screen_registry import ScreenRegistry
from ui.scene_factory import create_component_screen
from ui.scene_view import SceneView


def _sample_view(screen_id: str) -> SceneView:
    return SceneView(
        screen_id=screen_id,
        child_name="Player 1",
        lumi_energy=85,
        lumi_energy_max=100,
        stars_filled=2,
        progress_text="Letter journey: learning B (2/26)",
        target_letter="B",
        slot_letters=("B", "D", "P", "A"),
        held_letter="B",
        target_word="cat",
        slot_words=("cat", "dog", "sun", "ball"),
        voice_target="apple",
        sentence_prompt="Build the sentence: I see a cat.",
        sentence_words=("I", "see", "a", "cat"),
        sentence_slots=("I", "see", "", ""),
        feedback_message="Great job! This is B.",
        music_enabled=True,
        voice_enabled=True,
        difficulty_mode="Medium",
        settings_status="Settings saved.",
        teacher_report={
            "stars_earned": 12,
            "accuracy_percent": 78,
            "strong_skill": "Letters",
            "needs_practice": "B / D",
            "recommended_next_activity": "Word Garden",
        },
        offline_message="No microphone right now. You can keep learning offline.",
        microphone_status="Tap the mic to test your microphone.",
        practice_cards=("Practice B", "Practice D", "Practice Word Cat", "Practice Sentence"),
        badge_names=("Rising Reader",),
        loading_progress=0.72,
    )


def main() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    registry = ScreenRegistry()
    out_dir = REFERENCE_INTERFACES_DIR.parent / "component_renders"
    out_dir.mkdir(exist_ok=True)

    view = _sample_view("")
    for screen_id in registry.screen_ids:
        view.screen_id = screen_id
        screen = create_component_screen(screen_id, registry.get_hitboxes(screen_id), lambda v=view: v)
        screen.draw(surface)
        path = out_dir / f"{screen_id}.png"
        pygame.image.save(surface, str(path))
        print(f"wrote {path.name}")

    print(f"Reference PNGs: {REFERENCE_INTERFACES_DIR}")
    print(f"Component renders: {out_dir}")


if __name__ == "__main__":
    main()
