"""Where the squirrels are standing, and how they get somewhere else.

Pure like `battle.py` and `choreography.py` — nothing here imports pygame — so
the walking limits and the rival's wandering can be tested without opening a
window. Everything is in the window version's pixel coordinates.

These numbers are the fun part to retune, like the damage ranges in `moves.py`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# The window is 960 wide and squirrels are drawn by their middle, so the band
# stops short of both edges to keep the widest one (~250px) fully on screen.
WALK_LEFT = 140
WALK_RIGHT = 820

# Squirrels bump into each other rather than overlapping. Because neither can
# cross the other, the player is always the left fighter and the rival the right.
MIN_GAP = 170

# Closer than this and melee connects; further and ranged moves do.
CLOSE_RANGE = 300

# Where they stand at the start of a battle — deliberately further apart than
# CLOSE_RANGE, so the very first turn already poses the question.
PLAYER_START = 250
RIVAL_START = 710


def gap(player_x, rival_x) -> float:
    return abs(player_x - rival_x)


def is_close(player_x, rival_x) -> bool:
    return gap(player_x, rival_x) <= CLOSE_RANGE


def reaches(move, player_x, rival_x) -> bool:
    """Would `move` connect from where these two are standing?"""
    if move.reach == "any":
        return True
    close = is_close(player_x, rival_x)
    return close if move.reach == "melee" else not close


# How fast each one walks, in pixels per second. The rival is slower than the
# player so that chasing it down is winnable.
PLAYER_SPEED = 220.0
RIVAL_SPEED = 90.0


def clamp_player(x, rival_x) -> float:
    """Keep the player on the stage and to the left of the rival."""
    x = max(WALK_LEFT, min(WALK_RIGHT, x))
    return max(WALK_LEFT, min(x, rival_x - MIN_GAP))


def clamp_rival(x, player_x) -> float:
    """Keep the rival on the stage and to the right of the player."""
    x = max(WALK_LEFT, min(WALK_RIGHT, x))
    return min(WALK_RIGHT, max(x, player_x + MIN_GAP))


def walk_player(x, direction, dt_ms, rival_x, speed=PLAYER_SPEED) -> float:
    """Step the player `direction` (-1 left, +1 right) for `dt_ms` milliseconds."""
    return clamp_player(x + direction * speed * (dt_ms / 1000.0), rival_x)


# How long the rival keeps ambling one way before picking a new direction.
WANDER_MIN_MS = 400
WANDER_MAX_MS = 1200


@dataclass(frozen=True)
class Wander:
    """The rival's current whim: which way, and for how much longer."""

    direction: int = 1
    remaining_ms: int = 0


def step_wander(wander, rival_x, player_x, dt_ms, rng=random) -> tuple:
    """Amble the rival along for `dt_ms`. Returns `(new_x, new_wander)`.

    The direction is random rather than tactical, so the rival regularly
    wanders itself out of range of the move it picked. That is the joke.
    """
    direction = wander.direction
    remaining = wander.remaining_ms - dt_ms
    if remaining <= 0:
        direction = rng.choice((-1, 1))
        remaining = rng.randint(WANDER_MIN_MS, WANDER_MAX_MS)

    x = clamp_rival(rival_x + direction * RIVAL_SPEED * (dt_ms / 1000.0), player_x)
    if x == rival_x and dt_ms > 0:
        # Walked into a wall or into the player. Turn around rather than
        # standing there pushing against it for the rest of the stretch.
        direction = -direction
    return x, Wander(direction=direction, remaining_ms=remaining)
