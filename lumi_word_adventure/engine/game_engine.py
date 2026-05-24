"""Main runtime loop and screen orchestration."""
from __future__ import annotations

import pygame

from config import DEBUG_HITBOXES, SPLASH_DURATION_MS, VOICE_ENABLED_DEFAULT, VOICE_FALLBACK_SCREEN_ID
from engine.asset_manager import AssetManager
from engine.adaptive_ai import choose_hint, choose_next_question, diagnose_word_mistake, recommend_practice
from engine.feedback import get_feedback, get_hint, get_lumi_speech
from engine.game_state import GameState
from engine.learner_model import LearnerModel
from engine.screen_registry import ScreenRegistry
from engine.scoring import calculate_stars, check_badge_unlocks, update_score
from data_loader import load_vocabulary
from reports.report_generator import generate_report
from ui.screens import create_screen_with_hitboxes
from voice.text_to_speech import TextToSpeech
import voice.speech_to_text as speech_to_text
from voice.voice_checker import check_spoken_answer


class GameEngine:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.asset_manager = AssetManager()
        self.registry = ScreenRegistry()
        self.voice = TextToSpeech(enabled=VOICE_ENABLED_DEFAULT)
        self.learner = LearnerModel()
        self.state = GameState(splash_started_at=pygame.time.get_ticks())
        self.word_questions = load_vocabulary()
        self.voice.set_enabled(self.state.voice_enabled)
        self._log_voice_startup_status()
        self._configure_letter_island_task()
        self.screens = {
            screen_id: create_screen_with_hitboxes(
                self.registry.get_image_filename(screen_id),
                self.registry.get_hitboxes(screen_id),
                self.asset_manager,
            )
            for screen_id in self.registry.screen_ids
        }
        self.state.current_screen_id = self.registry.screen_ids[0]
        self.current_screen = self.screens[self.state.current_screen_id]

    def _log_voice_startup_status(self) -> None:
        status_message = speech_to_text.get_status_message()
        backend = "not_ready"
        if "Vosk offline" in status_message:
            backend = "vosk_offline"
        elif "SpeechRecognition" in status_message:
            backend = "speech_recognition"
        print(
            f"[Lumi Voice] tts_enabled={self.state.voice_enabled} "
            f"stt_available={speech_to_text.is_available()} backend={backend} status='{status_message}'"
        )

    def change_screen(self, screen_id: str) -> None:
        if screen_id in self.screens:
            previous_screen_id = self.state.current_screen_id
            if screen_id == "word_garden_game":
                if self.state.preserve_word_garden_task:
                    self.state.preserve_word_garden_task = False
                else:
                    self._configure_word_garden_task()
            if screen_id == "sentence_castle_game" and previous_screen_id not in {
                "sentence_dragging",
                "sentence_mistake_hint",
            }:
                self._configure_sentence_castle_task()
            self.state.current_screen_id = screen_id
            self.current_screen = self.screens[screen_id]
            self.state.history.append(screen_id)
            self._speak_for_screen(screen_id)

    def _configure_letter_island_task(self) -> None:
        self.state.current_task_prompt = "Find the letter B."
        self.state.current_task_target = "B"
        self.state.current_hint_level = 0
        self.state.last_mistake_type = ""
        self.state.bd_confusion_attempts = 0
        self.state.bd_practice_target = ""
        self.state.bd_practice_step = 0

    def _configure_bd_practice(self, target_letter: str = "B") -> None:
        self.state.bd_practice_target = target_letter
        self.state.bd_practice_step = 0 if target_letter == "B" else 1
        self.state.current_task_target = target_letter
        self.state.current_task_prompt = f"Find the letter {target_letter}."
        self.state.current_hint_level = 0

    def _configure_word_garden_task(self) -> None:
        recommendation = recommend_practice(self.learner)
        next_question = choose_next_question(self.learner, self.word_questions, "word")
        question = next_question.get("question") or {}
        target_word = str(question.get("word") or "cat").strip().lower() or "cat"
        prompt = str(question.get("prompt") or f"Touch the {target_word}").strip()
        if not prompt.endswith((".", "!", "?")):
            prompt = f"{prompt}."

        self.state.current_task_target = target_word
        self.state.current_task_prompt = prompt
        self.state.current_hint_level = 0
        self.state.current_word_mode = str(next_question.get("reason") or recommendation.get("reason") or "")
        self.state.word_garden_support = str(next_question.get("support") or recommendation.get("support") or "")
        self.state.word_garden_option_count = int(next_question.get("option_count") or recommendation.get("option_count") or 4)
        self.state.last_word_selected = ""
        self.state.last_word_feedback_message = ""

    def _configure_voice_challenge_task(self) -> None:
        self.state.current_task_target = "apple"
        self.state.current_task_prompt = "Say apple."
        self.state.current_hint_level = 0

    def _configure_sentence_castle_task(self) -> None:
        self.state.current_task_target = "I see a cat"
        self.state.current_task_prompt = "Build the sentence."
        self.state.current_hint_level = 0
        self.state.sentence_target_words = ["I", "see", "a", "cat"]
        self.state.sentence_slots = ["", "", "", ""]
        self.state.sentence_locked_indices = []
        self.state.sentence_feedback_message = ""

    def _is_sentence_complete(self) -> bool:
        return all(bool(slot) for slot in self.state.sentence_slots)

    def _place_sentence_word(self, word: str) -> None:
        # click-to-place fallback: put the tapped word into the next free slot
        for idx in range(len(self.state.sentence_slots)):
            if self.state.sentence_slots[idx]:
                continue
            self.state.sentence_slots[idx] = word
            if self.state.current_screen_id == "sentence_castle_game":
                self.set_screen("sentence_dragging")
            if self._is_sentence_complete():
                self._evaluate_sentence_slots()
            return

    def _evaluate_sentence_slots(self) -> None:
        expected = ["I", "see", "a", "cat"]
        if self.state.sentence_slots == expected:
            stars_earned = calculate_stars(True, self.state.current_hint_level)
            self.learner.update_correct_streak()
            self.learner.attempts = int(self.learner.attempts) + 1
            self.learner.correct_answers = int(self.learner.correct_answers) + 1
            self.learner.update_accuracy()
            update_score(self.learner, stars_earned)
            self.state.sentence_feedback_message = "You built it!"
            self.voice.speak("You built it!")
            self.set_screen("sentence_correct_feedback")
            return

        self.learner.update_wrong_streak()
        self.learner.attempts = int(self.learner.attempts) + 1
        self.learner.update_accuracy()
        self.learner.record_sentence_error("word_order")
        self.state.last_mistake_type = "word_order"
        self.state.sentence_feedback_message = "Good try. Start with I."
        self.voice.speak("Good try. Start with I.")
        self.set_screen("sentence_mistake_hint")

    def _handle_sentence_hint(self) -> None:
        self.state.current_hint_level += 1
        hint_level = self.state.current_hint_level
        if hint_level == 1:
            self.voice.speak("Start with I.")
            return
        if hint_level == 2:
            if not self.state.sentence_slots[0]:
                self.state.sentence_slots[0] = "I"
            if 0 not in self.state.sentence_locked_indices:
                self.state.sentence_locked_indices.append(0)
            self.voice.speak("I is first. I placed it for you.")
            self.set_screen("sentence_dragging")
            if self._is_sentence_complete():
                self._evaluate_sentence_slots()
            return

        # Level 3 guided full sentence
        self.state.sentence_slots = ["I", "see", "a", "cat"]
        self.voice.speak("Guided sentence: I see a cat.")
        self._evaluate_sentence_slots()

    def _handle_sentence_action(self, action: str) -> bool:
        word_map = {
            "drag_word_I": "I",
            "drag_word_see": "see",
            "drag_word_a": "a",
            "drag_word_cat": "cat",
        }

        if action in word_map:
            self._place_sentence_word(word_map[action])
            return True

        if action == "repeat_sentence_prompt" or action == "repeat_prompt":
            self.voice.speak("Build the sentence.")
            return True

        if action == "show_hint" or action == "show_next_hint":
            self._handle_sentence_hint()
            return True

        if action == "try_again":
            if any(self.state.sentence_slots):
                self.set_screen("sentence_dragging")
            else:
                self.set_screen("sentence_castle_game")
            return True

        if action == "next_badge":
            self.set_screen("badge_unlock")
            return True

        if action in {"drop_a", "drop_cat"}:
            # click-to-place fallback keeps drag illusion; slot taps are optional
            return True

        return False

    def _handle_badges(self, unlocked: list[str]) -> None:
        """Record unlocked badges and switch to the badge unlock screen."""
        if not unlocked:
            return
        self.state.last_unlocked_badges = unlocked
        self.set_screen("badge_unlock")

    def _process_voice_capture_result(self, spoken: str | None) -> None:
        target_word = "apple"
        spoken_text = (spoken or "").strip().lower()
        self.state.last_spoken_text = spoken_text
        result = check_spoken_answer(spoken_text, target_word)

        if result == "correct":
            stars_earned = calculate_stars(True, self.state.current_hint_level)
            self.learner.update_correct_streak()
            self.learner.attempts = int(self.learner.attempts) + 1
            self.learner.correct_answers = int(self.learner.correct_answers) + 1
            self.learner.update_accuracy()
            update_score(self.learner, stars_earned)
            self.learner.mark_word_mastered(target_word)
            completed_worlds = list(self.learner.completed_worlds)
            if "voice_challenge" not in completed_worlds:
                completed_worlds.append("voice_challenge")
                self.learner.completed_worlds = completed_worlds
                self.learner.save_profile()
            unlocked = check_badge_unlocks(self.learner)
            self.state.current_hint_level = 0
            self.state.last_word_feedback_message = "You said apple!"
            if unlocked:
                self._handle_badges(unlocked)
                return
            self.set_screen("voice_correct_feedback")
            return

        self.learner.update_wrong_streak()
        self.learner.attempts = int(self.learner.attempts) + 1
        self.learner.update_accuracy()

        if result == "close":
            self.voice.speak("Almost! I heard something close. Try again.")
            self.set_screen("voice_challenge")
            return

        self.learner.record_weak_word(target_word)
        self.voice.speak("Good try! Open your mouth wide: a-pple. Say apple.")
        self.set_screen("voice_challenge")

    def _word_garden_hint_message(self) -> str:
        target_word = self.state.current_task_target or "cat"
        level = self.state.current_hint_level

        if target_word == "cat":
            if level <= 1:
                if self.state.last_mistake_type:
                    return choose_hint(self.learner, "word", self.state.last_mistake_type)
                return "Look for the cat."
            return "Cat says meow. Find the cat."

        if level <= 1:
            return f"Look for the {target_word}."
        return f"{target_word.capitalize()} is the word you want."

    def _word_garden_correct_message(self) -> str:
        target_word = self.state.current_task_target or "cat"
        return f"Wonderful! {target_word.capitalize()}."

    def _word_garden_mistake_message(self, selected_word: str) -> str:
        target_word = self.state.current_task_target or "cat"
        if self.state.last_mistake_type == "same_category_vocabulary_confusion" or {
            target_word,
            selected_word,
        } == {"cat", "dog"}:
            return "This is dog. A cat says meow. Find the cat."
        if target_word == "cat":
            return f"This is {selected_word}. A cat says meow. Find the cat."
        return f"This is {selected_word}. Look for {target_word}."

    def _advance_bd_practice(self) -> None:
        if self.state.bd_practice_target == "B":
            self.state.bd_practice_target = "D"
            self.state.bd_practice_step = 1
            self.state.current_task_target = "D"
            self.state.current_task_prompt = "Now find the letter D."
            self.voice.speak("Great job! Now find D.")
            return

        self.learner.mark_letter_mastered("D")
        unlocked_badges = check_badge_unlocks(self.learner)
        self.state.bd_practice_target = ""
        self.state.bd_practice_step = 2
        self.state.current_task_target = "B"
        self.state.current_task_prompt = "Find the letter B."
        self.voice.speak("Great job! You know B and D!")
        if "B and D Master" in unlocked_badges:
            self.set_screen("badge_unlock")
        else:
            self.set_screen("letter_correct_feedback")

    def set_screen(self, screen_id: str) -> None:
        self.change_screen(screen_id)

    def next_screen(self) -> None:
        self.change_screen(self.registry.next_screen_id(self.state.current_screen_id))

    def previous_screen(self) -> None:
        self.change_screen(self.registry.previous_screen_id(self.state.current_screen_id))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            self.next_screen()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            self.previous_screen()
            return
        action = self.current_screen.handle_event(event)
        if action:
            self._handle_action(action)

    def _handle_action(self, action: str) -> None:
        if action in self.screens:
            self.set_screen(action)
            return
        if action == "back":
            self.set_screen("main_menu")
            return
        if action == "home":
            if self.state.current_screen_id in {
                "world_map",
                "letter_island_game",
                "letter_correct_feedback",
                "letter_mistake_hint",
                "word_garden_game",
                "word_correct_feedback",
                "word_mistake_hint",
                "bd_practice",
                "sentence_castle_game",
                "sentence_mistake_hint",
                "sentence_correct_feedback",
            }:
                self.set_screen("world_map")
            else:
                self.set_screen("main_menu")
            return
        if action == "go_to_profile_selection":
            self.set_screen("profile_selection")
            return
        if action == "go_to_world_map":
            self.set_screen("world_map")
            return
        if action == "start_play":
            self.set_screen("world_map")
            return
        if action == "open_settings" or action == "settings":
            self.set_screen("settings")
            return
        if action == "test_mic" or action == "test_microphone":
            self.set_screen("microphone_check")
            return
        if action == "skip_mic":
            self.set_screen("settings")
            return
        if action == "play_again":
            self.set_screen("world_map")
            return
        if self.state.current_screen_id == "letter_correct_feedback" and action == "next_activity":
            if self.state.letter_demo_mode:
                self.set_screen("world_map")
            else:
                self._configure_letter_island_task()
                self.set_screen("letter_island_game")
            return
        if self.state.current_screen_id == "letter_mistake_hint":
            if action == "try_again":
                self.set_screen("letter_island_game")
                return
            if action == "repeat_prompt":
                self.voice.speak(self.state.current_task_prompt or "Find the letter B.")
                return
            if action == "next_hint_or_bd_practice":
                if self.state.bd_confusion_attempts >= 2:
                    self._configure_bd_practice("B")
                    self.set_screen("bd_practice")
                else:
                    self.state.current_hint_level += 1
                    self.learner.record_hint_usage(self.state.current_hint_level)
                    stronger_hint = get_hint("letter", self.state.current_hint_level, self.state.current_task_target or "B")
                    self.voice.speak(stronger_hint)
                return
        if self.state.current_screen_id == "word_garden_game":
            if action == "repeat_prompt":
                self.voice.speak(self.state.current_task_prompt or "Touch the cat.")
                return
            if action == "show_hint":
                self.state.current_hint_level += 1
                self.state.last_word_feedback_message = self._word_garden_hint_message()
                self.set_screen("word_mistake_hint")
                return
            if action == "voice_mode":
                self.set_screen("voice_challenge")
                return
            if action in {"answer_cat_correct", "answer_dog_wrong", "answer_sun_wrong", "answer_ball_wrong"}:
                selected_word = {
                    "answer_cat_correct": "cat",
                    "answer_dog_wrong": "dog",
                    "answer_sun_wrong": "sun",
                    "answer_ball_wrong": "ball",
                }[action]
                target_word = self.state.current_task_target or "cat"
                self.state.last_word_selected = selected_word
                if selected_word == target_word:
                    stars_earned = calculate_stars(True, self.state.current_hint_level)
                    self.learner.update_correct_streak()
                    self.learner.attempts = int(self.learner.attempts) + 1
                    self.learner.correct_answers = int(self.learner.correct_answers) + 1
                    self.learner.update_accuracy()
                    update_score(self.learner, stars_earned)
                    self.learner.mark_word_mastered(target_word)
                    unlocked = check_badge_unlocks(self.learner)
                    self.state.current_hint_level = 0
                    self.state.last_word_feedback_message = self._word_garden_correct_message()
                    if unlocked:
                        self._handle_badges(unlocked)
                        return
                    self.set_screen("word_correct_feedback")
                    return

                self.learner.update_wrong_streak()
                self.learner.attempts = int(self.learner.attempts) + 1
                self.learner.update_accuracy()
                self.learner.record_weak_word(target_word)
                mistake_type = diagnose_word_mistake(target_word, selected_word, self.word_questions)
                self.state.last_mistake_type = mistake_type
                self.state.last_word_feedback_message = get_feedback(
                    False,
                    mistake_type=mistake_type,
                    target=target_word,
                    selected=selected_word,
                )["message"]
                self.state.current_hint_level = 1
                self.set_screen("word_mistake_hint")
                return
            if action == "play_cat_sound":
                self.voice.speak("Cat says meow.")
                return
        if self.state.current_screen_id == "word_correct_feedback":
            if action == "next_voice_challenge":
                self._configure_voice_challenge_task()
                self.set_screen("voice_challenge")
                return
            if action == "home":
                self.set_screen("world_map")
                return
        if self.state.current_screen_id == "word_mistake_hint":
            if action == "try_again":
                self.state.preserve_word_garden_task = True
                self.set_screen("word_garden_game")
                return
            if action == "repeat_prompt":
                self.voice.speak(self.state.current_task_prompt or "Touch the cat.")
                return
            if action == "show_next_hint":
                self.state.current_hint_level += 1
                self.state.last_word_feedback_message = self._word_garden_hint_message()
                self.voice.speak(self.state.last_word_feedback_message)
                return
            if action == "play_cat_sound":
                self.voice.speak("Cat says meow.")
                return
        if self.state.current_screen_id == "voice_challenge":
            if action == "repeat_word":
                self.voice.speak("Say apple.")
                return
            if action == "voice_help":
                self.voice.speak("Listen: ah-puhl. Say apple.")
                return
            if action == "skip_voice":
                self.state.preserve_word_garden_task = True
                self.set_screen("word_garden_game")
                return
            if action == "start_listening":
                self._configure_voice_challenge_task()
                if not speech_to_text.is_available():
                    msg = speech_to_text.get_status_message()
                    self.voice.speak(msg)
                    self.set_screen("voice_challenge")
                    return
                self.set_screen("listening_state")
                spoken = speech_to_text.listen_once(timeout=5)
                self._process_voice_capture_result(spoken)
                return
        if self.state.current_screen_id == "bd_practice":
            if action == "repeat_bd_prompt":
                target_letter = self.state.bd_practice_target or "B"
                self.voice.speak(f"B has a belly. D has a drum. Find {target_letter}.")
                return
            if action == "bd_hint":
                self.voice.speak("B has a belly. D has a drum.")
                return
            if action in {"answer_B", "answer_D"}:
                target_letter = self.state.bd_practice_target or "B"
                selected_letter = "B" if action == "answer_B" else "D"
                if selected_letter == target_letter:
                    self.learner.update_correct_streak()
                    update_score(self.learner, calculate_stars(True, self.state.current_hint_level))
                    self.learner.mark_letter_mastered(selected_letter)
                    self._advance_bd_practice()
                else:
                    self.learner.update_wrong_streak()
                    self.state.last_mistake_type = "bd_confusion"
                    self.learner.record_weak_letter(target_letter)
                    self.voice.speak(get_feedback(False, mistake_type="bd_confusion")["message"])
                return
        if self.state.current_screen_id in {
            "sentence_castle_game",
            "sentence_dragging",
            "sentence_mistake_hint",
            "sentence_correct_feedback",
        }:
            if self._handle_sentence_action(action):
                return
        if self.state.current_screen_id == "listening_state":
            if action == "repeat_word":
                self.voice.speak("Say apple.")
                return
            if action in {"stop_listening", "stop_and_process"}:
                self.voice.speak("Listening stopped. Say apple when you are ready.")
                self.set_screen("voice_challenge")
                return
        if self.state.current_screen_id == "voice_correct_feedback":
            if action == "say_again":
                self._configure_voice_challenge_task()
                self.set_screen("voice_challenge")
                return
            if action == "next_activity":
                self.state.preserve_word_garden_task = True
                self.set_screen("word_garden_game")
                return
        if action == "view_report" or action == "open_report":
            self.set_screen("teacher_report")
            return
        if action == "continue_offline":
            self.set_screen("main_menu")
            return
        if action == "continue_from_badge":
            # return to the previous screen before the badge popup
            if len(self.state.history) >= 2:
                previous = self.state.history[-2]
            else:
                previous = "world_map"
            self.set_screen(previous)
            return
        if action == "view_badges":
            self.set_screen("progress_complete")
            return
        if self.state.current_screen_id == "letter_island_game" and action in {
            "select_letter_b",
            "select_letter_d",
            "select_letter_p",
            "select_letter_a",
            "repeat_prompt",
            "show_hint",
            "voice_or_speak_mode",
        }:
            self._handle_letter_island_action(action)
            return
        if action == "repeat_instruction_audio" or action == "repeat_instruction":
            return
        if action == "replay_welcome_audio" or action == "replay_main_menu_audio" or action == "replay_instruction_audio":
            return
        if action == "toggle_music" or action == "change_difficulty" or action == "reset_progress":
            return
        if action == "toggle_voice":
            self.state.voice_enabled = not self.state.voice_enabled
            self.voice.set_enabled(self.state.voice_enabled)
            if self.state.voice_enabled:
                self.voice.speak("Voice is on.")
            return
        if self.state.current_screen_id == "progress_complete":
            if action == "next_world":
                try:
                    current = int(self.learner.current_world or 1)
                except Exception:
                    current = 1
                self.learner.current_world = current + 1
                self.learner.save_profile()
                self.set_screen("world_map")
                return
            if action == "practice_again":
                self.set_screen("practice_weak_skills")
                return
        if action == "show_profile" or action == "repeat_prompt" or action == "show_hint" or action == "voice_or_speak_mode":
            if action == "show_hint":
                self.voice.speak(get_feedback("hint")["message"])
            elif action == "repeat_prompt":
                self.voice.speak(self.state.current_task_prompt or get_lumi_speech(self.state.current_screen_id))
            return
        if self.state.current_screen_id == "letter_island_game":
            self._handle_letter_island_action(action)
            return
        if action == "next_activity":
            self.set_screen("word_garden_game")
            return

        if action in {"repeat_bd_prompt", "bd_hint", "answer_B", "answer_D", "next_hint_or_bd_practice", "try_again"}:
            return

    def _handle_letter_island_action(self, action: str) -> None:
        target_letter = self.state.current_task_target or "B"

        if action == "repeat_prompt":
            self.voice.speak(self.state.current_task_prompt or "Find the letter B.")
            return

        if action == "show_hint":
            self.state.current_hint_level += 1
            self.learner.record_hint_usage(self.state.current_hint_level)
            hint_message = get_hint("letter", self.state.current_hint_level, target_letter)
            self.voice.speak(hint_message)
            self.set_screen("letter_mistake_hint")
            return

        if action == "voice_or_speak_mode":
            self.voice.speak("Voice coming soon.")
            return

        card_actions = {
            "select_letter_b": "B",
            "select_letter_d": "D",
            "select_letter_p": "P",
            "select_letter_a": "A",
        }
        selected_letter = card_actions.get(action)
        if selected_letter is None:
            return

        if selected_letter == target_letter:
            stars_earned = calculate_stars(True, self.state.current_hint_level)
            self.learner.update_correct_streak()
            update_score(self.learner, stars_earned)
            self.learner.mark_letter_mastered(target_letter)
                unlocked = check_badge_unlocks(self.learner)
            self.state.current_hint_level = 0
            self.state.bd_confusion_attempts = 0
            self.voice.speak("Great job! This is B.")
                if unlocked:
                    self._handle_badges(unlocked)
                    return
                self.set_screen("letter_correct_feedback")
            return

        self.learner.update_wrong_streak()
        self.learner.record_weak_letter(target_letter)
        if selected_letter == "D":
            self.state.last_mistake_type = "visual_letter_confusion"
            self.state.bd_confusion_attempts += 1
        else:
            self.state.last_mistake_type = "letter_confusion"
        feedback = get_feedback(
            False,
            mistake_type=self.state.last_mistake_type,
            target=target_letter,
            selected=selected_letter,
        )
        self.voice.speak(feedback["message"])
        if self.state.bd_confusion_attempts >= 2:
            self._configure_bd_practice("B")
            self.set_screen("bd_practice")
            return
        self.set_screen("letter_mistake_hint")

    def _speak_for_screen(self, screen_id: str) -> None:
        if not self.state.voice_enabled:
            return

        if screen_id == "welcome":
            self.voice.speak(get_lumi_speech(screen_id))
            return

        if screen_id == "how_to_play":
            self.voice.speak(get_lumi_speech(screen_id))
            return

        if screen_id == "world_map":
            self.voice.speak(get_lumi_speech(screen_id))
            return

        if screen_id == "letter_island_game":
            self.voice.speak(self.state.current_task_prompt or get_lumi_speech(screen_id, self.state.current_task_target))
            return

        if screen_id == "word_garden_game":
            self.voice.speak(self.state.current_task_prompt or "Touch the cat.")
            return

        if screen_id == "sentence_castle_game":
            self.voice.speak("Build the sentence.")
            return

        if screen_id == "sentence_dragging":
            self.voice.speak("Keep building the sentence.")
            return

        if screen_id == "sentence_mistake_hint":
            self.voice.speak(self.state.sentence_feedback_message or "Good try. Start with I.")
            return

        if screen_id == "sentence_correct_feedback":
            self.voice.speak(self.state.sentence_feedback_message or "You built it!")
            return

        if screen_id == "voice_challenge":
            self.voice.speak("Say apple.")
            return

        if screen_id == "listening_state":
            self.voice.speak("I am listening. Say apple.")
            return

        if screen_id == "voice_correct_feedback":
            self.voice.speak(self.state.last_word_feedback_message or "You said apple!")
            return

        if screen_id == "word_correct_feedback":
            self.voice.speak(self.state.last_word_feedback_message or self._word_garden_correct_message())
            return

        if screen_id == "word_mistake_hint":
            self.voice.speak(self.state.last_word_feedback_message or self._word_garden_hint_message())
            return

        if screen_id == "bd_practice":
            target_letter = self.state.bd_practice_target or "B"
            self.voice.speak(f"B has a belly. D has a drum. Find {target_letter}.")
            return

        if screen_id in {"offline_continue"}:
            self.voice.speak(get_lumi_speech(screen_id))
            return

        if screen_id in {"letter_island_game"}:
            self.voice.speak(get_lumi_speech(screen_id))
            return

        if screen_id in {"letter_correct_feedback", "sentence_correct_feedback", "voice_correct_feedback"}:
            self.voice.speak(get_feedback(True)["message"])
            return

        if screen_id in {"letter_mistake_hint"}:
            self.voice.speak(get_feedback("hint")["message"])
            return

        if screen_id == "badge_unlock":
            # announce the badge(s) unlocked, if available
            msg = get_feedback("badge_unlock")["message"]
            if getattr(self.state, "last_unlocked_badges", None):
                names = ", ".join(self.state.last_unlocked_badges)
                msg = f"You unlocked: {names}. " + msg
            self.voice.speak(msg)
            return

        if screen_id == "progress_complete":
            self.voice.speak(get_feedback("level_complete")["message"])
            return

        if screen_id == "teacher_report":
            report = generate_report(self.learner.get_profile())
            self.voice.speak(
                f"{report['child_name']} has {report['stars']} stars and {report['correct_answers']} correct answers."
            )

    def update(self) -> None:
        self.current_screen.update()
        if self.state.current_screen_id == "splash_loading":
            elapsed = pygame.time.get_ticks() - self.state.splash_started_at
            if elapsed >= SPLASH_DURATION_MS:
                self.set_screen("welcome")

    def stop(self) -> None:
        self.voice.stop()

    def draw(self) -> None:
        self.current_screen.draw(self.screen, debug_hitboxes=DEBUG_HITBOXES)
        if self.state.current_screen_id == VOICE_FALLBACK_SCREEN_ID:
            pygame.display.set_caption("Lumi's Word Adventure - Offline Mode")
