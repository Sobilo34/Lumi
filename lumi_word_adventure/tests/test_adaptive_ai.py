from engine.adaptive_ai import (
    AdaptiveAI,
    choose_hint,
    choose_next_question,
    diagnose_letter_mistake,
    diagnose_sentence_mistake,
    diagnose_word_mistake,
    has_repeated_weak_letter,
    recommend_practice,
    should_decrease_difficulty,
    should_increase_difficulty,
)
from engine.learner_model import LearnerModel
from data_loader import load_default_profile, load_letters, load_sentences, load_vocabulary


def _make_learner(**overrides: object) -> LearnerModel:
    profile = load_default_profile()
    profile.update(
        {
            "correct_streak": 0,
            "wrong_streak": 0,
            "difficulty": 1,
            "correct_answers": 0,
            "attempts": 0,
            "weak_letters": {},
            "weak_words": {},
            "sentence_errors": {},
            "hint_usage": {},
            "badges": [],
        }
    )
    profile.update(overrides)
    return LearnerModel(profile_data=profile)


def test_correct_streak_increases_difficulty() -> None:
    learner = _make_learner(correct_streak=2, difficulty=1)
    ai = AdaptiveAI()

    ai.update_after_attempt(learner, True, skill_key="A")

    assert learner.correct_answers == 1
    assert learner.difficulty == 2
    assert should_increase_difficulty(learner.get_profile()) is True


def test_wrong_streak_decreases_difficulty() -> None:
    learner = _make_learner(wrong_streak=1, difficulty=2)
    ai = AdaptiveAI()

    ai.update_after_attempt(learner, False, skill_key="A")

    assert learner.wrong_streak == 2
    assert learner.difficulty == 1
    assert should_decrease_difficulty(learner.get_profile()) is True


def test_bd_repeated_mistake_triggers_bd_practice() -> None:
    profile = {"weak_letters": {"B": 2}, "correct_streak": 0, "wrong_streak": 0, "hint_usage": {}}

    recommendation = recommend_practice(profile)

    assert has_repeated_weak_letter(profile) == "B"
    assert recommendation["activity"] == "bd_practice"
    assert recommendation["focus"] == "B/D"


def test_weak_word_triggers_practice_recommendation() -> None:
    profile = {"weak_words": {"cat": 2}, "correct_streak": 0, "wrong_streak": 0, "hint_usage": {}}
    vocabulary = load_vocabulary()

    recommendation = recommend_practice(profile)
    question = choose_next_question(profile, vocabulary, "word")

    assert recommendation["activity"] == "word_garden_game"
    assert recommendation["support"] == "simplified_word_garden"
    assert recommendation["option_count"] == 2
    assert question["activity"] == "word_garden_game"
    assert question["option_count"] == 2
    assert question["question"]["word"] == "cat"


def test_sentence_order_error_triggers_easier_sentence_support() -> None:
    profile = {"sentence_errors": {"word_order": 2}, "correct_streak": 0, "wrong_streak": 0, "hint_usage": {}}
    sentences = load_sentences()

    recommendation = recommend_practice(profile)
    question = choose_next_question(profile, sentences, "sentence")

    assert recommendation["activity"] == "sentence_castle_game"
    assert recommendation["support"] == "ghost_hints"
    assert question["support"] == "ghost_hints"
    assert question["question"]["difficulty"] == 1


def test_diagnosis_helpers_return_expected_labels() -> None:
    letters = load_letters()

    assert diagnose_letter_mistake("B", "D") == "bd_confusion"
    assert diagnose_word_mistake("cat", "dog", load_vocabulary()) == "same_category_vocabulary_confusion"
    assert diagnose_sentence_mistake(["I", "see", "a", "cat"], ["see", "I", "a", "cat"]) == "word_order"
    assert choose_hint({"weak_letters": {"B": 2}, "hint_usage": {}}, "letter", "bd_confusion") == "B has a belly. D has a drum."
    assert choose_next_question({"weak_letters": {"B": 2}}, letters, "letter")["activity"] == "bd_practice"
