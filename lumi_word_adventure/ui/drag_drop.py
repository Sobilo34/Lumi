"""Drag-and-drop placeholders for future sentence activities."""
from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class DraggableItem:
    label: str
    rect: pygame.Rect
    value: str = ""


@dataclass
class DropZone:
    label: str
    rect: pygame.Rect
    expected_value: str = ""
