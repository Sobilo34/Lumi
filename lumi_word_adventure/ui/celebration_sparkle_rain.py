"""Falling sparkle/stars for correct-answer celebrations (tap + writing popups)."""
from __future__ import annotations

import math
import random

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import draw_sparkle

_SPARKLE_COUNT = 150  # Much denser for Champions League effect
_STAR_COLORS: tuple[tuple[int, int, int], ...] = (
    # Golds and yellows
    (255, 215, 0),
    (255, 244, 140),
    (255, 220, 120),
    # Silvers and whites
    (255, 255, 255),
    (220, 220, 255),
    (192, 192, 220),
    # Blues
    (100, 149, 237),
    (65, 105, 225),
    (180, 230, 255),
    # Reds and pinks
    (255, 105, 180),
    (255, 182, 193),
    (255, 99, 71),
    # Greens
    (144, 238, 144),
    (50, 205, 50),
    # Purples
    (186, 85, 211),
    (147, 112, 219),
    # Orange
    (255, 165, 0),
    (255, 140, 0),
)


def _particle_rng(index: int) -> random.Random:
    return random.Random(index * 92821 + 17)


def _spawn_particles() -> list[dict]:
    particles: list[dict] = []
    for index in range(_SPARKLE_COUNT):
        rng = _particle_rng(index)
        # Stagger spawn times more for continuous rain effect
        particles.append(
            {
                "x_ratio": rng.uniform(0.0, 1.0),  # Full width coverage
                "start_delay_ms": rng.randint(0, 800),  # Longer stagger
                "speed": rng.uniform(180.0, 400.0),  # Faster falling
                "wobble_amp": rng.uniform(8.0, 25.0),  # More sway
                "wobble_freq": rng.uniform(0.003, 0.012),
                "wobble_phase": rng.uniform(0.0, math.tau),
                "rotation_speed": rng.uniform(-0.01, 0.01),  # Spinning confetti
                "bubble_radius": rng.randint(6, 14),  # Smaller confetti pieces
                "star_size": rng.randint(3, 8),
                "color": _STAR_COLORS[index % len(_STAR_COLORS)],
                "shape": rng.choice(["star", "square", "circle", "diamond"]),
                "flutter_amp": rng.uniform(0.5, 1.5),  # Flutter intensity
            }
        )
    return particles


_PARTICLES = _spawn_particles()


def _fade_alpha(elapsed_ms: int, duration_ms: int) -> int:
    if elapsed_ms < 0:
        return 0
    if duration_ms <= 0:
        return 0
    if elapsed_ms <= 150:
        return int(255 * (elapsed_ms / 150.0))
    remaining = duration_ms - elapsed_ms
    if remaining <= 300:
        return max(0, int(255 * (remaining / 300.0)))
    return 255


def _draw_confetti_shape(
    surface: pygame.Surface,
    x: int,
    y: int,
    size: int,
    color: tuple[int, int, int],
    shape: str,
    rotation: float,
    alpha: int,
) -> None:
    """Draw various confetti shapes with rotation effect."""
    if alpha <= 0:
        return
    
    # Create surface for the shape
    surf_size = size * 4
    shape_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    center = surf_size // 2
    
    # Apply rotation scaling to simulate 3D tumbling
    scale_x = abs(math.cos(rotation))
    scale_y = abs(math.sin(rotation * 0.7 + 0.5))
    
    if shape == "star":
        draw_sparkle(shape_surf, center, center, size=size, color=color)
    elif shape == "square":
        # Rectangular confetti piece
        rect_w = max(2, int(size * 1.5 * max(0.3, scale_x)))
        rect_h = max(2, int(size * max(0.3, scale_y)))
        rect = pygame.Rect(center - rect_w // 2, center - rect_h // 2, rect_w, rect_h)
        pygame.draw.rect(shape_surf, (*color, alpha), rect)
    elif shape == "circle":
        radius = max(2, int(size * 0.7))
        pygame.draw.circle(shape_surf, (*color, alpha), (center, center), radius)
    elif shape == "diamond":
        # Diamond/rhombus shape
        half_w = max(2, int(size * max(0.3, scale_x)))
        half_h = max(2, int(size * 1.2 * max(0.3, scale_y)))
        points = [
            (center, center - half_h),
            (center + half_w, center),
            (center, center + half_h),
            (center - half_w, center),
        ]
        pygame.draw.polygon(shape_surf, (*color, alpha), points)
    
    if shape == "star":
        shape_surf.set_alpha(alpha)
    
    surface.blit(shape_surf, (x - center, y - center))


def draw_celebration_sparkle_rain(
    screen: pygame.Surface,
    *,
    elapsed_ms: int,
    duration_ms: int = 2500,  # Longer duration for full effect
) -> None:
    """Draw Champions League-style confetti rain celebration."""
    if elapsed_ms < 0 or elapsed_ms > duration_ms + 300:
        return

    master_alpha = _fade_alpha(elapsed_ms, duration_ms)
    if master_alpha <= 0:
        return

    width = SCREEN_WIDTH
    height = SCREEN_HEIGHT

    for index, particle in enumerate(_PARTICLES):
        delay = int(particle["start_delay_ms"])
        local_ms = elapsed_ms - delay
        if local_ms < 0:
            continue

        # Base position
        x_base = int(float(particle["x_ratio"]) * width)
        
        # Wobble side to side
        wobble = particle["wobble_amp"] * math.sin(
            local_ms * particle["wobble_freq"] + particle["wobble_phase"]
        )
        
        # Flutter effect - slight horizontal drift
        flutter = particle["flutter_amp"] * math.sin(local_ms * 0.002 + index)
        
        x = int(x_base + wobble + flutter * 10)
        
        # Fall from above screen
        y = int(-30 + (local_ms / 1000.0) * particle["speed"])
        
        if y > height + 30:
            continue

        size = int(particle["star_size"])
        color = tuple(particle["color"])
        shape = str(particle["shape"])
        
        # Calculate rotation for tumbling effect
        rotation = local_ms * particle["rotation_speed"] + particle["wobble_phase"]
        
        # Slight alpha variation for depth
        depth_alpha = int(master_alpha * random.Random(index).uniform(0.7, 1.0))
        
        # Add subtle glow behind bright pieces
        if index % 5 == 0:
            glow_surf = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
            glow_center = size * 3
            glow_alpha = int(depth_alpha * 0.15)
            pygame.draw.circle(
                glow_surf,
                (*color, glow_alpha),
                (glow_center, glow_center),
                size * 2,
            )
            screen.blit(glow_surf, (x - glow_center, y - glow_center))
        
        _draw_confetti_shape(
            screen, x, y, size, color, shape, rotation, depth_alpha
        )


# Keep backwards compatibility with any existing calls
__all__ = ["draw_celebration_sparkle_rain"]
