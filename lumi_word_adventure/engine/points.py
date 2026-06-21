"""Lumi point system — a warm, motivating reward economy for ages 2-4.

Design goals (studied against the game loop):
- Every correct answer always feels rewarding (base points), so kids never feel
  punished, while still rewarding mastery: more points for first-try / no-hint
  answers (which earn 3 stars) and for keeping a streak going.
- Bigger milestones (badges, finishing a world) give satisfying point bursts.
- Points roll up into friendly *ranks* with a visible progress bar, giving a
  long-term goal beyond a single session.

All values are intentionally small, round numbers so a parent/teacher can reason
about them and a toddler sees the number climb often.
"""
from __future__ import annotations

# --- award amounts ---------------------------------------------------------
POINTS_BASE_CORRECT = 10        # any correct answer
POINTS_PER_STAR = 5             # 1 star=+5 ... 3 stars=+15 on top of base
STREAK_BONUS_PER = 2            # per consecutive correct answer
STREAK_BONUS_CAP = 5            # capped so it stays gentle (max +10)
POINTS_PER_BADGE = 50           # each badge unlocked
POINTS_PER_WORLD = 100          # finishing a world

# --- friendly ranks (threshold, name, emoji) -------------------------------
RANK_TIERS: tuple[tuple[int, str, str], ...] = (
    (0, "Little Sprout", "🌱"),
    (100, "Bright Star", "⭐"),
    (250, "Happy Explorer", "🧭"),
    (500, "Word Wizard", "🪄"),
    (1000, "Reading Hero", "🦸"),
    (2000, "Lumi Champion", "🏆"),
)


def points_for_correct(stars_earned: int, streak: int = 0) -> int:
    """Points for a single correct answer given stars and the current streak.

    ``streak`` is the number of correct answers in a row *including* this one.
    """
    stars = max(0, int(stars_earned))
    streak_steps = min(STREAK_BONUS_CAP, max(0, int(streak)))
    return POINTS_BASE_CORRECT + stars * POINTS_PER_STAR + streak_steps * STREAK_BONUS_PER


def rank_for_points(points: int) -> tuple[str, str]:
    """Return (rank_name, emoji) for a point total."""
    points = max(0, int(points))
    current = RANK_TIERS[0]
    for tier in RANK_TIERS:
        if points >= tier[0]:
            current = tier
        else:
            break
    return current[1], current[2]


def rank_progress(points: int) -> dict[str, object]:
    """Progress info toward the next rank (for a progress bar / page)."""
    points = max(0, int(points))
    current = RANK_TIERS[0]
    nxt: tuple[int, str, str] | None = None
    for index, tier in enumerate(RANK_TIERS):
        if points >= tier[0]:
            current = tier
            nxt = RANK_TIERS[index + 1] if index + 1 < len(RANK_TIERS) else None
        else:
            break

    if nxt is None:
        return {
            "rank_name": current[1],
            "rank_emoji": current[2],
            "next_rank_name": "",
            "points_into_rank": points - current[0],
            "points_for_next": 0,
            "points_to_next": 0,
            "progress": 1.0,
            "is_max_rank": True,
        }

    span = max(1, nxt[0] - current[0])
    into = points - current[0]
    return {
        "rank_name": current[1],
        "rank_emoji": current[2],
        "next_rank_name": nxt[1],
        "points_into_rank": into,
        "points_for_next": span,
        "points_to_next": max(0, nxt[0] - points),
        "progress": max(0.0, min(1.0, into / span)),
        "is_max_rank": False,
    }
