"""Where the squirrels are standing, and how they get somewhere else.

Pure like `battle.py` and `choreography.py` — nothing here imports pygame — so
the walking limits and the rival's wandering can be tested without opening a
window. Everything is in the window version's pixel coordinates.

These numbers are the fun part to retune, like the damage ranges in `moves.py`.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace

# The world is three windows wide. The window stays 960; the camera scrolls.
WINDOW_WIDTH = 960
WORLD_WIDTH = 2880

# Squirrels are drawn by their middle, so the walkable band stops short of both
# world edges to keep the widest one (~250px) from hanging off.
WALK_LEFT = 140
WALK_RIGHT = WORLD_WIDTH - 140

# How close two squirrels at similar heights may get. They can pass each other
# when one is up a tree, so neither is permanently the left or the right fighter.
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

# Trunks across the world. The spacing is what a jump has to clear, so it is
# named rather than implied — see JUMP_SPEED and the reach table in the spec.
#
# 230 divides the 460px gap the fighters start at, so both of them begin at a
# trunk. At 290 the player would start at a tree and the rival would not.
TREE_SPACING = 230
TREES = tuple(range(290, 2591, TREE_SPACING))

# How near a trunk you have to be to start climbing it.
CLIMB_REACH = 60

# How near you have to pass to grab a trunk in mid-air. Tighter than CLIMB_REACH
# because snatching a branch as you fly past is a finer thing than standing next
# to a tree and starting up it — and because a generous catch radius quietly adds
# itself to every jump's reach, which is what broke the tree-to-tree rule the
# first time these numbers were picked.
CATCH_REACH = 20

# How high a squirrel can climb. NOT a tuning knob — it is set by the stage
# ceiling, and the thing that has to fit under it is the JUMP APEX, not this.
#
# A jump rises JUMP_SPEED^2 / 2*GRAVITY = 76px above wherever it launched, so the
# highest a squirrel ever gets is MAX_CLIMB + 76 = 240, which is exactly where the
# tallest drawing's head meets the top of the stage. This was 240 while climbing
# was the only way up; jumping quietly went 76px higher and clipped heads off.
# `test_a_jumping_squirrel_still_fits_on_the_stage` guards it.
MAX_CLIMB = 164

# Height difference above which two squirrels stop bumping into each other, so
# one can walk underneath another that is up a tree.
CLIMB_CLEARANCE = 60

CLIMB_SPEED = 160.0
RIVAL_CLIMB_SPEED = 70.0

# How long one of the rival's vertical whims lasts.
CLIMB_MIN_MS = 300
CLIMB_MAX_MS = 900

# How long between the rival considering a jump.
JUMP_MIN_MS = 700
JUMP_MAX_MS = 2000

# Jumping. These are coupled to TREE_SPACING and CATCH_REACH: a jump from the ground
# lands 192px along and a jump from MAX_CLIMB catches the trunk 230px along —
# so you can only leap tree to tree if you launch from up a tree.
#
# CATCH_REACH is part of this arithmetic, not separate from it: a catch radius
# adds itself to every jump's effective reach, and at 60 a ground jump grabbed
# the next trunk and broke the rule entirely. Changing any of the four means
# rechecking the other three.
# `test_a_ground_jump_does_not_reach_the_next_tree` guards the rule.
JUMP_SPEED = 380.0
GRAVITY = 950.0
AIR_SPEED = 240.0


def gap(player_x, player_y, rival_x, rival_y) -> float:
    """Straight-line distance, so height counts the same as walking does."""
    return math.hypot(player_x - rival_x, player_y - rival_y)


def band(player_x, player_y, rival_x, rival_y) -> str:
    """Which of the three range bands these two are standing in."""
    distance = gap(player_x, player_y, rival_x, rival_y)
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


def reaches(move, player_x, player_y, rival_x, rival_y) -> bool:
    """Would `move` connect from where these two are standing?"""
    if move.reach == "any":
        return True
    here = band(player_x, player_y, rival_x, rival_y)
    if move.reach == "melee":
        return here == CLOSE
    return here == MID


def clamp_walk(x, my_y, other_x, other_y) -> float:
    """Keep a walking squirrel in the world, inside the leash, and out of the other.

    Side-agnostic. Squirrels used to be unable to pass each other, so the player
    was permanently the left fighter — but now that one can walk underneath
    another that is up a tree, either may end up on either side.
    """
    x = max(WALK_LEFT, min(WALK_RIGHT, x))
    x = max(other_x - LEASH, min(other_x + LEASH, x))
    if abs(my_y - other_y) < CLIMB_CLEARANCE and abs(x - other_x) < MIN_GAP:
        # Same sort of height, so they bump. `shove` already knows how to push
        # something clear without letting it fall out of the world, which is the
        # one case a plain "step back MIN_GAP" gets wrong next to a wall.
        x = shove(x, other_x)
    return x


def walk(x, my_y, direction, dt_ms, other_x, other_y, speed=PLAYER_SPEED) -> float:
    """Step `direction` (-1 left, +1 right) for `dt_ms` milliseconds."""
    return clamp_walk(x + direction * speed * (dt_ms / 1000.0), my_y, other_x, other_y)


def shove(grounded_x, lander_x) -> float:
    """Where a squirrel ends up when something climbs down onto it.

    It goes to whichever side of the lander it is already on, unless that would
    put it outside the world — the walkable world is 2600px against a 170px
    MIN_GAP, so the other side always has room.
    """
    if grounded_x <= lander_x:
        near, far = lander_x - MIN_GAP, lander_x + MIN_GAP
    else:
        near, far = lander_x + MIN_GAP, lander_x - MIN_GAP
    if WALK_LEFT <= near <= WALK_RIGHT:
        return near
    return max(WALK_LEFT, min(WALK_RIGHT, far))


def resolve_overlap(player_x, player_y, rival_x, rival_y) -> tuple:
    """Sort out two squirrels that have ended up in the same place.

    Returns the four coordinates after any shove or blocked descent. Only
    vertical movement can create this — `clamp_walk` already stops a walking
    squirrel from causing it.
    """
    if (abs(player_y - rival_y) >= CLIMB_CLEARANCE
            or abs(player_x - rival_x) >= MIN_GAP):
        return player_x, player_y, rival_x, rival_y

    # Whoever is nearer the ground is the one in the way.
    if player_y <= rival_y:
        if player_y > 0:
            # Both up a trunk. Shoving one sideways would leave it gripping thin
            # air, so the higher one stops instead.
            return player_x, player_y, rival_x, player_y + CLIMB_CLEARANCE
        return shove(player_x, rival_x), player_y, rival_x, rival_y
    if rival_y > 0:
        return player_x, rival_y + CLIMB_CLEARANCE, rival_x, rival_y
    return player_x, player_y, shove(rival_x, player_x), rival_y


def tree_near(x, reach=CLIMB_REACH):
    """The trunk within `reach` of `x`, or None."""
    for trunk in TREES:
        if abs(x - trunk) <= reach:
            return trunk
    return None


def climb(y, direction, dt_ms, speed=CLIMB_SPEED) -> float:
    """Move up (+1) or down (-1) a trunk, stopping at the ground and the ceiling."""
    return max(0.0, min(MAX_CLIMB, y + direction * speed * (dt_ms / 1000.0)))


@dataclass(frozen=True)
class Flight:
    """Whether a squirrel is in the air, and how fast it is rising."""

    airborne: bool = False
    vy: float = 0.0


def launch() -> Flight:
    """Push off. Gravity takes over from here until something is caught."""
    return Flight(airborne=True, vy=JUMP_SPEED)


def step_flight(flight, x, y, direction, dt_ms, other_x, other_y) -> tuple:
    """Advance a jump by `dt_ms`. Returns `(x, y, flight)`.

    Gravity only ever applies to a squirrel that jumped — on a trunk it is
    gripping, and stays put. So this is a no-op for anyone not airborne.
    """
    if not flight.airborne:
        return x, y, flight

    seconds = dt_ms / 1000.0
    vy = flight.vy - GRAVITY * seconds
    y = y + vy * seconds
    x = clamp_walk(x + direction * AIR_SPEED * seconds, y, other_x, other_y)

    if y <= 0:
        return x, 0.0, Flight()
    if vy < 0 and tree_near(x, CATCH_REACH) is not None:
        # Caught a trunk on the way down. Only when descending: on the way up a
        # squirrel is still next to the tree it just left, and would re-grab it
        # instantly and never get anywhere.
        return x, y, Flight()
    return x, y, Flight(airborne=True, vy=vy)


@dataclass(frozen=True)
class Wander:
    """The rival's current whim: which way along, which way up, and for how long."""

    direction: int = 1
    remaining_ms: int = 0
    climb_direction: int = 0        # -1 down, 0 staying put, +1 up
    climb_remaining_ms: int = 0
    jump_remaining_ms: int = 0


