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
