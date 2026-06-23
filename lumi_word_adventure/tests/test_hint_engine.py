from engine.hint_engine import HintEngine
from engine.word_mastery import WORD_MASTERY_THRESHOLD, empty_word_mastery_record


def test_word_hint_uses_vocabulary_prompt_for_fish() -> None:
    engine = HintEngine()
    hint = engine.word_hint("fish", level=1)
    assert hint == "Touch the fish"


def test_word_hint_escalates_with_level() -> None:
    engine = HintEngine()
    level_two = engine.word_hint("fish", level=2)
    assert "Fish" in level_two
    assert "F" in level_two

    level_three = engine.word_hint("fish", level=3)
    assert "fish" in level_three.lower()


def test_word_hint_contrasts_wrong_selection() -> None:
    engine = HintEngine()
    hint = engine.word_hint(
        "fish",
        level=1,
        mistake_type="word_confusion",
        selected="bird",
    )
    assert "Bird" in hint
    assert "Fish" in hint


def test_letter_hint_handles_bd_confusion() -> None:
    engine = HintEngine()
    hint = engine.letter_hint("B", level=1, mistake_type="bd_confusion")
    assert "belly" in hint.lower()
    assert "B" in hint


def test_word_garden_success_does_not_unlock_bd_badge() -> None:
    from engine.scoring import check_badge_unlocks

    profile = {
        "badges": [],
        "mastered_letters": ["B", "D"],
        "mastered_words": ["fish"],
        "total_stars": 3,
        "voice_word_successes": 0,
        "word_mastery": {
            "fish": {
                **empty_word_mastery_record(),
                "mastery_score": WORD_MASTERY_THRESHOLD,
                "consecutive_correct": 2,
            }
        },
    }
    unlocked = check_badge_unlocks(profile)
    assert "B and D Master" not in unlocked
