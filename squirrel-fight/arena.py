"""Where the squirrels are standing, and how they get somewhere else.

Pure like `battle.py` and `choreography.py` — nothing here imports pygame — so
the walking limits and the rival's wandering can be tested without opening a
window. Everything is in the window version's pixel coordinates.

These numbers are the fun part to retune, like the damage ranges in `moves.py`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# The world is three windows wide. The window stays 960; the camera scrolls.
WINDOW_WIDTH = 960
WORLD_WIDTH = 2880

# Squirrels are drawn by their middle, so the walkable band stops short of both
# world edges to keep the widest one (~250px) from hanging off.
WALK_LEFT = 140
WALK_RIGHT = WORLD_WIDTH - 140

# Squirrels bump into each other rather than overlapping. Because neither can
# cross the other, the player is always the left fighter and the rival the right.
MIN_GAP = 170

# Neither squirrel may get further than this from the other. At this gap each one
# sits 350px from the centre of the screen plus ~125px of sprite — just inside the
# 480px half-window — so it is exactly "as far apart as they can get while both
# stay fully visible". It binds BOTH of them: leashing only the wandering rival
# would let the player walk to the world's edge with nothing pulling it after them.
LEASH = 700

# The three range bands. Melee lands inside CLOSE_RANGE, ranged lands between
# CLOSE_RANGE and LONG_RANGE, and past LONG_RANGE nothing lands at all — so
# retreating has a cost instead of being a free way to stay safe.
CLOSE_RANGE = 300
LONG_RANGE = 550

CLOSE = "close"
MID = "mid"
FAR = "far"

# World centre ± 230. That keeps today's 460 opening gap, and puts the camera at
# 960 — which lands the two squirrels on screen x250 and x710, the exact marks
# they stood on before the world got wide. The game opens looking unchanged.
PLAYER_START = 1210
RIVAL_START = 1670

# How fast each one walks, in pixels per second. The rival is slower than the
# player so that chasing it down is winnable.
PLAYER_SPEED = 220.0
RIVAL_SPEED = 90.0

# How long the rival keeps ambling one way before picking a new direction.
WANDER_MIN_MS = 400
WANDER_MAX_MS = 1200


def gap(player_x, rival_x) -> float:
    return abs(player_x - rival_x)


def band(player_x, rival_x) -> str:
    """Which of the three range bands these two are standing in."""
    distance = gap(player_x, rival_x)
    if distance <= CLOSE_RANGE:
        return CLOSE
    if distance <= LONG_RANGE:
        return MID
    return FAR


def camera_x(player_x, rival_x) -> float:
    """The left edge of the view: centred between the fighters, inside the world.

    Deliberately stateless — recomputed every frame rather than stored and eased.
    The squirrels already move smoothly, so the camera does too, and there is no
    scroll position that can drift out of step with where they actually are.
    """
    middle = (player_x + rival_x) / 2.0
    return max(0.0, min(WORLD_WIDTH - WINDOW_WIDTH, middle - WINDOW_WIDTH / 2.0))


def reaches(move, player_x, rival_x) -> bool:
    """Would `move` connect from where these two are standing?"""
    if move.reach == "any":
        return True
    here = band(player_x, rival_x)
    if move.reach == "melee":
        return here == CLOSE
    return here == MID


def clamp_player(x, rival_x) -> float:
    """Keep the player on the stage, left of the rival, and inside the leash."""
    low = max(WALK_LEFT, rival_x - LEASH)
    high = min(WALK_RIGHT - MIN_GAP, rival_x - MIN_GAP)
    return max(low, min(high, x))


def clamp_rival(x, player_x) -> float:
    """Keep the rival on the stage, right of the player, and inside the leash."""
    low = max(WALK_LEFT + MIN_GAP, player_x + MIN_GAP)
    high = min(WALK_RIGHT, player_x + LEASH)
    return max(low, min(high, x))


def walk_player(x, direction, dt_ms, rival_x, speed=PLAYER_SPEED) -> float:
    """Step the player `direction` (-1 left, +1 right) for `dt_ms` milliseconds."""
    return clamp_player(x + direction * speed * (dt_ms / 1000.0), rival_x)


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
