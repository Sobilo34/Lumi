from engine.adaptive_ai import AdaptiveAI
from engine.learner_model import LearnerModel


def test_choose_next_activity_prefers_practice_when_weak_skills_exist() -> None:
    learner = LearnerModel(weak_letters={"B": 2})
    ai = AdaptiveAI()

    assert ai.choose_next_activity(learner) == "practice_weak_skills"


def test_update_after_attempt_increases_difficulty_after_three_correct_answers() -> None:
    learner = LearnerModel(correct_streak=2, difficulty=1)
    ai = AdaptiveAI()

    ai.update_after_attempt(learner, True, skill_key="B")

    assert learner.correct_answers == 1
    assert learner.difficulty == 2
