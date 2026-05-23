"""Safe JSON loading helpers for Lumi's learning content."""
from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from config import DATA_DIR, PROFILES_DIR


class DataLoadError(RuntimeError):
    """Raised when a content file is missing or malformed."""


def _resolve_path(file_name: str | Path, base_dir: Path) -> Path:
    path = Path(file_name)
    if not path.is_absolute():
        path = base_dir / path
    return path


def load_json_file(file_name: str | Path, base_dir: Path | None = None) -> Any:
    resolved_base = base_dir or DATA_DIR
    path = _resolve_path(file_name, resolved_base)

    if not path.exists():
        raise DataLoadError(f"Missing data file: {path}")

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as error:
        raise DataLoadError(f"Invalid JSON in {path}: {error.msg} (line {error.lineno}, column {error.colno})") from error
    except OSError as error:
        raise DataLoadError(f"Unable to read data file {path}: {error}") from error


def load_letters() -> list[dict[str, Any]]:
    payload = load_json_file("letters.json")
    if not isinstance(payload, list):
        raise DataLoadError("letters.json must contain a JSON array")
    return payload


def load_vocabulary() -> list[dict[str, Any]]:
    payload = load_json_file("vocabulary.json")
    if not isinstance(payload, list):
        raise DataLoadError("vocabulary.json must contain a JSON array")
    return payload


def load_sentences() -> list[dict[str, Any]]:
    payload = load_json_file("sentences.json")
    if not isinstance(payload, list):
        raise DataLoadError("sentences.json must contain a JSON array")
    return payload


def load_default_profile() -> dict[str, Any]:
    payload = load_json_file("default_profile.json")
    if not isinstance(payload, dict):
        raise DataLoadError("default_profile.json must contain a JSON object")
    return payload


def load_profile(profile_name: str) -> dict[str, Any]:
    payload = load_json_file(profile_name, base_dir=PROFILES_DIR)
    if not isinstance(payload, dict):
        raise DataLoadError(f"{profile_name} must contain a JSON object")
    return payload