def step_wander(wander, rival_x, rival_y, player_x, player_y, dt_ms, rng=random) -> tuple:
    """Amble the rival along and up for `dt_ms`. Returns `(x, y, wander)`.

    Both whims are random rather than tactical, so the rival regularly strands
    itself halfway up a tree with nothing in range. That is the joke.
    """
    direction = wander.direction
    remaining = wander.remaining_ms - dt_ms
    if remaining <= 0:
        direction = rng.choice((-1, 1))
        remaining = rng.randint(WANDER_MIN_MS, WANDER_MAX_MS)

    climb_direction = wander.climb_direction
    climb_remaining = wander.climb_remaining_ms - dt_ms
    if climb_remaining <= 0:
        # Weighted towards *going down*, which is not the same as being weighted
        # towards 0. This used to be (-1, 0, 0, 1), which averages zero: height
        # became an aimless walk between the ground and the treetop, and that
        # sits at every height equally. The rival clung to a trunk 71% of the
        # fight — and it can't walk while it's off the ground, so the whole
        # fight stopped moving. `test_the_rival_does_not_live_up_a_tree` guards
        # the mean staying negative.
        climb_direction = rng.choice((-1, -1, -1, -1, -1, -1, 0, 1))
        climb_remaining = rng.randint(CLIMB_MIN_MS, CLIMB_MAX_MS)

    y = rival_y
    if tree_near(rival_x) is not None or rival_y > 0:
        y = climb(rival_y, climb_direction, dt_ms, RIVAL_CLIMB_SPEED)

    x = rival_x
    if y <= 0:
        # Only a squirrel with its feet on the ground ambles sideways; off the
        # ground it is gripping a trunk.
        x = clamp_walk(rival_x + direction * RIVAL_SPEED * (dt_ms / 1000.0),
                       y, player_x, player_y)
        if x == rival_x and dt_ms > 0:
            # Walked into a wall or into the player. Turn around rather than
            # standing there pushing against it for the rest of the stretch.
            direction = -direction
    return x, y, Wander(direction, remaining, climb_direction, climb_remaining)


def step_rival(wander, flight, rival_x, rival_y, player_x, player_y, dt_ms, rng=random):
    """One frame of everything the rival does. Returns `(x, y, wander, flight)`.

    A jump takes priority: while it is in the air nothing else applies, because
    it is neither walking nor gripping a trunk.
    """
    if flight.airborne:
        x, y, flight = step_flight(
            flight, rival_x, rival_y, wander.direction, dt_ms, player_x, player_y)
        return x, y, wander, flight

    jump_remaining = wander.jump_remaining_ms - dt_ms
    if jump_remaining <= 0:
        jump_remaining = rng.randint(JUMP_MIN_MS, JUMP_MAX_MS)
        # Only worth jumping from up a trunk; a hop off the ground goes nowhere.
        if rival_y > 0 and rng.choice((True, False)):
            wander = replace(wander, jump_remaining_ms=jump_remaining)
            return rival_x, rival_y, wander, launch()

    x, y, wander = step_wander(
        wander, rival_x, rival_y, player_x, player_y, dt_ms, rng=rng)
    return x, y, replace(wander, jump_remaining_ms=jump_remaining), flight
