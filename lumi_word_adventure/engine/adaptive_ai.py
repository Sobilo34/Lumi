"""Rule-based adaptive tutoring helpers."""
from __future__ import annotations

from config import MAX_DIFFICULTY, MIN_DIFFICULTY
from engine.learner_model import LearnerModel


class AdaptiveAI:
    def choose_next_activity(self, learner: LearnerModel) -> str:
        if learner.weak_letters or learner.weak_words or learner.sentence_errors:
            return "practice_weak_skills"
        if learner.difficulty <= MIN_DIFFICULTY:
            return "letter_island"
        if learner.difficulty >= MAX_DIFFICULTY:
            return "sentence_castle"
        return "word_garden"

    def update_after_attempt(
        self,
        learner: LearnerModel,
        is_correct: bool,
        skill_key: str | None = None,
    ) -> LearnerModel:
        learner.attempts += 1
        if is_correct:
            learner.correct_answers += 1
            learner.correct_streak += 1
            learner.wrong_streak = 0
            if skill_key and skill_key in learner.weak_letters:
                learner.weak_letters.pop(skill_key, None)
            if learner.correct_streak >= 3:
                learner.difficulty = min(MAX_DIFFICULTY, learner.difficulty + 1)
        else:
            learner.wrong_streak += 1
            learner.correct_streak = 0
            if skill_key:
                learner.weak_letters[skill_key] = learner.weak_letters.get(skill_key, 0) + 1
            if learner.wrong_streak >= 2:
                learner.difficulty = max(MIN_DIFFICULTY, learner.difficulty - 1)
        return learner
