"""Bridge so voice/STT modules can duck background music without importing GameEngine."""
from __future__ import annotations

from typing import Any

_manager: Any = None


def bind(manager: Any) -> None:
    global _manager
    _manager = manager


def duck(reason: str) -> None:
    if _manager is not None:
        _manager.duck(reason)


def unduck(reason: str) -> None:
    if _manager is not None:
        _manager.unduck(reason)
