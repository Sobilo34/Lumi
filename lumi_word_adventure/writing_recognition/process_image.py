"""OpenCV + CNN handwriting recognition (lazy-loaded model)."""
from __future__ import annotations

import math
import os
from pathlib import Path

import cv2
import numpy as np

from writing_recognition.hints import close_word_matches, disambiguate_letter, index_to_letter, letter_hints, refine_with_expected_letter, word_hints

_PACKAGE_DIR = Path(__file__).resolve().parent
MODEL_PATH = _PACKAGE_DIR / "cnn_model" / "letter_classifier.h5"
FALLBACK_MODEL_PATH = _PACKAGE_DIR / "cnn_model" / "digit_classifier.h5"

_model = None
NUM_CLASSES = 26
LETTER_MODEL = True
_load_error: str | None = None


def recognition_available() -> bool:
    return _ensure_model() is not None


def _ensure_model():
    global _model, NUM_CLASSES, LETTER_MODEL, _load_error
    if _model is not None:
        return _model
    if _load_error is not None:
        return None
    try:
        from tf_keras.models import load_model
    except ImportError as exc:
        _load_error = str(exc)
        return None
    try:
        if MODEL_PATH.is_file():
            _model = load_model(str(MODEL_PATH))
            NUM_CLASSES = 26
            LETTER_MODEL = True
        elif FALLBACK_MODEL_PATH.is_file():
            _model = load_model(str(FALLBACK_MODEL_PATH))
            NUM_CLASSES = 10
            LETTER_MODEL = False
        else:
            _load_error = "No handwriting model found."
            return None
    except Exception as exc:  # pragma: no cover - runtime / TF errors
        _load_error = str(exc)
        return None
    return _model


def image_refiner(gray):
    org_size = 22
    img_size = 28
    rows, cols = gray.shape

    if rows > cols:
        factor = org_size / rows
        rows = org_size
        cols = int(round(cols * factor))
    else:
        factor = org_size / cols
        cols = org_size
        rows = int(round(rows * factor))
    gray = cv2.resize(gray, (cols, rows))

    cols_padding = (
        int(math.ceil((img_size - cols) / 2.0)),
        int(math.floor((img_size - cols) / 2.0)),
    )
    rows_padding = (
        int(math.ceil((img_size - rows) / 2.0)),
        int(math.floor((img_size - rows) / 2.0)),
    )
    return np.pad(gray, (rows_padding, cols_padding), mode="constant")


def prepare_for_model(gray):
    prepared = image_refiner(gray)
    if LETTER_MODEL:
        prepared = cv2.rotate(prepared, cv2.ROTATE_90_CLOCKWISE)
    return prepared


def predict_letter(img):
    model = _ensure_model()
    if model is None:
        return "?", 0.0, [("?", 0.0)]

    prepared = prepare_for_model(img)
    test_image = prepared.reshape(-1, 28, 28, 1).astype("float32")
    probabilities = model.predict(test_image, verbose=0)[0]
    top_indices = np.argsort(probabilities)[::-1][:5]

    top_predictions = []
    for index in top_indices:
        if index < NUM_CLASSES:
            if NUM_CLASSES == 26:
                label = index_to_letter(int(index))
            else:
                label = str(int(index))
            top_predictions.append((label, float(probabilities[index])))

    best_letter, best_confidence = top_predictions[0]
    return best_letter, best_confidence, top_predictions


def put_label(image, label, x, y, hint=None):
    font = cv2.FONT_HERSHEY_SIMPLEX
    label_x = int(x) - 10
    label_y = int(y) + 10
    cv2.rectangle(
        image,
        (label_x, label_y + 5),
        (label_x + 35, label_y - 35),
        (0, 255, 0),
        -1,
    )
    cv2.putText(
        image,
        str(label),
        (label_x, label_y),
        font,
        1.5,
        (255, 0, 0),
        1,
        cv2.LINE_AA,
    )
    if hint:
        cv2.putText(
            image,
            hint[:28],
            (label_x, label_y + 35),
            font,
            0.45,
            (0, 0, 200),
            1,
            cv2.LINE_AA,
        )
    return image


def extract_letter_regions(path, expected_letter: str = ""):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return [], None

    img_org = cv2.imread(path)
    _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w <= 10 or h <= 10:
            continue

        roi = thresh[y : y + h, x : x + w]

        letter, confidence, top_predictions = predict_letter(roi)
        letter, confidence, top_predictions, shape_note = disambiguate_letter(
            roi, letter, confidence, top_predictions
        )
        if expected_letter:
            letter, confidence, top_predictions, target_note = refine_with_expected_letter(
                roi,
                letter,
                confidence,
                top_predictions,
                expected_letter,
            )
            if target_note and not shape_note:
                shape_note = target_note
        hint = letter_hints(top_predictions, shape_note=shape_note)
        regions.append(
            {
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "letter": letter,
                "confidence": confidence,
                "top_predictions": top_predictions,
                "hint": hint,
            }
        )

    regions.sort(key=lambda region: region["x"])
    return regions, img_org


def build_letter_board(regions, img_org):
    board = img_org.copy()
    letter_results = []

    for region in regions:
        cv2.rectangle(
            board,
            (region["x"], region["y"]),
            (region["x"] + region["w"], region["y"] + region["h"]),
            (0, 255, 0),
            2,
        )
        center_x = region["x"] + region["w"] // 2
        center_y = region["y"] + region["h"] // 2
        board = put_label(board, region["letter"], center_x, center_y, region["hint"])
        letter_results.append(
            {
                "letter": region["letter"],
                "confidence": region["confidence"],
                "hint": region["hint"],
            }
        )

    return board, letter_results


def recognize_letters(path, single=False, expected_letter: str = ""):
    regions, img_org = extract_letter_regions(path, expected_letter=expected_letter)
    if img_org is None:
        return np.zeros((640, 640, 3), dtype=np.uint8), []

    if single and regions:
        regions = [max(regions, key=lambda region: region["w"] * region["h"])]

    board, letter_results = build_letter_board(regions, img_org)
    return board, letter_results


def recognize_word(path, expected_word: str = ""):
    regions, _ = extract_letter_regions(path)
    if not regions:
        return "", "Draw a word with clear spacing, then click Complete."

    word = "".join(region["letter"] for region in regions)
    target = str(expected_word or "").strip().lower()
    if target and close_word_matches(target, word):
        word = target
    hint = word_hints(word)
    return word, hint


def get_output_images(path, mode="letters", complete_word=False):
    letter_board, letter_results = recognize_letters(path)
    words = []
    word_hint = None

    if mode == "words" and complete_word:
        word, word_hint = recognize_word(path)
        if word:
            words = [word]

    letter_hints_list = [result["hint"] for result in letter_results if result["hint"]]
    return letter_board, letter_hints_list, words, word_hint
