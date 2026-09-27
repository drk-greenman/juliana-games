# Squirrel Movement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the player walk their squirrel around the stage in the window version, with each move only reaching at the right distance.

**Architecture:** A new pure `arena.py` owns positions, walking limits and the rival's random wander, mirroring how `battle.py` and `choreography.py` stay free of pygame. `battle.py` learns one new thing — whether the fighters are close — and whiffs attacks used at the wrong distance. `visual_game.py` keeps the live positions and does the input and drawing. The terminal `game.py` is untouched.

**Tech Stack:** Python 3.9 (system interpreter, no venv), pygame-ce, pytest. Note that `X | Y` type annotations need `from __future__ import annotations`, which every module here already has.

**Spec:** `docs/superpowers/specs/2026-09-26-squirrel-movement-design.md`

---

## File Structure

| File | Responsibility |
| --- | --- |
| `squirrel-fight/moves.py` | **Modify.** Add a `reach` field to `Move` and set it on all 12 moves. Data only. |
| `squirrel-fight/test_moves.py` | **Create.** Guards the reach data against typos. |
| `squirrel-fight/arena.py` | **Create.** Pure. Walking band, gap, close/far, clamping, rival wander. No pygame. |
| `squirrel-fight/test_arena.py` | **Create.** Tests for the above. |
| `squirrel-fight/battle.py` | **Modify.** `resolve_turn()` takes `close` and whiffs out-of-range attacks. |
| `squirrel-fight/test_battle.py` | **Modify.** New range cases; existing tests must pass untouched. |
| `squirrel-fight/choreography.py` | **Modify.** A whiff gets its own caption instead of "shrugs it off". |
| `squirrel-fight/test_choreography.py` | **Modify.** New whiff caption test. |
| `squirrel-fight/visual_game.py` | **Modify.** Live positions, arrow-key walking, rival wander, out-of-range button dimming. |
| `squirrel-fight/README.md` | **Modify.** Document the controls and that walking is window-only. |

**Key design note:** `battle.py` takes a **boolean `close`**, not a pixel gap. The spec says "takes the gap"; a boolean is the same rule with no stage geometry leaking into the rules module. `arena.py` owns the pixels and decides what counts as close.

All commands below are run from the repo root, `/Users/kgreenman/git/juliana-games`.

---

## Task 1: Give every move a reach

**Files:**
- Modify: `squirrel-fight/moves.py`
- Test: `squirrel-fight/test_moves.py` (create)

- [ ] **Step 1: Write the failing test**

Create `squirrel-fight/test_moves.py`:

```python
from moves import MOVES


def move_named(name):
    for move in MOVES:
        if move.name == name:
            return move
    raise AssertionError("no move called {}".format(name))


def test_melee_moves_are_marked_melee():
    for name in ("Tail Smack", "Cheek Barrel", "Scratch", "Steal"):
        assert move_named(name).reach == "melee"


def test_ranged_moves_are_marked_ranged():
    for name in ("Acorn Blast", "Chirp", "Chirp Insanely"):
        assert move_named(name).reach == "ranged"


def test_defenses_and_heals_work_at_any_distance():
    for move in MOVES:
        if move.kind != "attack":
            assert move.reach == "any"


def test_every_attack_picks_a_side():
    for move in MOVES:
        if move.kind == "attack":
            assert move.reach in ("melee", "ranged")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_moves.py -v`
Expected: FAIL with `AttributeError: 'Move' object has no attribute 'reach'`

- [ ] **Step 3: Add the field and the data**

In `squirrel-fight/moves.py`, add `reach` as the last field of the `Move` dataclass (it must come after the other defaulted fields):

```python
@dataclass(frozen=True)
class Move:
    name: str
    kind: Literal["attack", "defense", "heal"]
    description: str
    dmg_range: tuple[int, int] | None = None
    lifesteal: bool = False
    dodge_chance: float | None = None
    block_reduction: float | None = None
    block_flat: int | None = None
    heal_range: tuple[int, int] | None = None
    # How close you have to be for this to connect. Defaults to "any" so a new
    # move without a reach still works everywhere rather than silently whiffing.
    reach: Literal["melee", "ranged", "any"] = "any"
```

Then set `reach` on the seven attacks. Replace the seven attack entries in `MOVES` with:

```python
    Move("Tail Smack", "attack", "A reliable melee whack.", dmg_range=(10, 13), reach="melee"),
    Move("Cheek Barrel", "attack", "A barreling tackle, cheeks first.", dmg_range=(9, 15), reach="melee"),
    Move("Acorn Blast", "attack", "A balanced ranged acorn throw.", dmg_range=(8, 16), reach="ranged"),
    Move("Scratch", "attack", "Quick claws, decent spread.", dmg_range=(7, 17), reach="melee"),
    Move("Chirp", "attack", "A risky, piercing shriek.", dmg_range=(4, 20), reach="ranged"),
    Move("Chirp Insanely", "attack", "Totally unhinged. Could whiff, could devastate.", dmg_range=(0, 26), reach="ranged"),
    Move(
        "Steal",
        "attack",
        "Swipes the rival's acorns; heals you for half the damage dealt.",
        dmg_range=(6, 14),
        lifesteal=True,
        reach="melee",
    ),
```

Leave the five defense/heal moves exactly as they are — they take the `"any"` default.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest squirrel-fight/ -v`
Expected: PASS — the 4 new tests plus all 68 existing ones.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/moves.py squirrel-fight/test_moves.py
git commit -m "Give each move a reach: melee, ranged or any"
```

---

## Task 2: Arena — the walking band and how far apart squirrels are

**Files:**
- Create: `squirrel-fight/arena.py`
- Test: `squirrel-fight/test_arena.py` (create)

- [ ] **Step 1: Write the failing test**

Create `squirrel-fight/test_arena.py`:

```python
import arena
from moves import Move


def test_gap_is_the_distance_between_them():
    assert arena.gap(250, 710) == 460
    assert arena.gap(710, 250) == 460


def test_close_and_far_split_at_the_threshold():
    assert arena.is_close(200, 200 + arena.CLOSE_RANGE) is True
    assert arena.is_close(200, 200 + arena.CLOSE_RANGE + 1) is False


def test_fighters_start_far_apart():
    assert arena.is_close(arena.PLAYER_START, arena.RIVAL_START) is False


def test_melee_reaches_only_when_close():
    move = Move("Tail Smack", "attack", "", dmg_range=(1, 1), reach="melee")
    assert arena.reaches(move, 400, 500) is True
    assert arena.reaches(move, 140, 820) is False


def test_ranged_reaches_only_when_far():
    move = Move("Acorn Blast", "attack", "", dmg_range=(1, 1), reach="ranged")
    assert arena.reaches(move, 140, 820) is True
    assert arena.reaches(move, 400, 500) is False


def test_any_reach_works_everywhere():
    move = Move("Scurry", "defense", "", block_reduction=0.5)
    assert arena.reaches(move, 400, 500) is True
    assert arena.reaches(move, 140, 820) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_arena.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'arena'`

- [ ] **Step 3: Write the minimal implementation**

Create `squirrel-fight/arena.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest squirrel-fight/test_arena.py -v`
Expected: PASS, 6 tests.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/arena.py squirrel-fight/test_arena.py
git commit -m "Add a pure arena module for distance and reach"
```

---

## Task 3: Arena — walking, without leaving the stage or overlapping

**Files:**
- Modify: `squirrel-fight/arena.py`
- Test: `squirrel-fight/test_arena.py`

- [ ] **Step 1: Write the failing test**

Append to `squirrel-fight/test_arena.py`:

```python
def test_player_stops_at_the_left_edge():
    assert arena.clamp_player(-500, arena.RIVAL_START) == arena.WALK_LEFT


def test_player_stops_short_of_the_rival():
    assert arena.clamp_player(900, 700) == 700 - arena.MIN_GAP


def test_rival_stops_at_the_right_edge():
    assert arena.clamp_rival(9999, arena.PLAYER_START) == arena.WALK_RIGHT


def test_rival_stops_short_of_the_player():
    assert arena.clamp_rival(100, 400) == 400 + arena.MIN_GAP


def test_squirrels_never_swap_sides():
    player = arena.clamp_player(9999, arena.RIVAL_START)
    rival = arena.clamp_rival(-9999, player)
    assert player < rival


def test_walking_right_moves_at_the_given_speed():
    moved = arena.walk_player(300, 1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == 300 + 220.0


def test_walking_left_moves_the_other_way():
    # Starts at 500 rather than 300: a 220px step left from 300 would land at 80,
    # outside the band, and the clamp would (correctly) pull it back to WALK_LEFT.
    moved = arena.walk_player(500, -1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == 500 - 220.0


def test_walking_is_clamped_like_everything_else():
    moved = arena.walk_player(arena.WALK_LEFT + 10, -1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == arena.WALK_LEFT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_arena.py -v`
Expected: FAIL with `AttributeError: module 'arena' has no attribute 'clamp_player'`

- [ ] **Step 3: Write the minimal implementation**

Add to `squirrel-fight/arena.py`, after `reaches()`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest squirrel-fight/test_arena.py -v`
Expected: PASS, 14 tests.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/arena.py squirrel-fight/test_arena.py
git commit -m "Let squirrels walk without leaving the stage or overlapping"
```

---

## Task 4: Arena — the rival's random wander

The rival picks a direction, ambles that way for a random stretch, then picks again. It turns around when it hits a wall or the player rather than grinding in place.

**Files:**
- Modify: `squirrel-fight/arena.py`
- Test: `squirrel-fight/test_arena.py`

- [ ] **Step 1: Write the failing test**

Append to `squirrel-fight/test_arena.py`:

```python
class FakeRandom:
    """A stand-in for `random` that hands back whatever the test wants."""

    def __init__(self, choices, ints):
        self.choices = list(choices)
        self.ints = list(ints)

    def choice(self, options):
        return self.choices.pop(0)

    def randint(self, low, high):
        return self.ints.pop(0)


def test_wander_picks_a_direction_when_its_stretch_runs_out():
    rng = FakeRandom(choices=[1], ints=[800])
    x, wander = arena.step_wander(arena.Wander(direction=-1, remaining_ms=0),
                                  500, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 800
    assert x > 500


def test_wander_keeps_going_while_its_stretch_lasts():
    rng = FakeRandom(choices=[], ints=[])
    x, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  500, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 400
    assert x > 500


def test_wander_turns_around_at_the_right_wall():
    rng = FakeRandom(choices=[], ints=[])
    _, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  arena.WALK_RIGHT, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == -1


def test_wander_stays_inside_the_band_over_many_steps():
    import random as real_random
    real_random.seed(1)
    wander = arena.Wander()
    x = arena.RIVAL_START
    for _ in range(2000):
        x, wander = arena.step_wander(wander, x, arena.PLAYER_START, 16)
        assert arena.WALK_LEFT <= x <= arena.WALK_RIGHT
        assert x >= arena.PLAYER_START + arena.MIN_GAP
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_arena.py -v`
Expected: FAIL with `AttributeError: module 'arena' has no attribute 'Wander'`

- [ ] **Step 3: Write the minimal implementation**

Add to the end of `squirrel-fight/arena.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest squirrel-fight/test_arena.py -v`
Expected: PASS, 18 tests.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/arena.py squirrel-fight/test_arena.py
git commit -m "Make the rival amble around at random"
```

---

## Task 5: Attacks whiff at the wrong distance

**Files:**
- Modify: `squirrel-fight/battle.py:16-21` (`FighterTurnOutcome`), `squirrel-fight/battle.py:64-107` (`resolve_turn`)
- Test: `squirrel-fight/test_battle.py`

- [ ] **Step 1: Write the failing test**

First, extend the existing `make_attack` helper at the top of `squirrel-fight/test_battle.py` so tests can set a reach. Replace it with:

```python
def make_attack(name, dmg_range, lifesteal=False, reach="any"):
    return Move(name=name, kind="attack", description="", dmg_range=dmg_range,
                lifesteal=lifesteal, reach=reach)
```

Then append these tests to the end of `squirrel-fight/test_battle.py`:

```python
def test_melee_whiffs_when_far_apart(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Tail Smack", (10, 13), reach="melee")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, close=False)
    assert result.fighter_a.whiffed is True
    assert result.fighter_a.damage_dealt == 0
    assert b.hp == 60


def test_melee_lands_when_close(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Tail Smack", (10, 13), reach="melee")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, close=True)
    assert result.fighter_a.whiffed is False
    assert result.fighter_a.damage_dealt == 13


def test_ranged_whiffs_when_close(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16), reach="ranged")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, close=True)
    assert result.fighter_a.whiffed is True
    assert b.hp == 60


def test_ranged_lands_when_far(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16), reach="ranged")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, close=False)
    assert result.fighter_a.whiffed is False
    assert result.fighter_a.damage_dealt == 16


def test_a_whiffed_steal_heals_nothing(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=30, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Steal", (6, 14), lifesteal=True, reach="melee")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, close=False)
    assert result.fighter_a.whiffed is True
    assert result.fighter_a.healed == 0
    assert a.hp == 30


def test_defenses_and_heals_ignore_distance(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=30, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_heal("Eat Garden", (12, 18))
    move_b = make_block_pct("Scurry", 0.5)
    result = resolve_turn(a, move_a, b, move_b, close=True)
    assert result.fighter_a.healed == 18
    assert a.hp == 48


def test_no_distance_given_means_everything_reaches(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Tail Smack", (10, 13), reach="melee")
    move_b = make_attack("Acorn Blast", (8, 16), reach="ranged")
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.whiffed is False
    assert result.fighter_b.whiffed is False
    assert result.fighter_a.damage_dealt == 13
    assert result.fighter_b.damage_dealt == 16
```

That last test is the one that proves the terminal version is unaffected.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_battle.py -v`
Expected: FAIL with `TypeError: resolve_turn() got an unexpected keyword argument 'close'`

- [ ] **Step 3: Write the minimal implementation**

In `squirrel-fight/battle.py`, add `whiffed` to the outcome dataclass:

```python
@dataclass
class FighterTurnOutcome:
    move_name: str
    damage_dealt: int = 0
    healed: int = 0
    dodged: bool = False
    whiffed: bool = False
```

Add this helper just above `resolve_turn`:

```python
def _reaches(move: Move, close: bool | None) -> bool:
    """Can this move connect from here?

    `close` is True when the fighters are near each other, False when they are
    apart, and None when distance isn't part of the game at all — which is how
    the terminal version in `game.py` keeps playing exactly as it always has.
    """
    if close is None or move.reach == "any":
        return True
    return close if move.reach == "melee" else not close
```

Change `resolve_turn`'s signature and its two attack branches. The signature becomes:

```python
def resolve_turn(
    fighter_a: Fighter,
    move_a: Move,
    fighter_b: Fighter,
    move_b: Move,
    close: bool | None = None,
) -> TurnResult:
```

Replace the first attack branch (currently `battle.py:72-77`) with:

```python
    if move_a.kind == "attack":
        if not _reaches(move_a, close):
            outcome_a.whiffed = True
        else:
            raw = _roll_damage(move_a)
            defending = move_b if move_b.kind == "defense" else None
            dmg_a_to_b, b_dodged = _mitigate(raw, defending)
            if defending is not None and defending.dodge_chance is not None:
                outcome_b.dodged = b_dodged
```

Replace the second attack branch (currently `battle.py:79-84`) with:

```python
    if move_b.kind == "attack":
        if not _reaches(move_b, close):
            outcome_b.whiffed = True
        else:
            raw = _roll_damage(move_b)
            defending = move_a if move_a.kind == "defense" else None
            dmg_b_to_a, a_dodged = _mitigate(raw, defending)
            if defending is not None and defending.dodge_chance is not None:
                outcome_a.dodged = a_dodged
```

Leave the lifesteal, heal, clash and HP lines below exactly as they are — a whiff leaves `dmg_a_to_b` at 0, so lifesteal already comes out as 0 without a special case.

- [ ] **Step 4: Run the whole suite**

Run: `python3 -m pytest squirrel-fight/ -v`
Expected: PASS — 7 new battle tests, and all previously existing tests still green.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/battle.py squirrel-fight/test_battle.py
git commit -m "Whiff attacks used at the wrong distance"
```

---

## Task 6: A whiff gets its own caption

Without this a whiff reads "B shrugs it off!", which sounds like a tough squirrel rather than a missed swing.

**Files:**
- Modify: `squirrel-fight/choreography.py` (the `if move.kind == "attack":` branch inside `build_timeline`)
- Test: `squirrel-fight/test_choreography.py`

- [ ] **Step 1: Write the failing test**

Append to `squirrel-fight/test_choreography.py`:

```python
def captions_of(timeline):
    return [text for _, text in timeline.captions]


def build_one_sided(player_move, player_outcome):
    """A turn where only the player acts and the rival stands there."""
    rival_move = Move("Scurry", "defense", "", block_reduction=0.5)
    result = TurnResult(
        fighter_a=player_outcome,
        fighter_b=FighterTurnOutcome(move_name=rival_move.name),
    )
    return build_timeline(
        "Nutsy", "Chompy", player_move, rival_move, result,
        {PLAYER: 60, RIVAL: 60}, {PLAYER: 60, RIVAL: 60}, 60,
    )


def test_melee_whiff_says_the_rival_is_too_far():
    move = Move("Tail Smack", "attack", "", dmg_range=(10, 13), reach="melee")
    outcome = FighterTurnOutcome(move_name="Tail Smack", whiffed=True)
    captions = " ".join(captions_of(build_one_sided(move, outcome)))
    assert "too far away" in captions
    assert "shrugs it off" not in captions


def test_ranged_whiff_says_the_rival_is_too_close():
    move = Move("Acorn Blast", "attack", "", dmg_range=(8, 16), reach="ranged")
    outcome = FighterTurnOutcome(move_name="Acorn Blast", whiffed=True)
    captions = " ".join(captions_of(build_one_sided(move, outcome)))
    assert "too close" in captions
    assert "shrugs it off" not in captions


def test_a_whiff_does_not_stagger_the_other_squirrel():
    move = Move("Tail Smack", "attack", "", dmg_range=(10, 13), reach="melee")
    outcome = FighterTurnOutcome(move_name="Tail Smack", whiffed=True)
    timeline = build_one_sided(move, outcome)
    effects = {cue.effect for cue in timeline.cues if cue.actor == RIVAL}
    assert "stagger" not in effects
    assert "flash" not in effects
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_choreography.py -v`
Expected: FAIL — `assert "too far away" in captions` fails, because the caption still reads "shrugs it off".

- [ ] **Step 3: Write the minimal implementation**

In `squirrel-fight/choreography.py`, inside `build_timeline`'s `if move.kind == "attack":` block, add a new first branch before the existing `if other_outcome.dodged:` so the chain reads whiff → dodge → hit → shrug:

```python
        if move.kind == "attack":
            cues.append(Cue(start_ms, ACTION_MS, actor, "lunge"))
            hit_ms = start_ms + IMPACT_MS
            if own.whiffed:
                # The lunge still plays — it just doesn't arrive anywhere, and
                # the other squirrel has nothing to react to.
                if move.reach == "melee":
                    captions.append((hit_ms, "{} swipes at thin air — {} is too far away!".format(
                        names[actor], names[other])))
                else:
                    captions.append((hit_ms, "{} is far too close for {} to land!".format(
                        names[other], move.name)))
            elif other_outcome.dodged:
                cues.append(Cue(start_ms + DODGE_MS, HOP_MS, other, "hop"))
                captions.append((hit_ms, "{} dodges out of the way!".format(names[other])))
            elif own.damage_dealt > 0:
                cues.append(Cue(hit_ms, STAGGER_MS, other, "stagger"))
                cues.append(Cue(hit_ms, FLASH_MS, other, "flash"))
                captions.append((hit_ms, "{} hits {} for {} damage!".format(
                    names[actor], names[other], own.damage_dealt)))
                hp_events[other].append((hit_ms, HP_MS, -own.damage_dealt))
            else:
                cues.append(Cue(hit_ms, BRACE_MS, other, "brace"))
                captions.append((hit_ms, "{} shrugs it off!".format(names[other])))
```

The `lifesteal` block that follows stays where it is — a whiff has `own.healed == 0`, so it doesn't fire.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest squirrel-fight/ -v`
Expected: PASS, including the 3 new choreography tests.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/choreography.py squirrel-fight/test_choreography.py
git commit -m "Say why an attack whiffed instead of shrugging it off"
```

---

## Task 7: Squirrels stand where the arena says, not on fixed marks

Pure refactor — behaviour identical, because the starting positions match today's constants. Do this before adding movement so any breakage is obviously from this step.

**Files:**
- Modify: `squirrel-fight/visual_game.py:54-55`, `:109-146`, `:307-308`

- [ ] **Step 1: Delete the fixed marks and import the arena**

In `squirrel-fight/visual_game.py`, add to the imports after `from battle import ...`:

```python
import arena
```

Delete these two lines (currently `visual_game.py:54-55`):

```python
PLAYER_X = 250
RIVAL_X = 710
```

- [ ] **Step 2: Hold live positions on the Game**

In `Game.__init__`, after `self.hover = None`, add:

```python
        self.player_x = arena.PLAYER_START
        self.rival_x = arena.RIVAL_START
        self.wander = arena.Wander()
```

In `start_battle`, add the same three lines just before `self.state = "battle"`, so every new battle starts both squirrels back on their marks:

```python
        self.player_x = arena.PLAYER_START
        self.rival_x = arena.RIVAL_START
        self.wander = arena.Wander()
```

- [ ] **Step 3: Draw them at their live positions**

In `_draw_stage`, replace the two calls (currently `visual_game.py:307-308`):

```python
        self._draw_squirrel(PLAYER, self.player_x)
        self._draw_squirrel(RIVAL, self.rival_x)
```

- [ ] **Step 4: Verify the game still runs and looks unchanged**

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS, all tests.

Run: `python3 squirrel-fight/visual_game.py`
Expected: the window opens, both squirrels stand exactly where they used to, a battle plays through normally. Press Esc to quit.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/visual_game.py
git commit -m "Position squirrels from the arena instead of fixed marks"
```

---

## Task 8: Walking, and a rival that won't stand still

**Files:**
- Modify: `squirrel-fight/visual_game.py` (`update`, currently `:213-220`)

- [ ] **Step 1: Walk on held keys, and wander every frame**

Arrow keys are read with `pygame.key.get_pressed()` rather than as KEYDOWN events, because walking needs to continue while a key is held.

In `squirrel-fight/visual_game.py`, replace `update` with:

```python
    def update(self, dt_ms):
        if self.state == "battle":
            self._walk(dt_ms)
            return
        if self.state != "animating":
            return
        self.elapsed_ms = min(self.elapsed_ms + dt_ms, self.timeline.total_ms)
        self.frame = sample(self.timeline, self.elapsed_ms)
        if self.elapsed_ms >= self.timeline.total_ms:
            self.message = self.frame.caption
            self.state = "result" if self.outcome != "ongoing" else "battle"

    def _walk(self, dt_ms):
        """Move both squirrels while the player is choosing a move.

        The rival ambles the whole time, so the gap keeps changing and the
        player has to commit at a moment when their move will actually reach.
        """
        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1
        if direction:
            self.player_x = arena.walk_player(self.player_x, direction, dt_ms, self.rival_x)
        self.rival_x, self.wander = arena.step_wander(
            self.wander, self.rival_x, self.player_x, dt_ms
        )
```

- [ ] **Step 2: Tell the battle how far apart they are**

In `take_turn`, pass the distance through. Replace the `resolve_turn` call (currently `visual_game.py:199`) with:

```python
        result = resolve_turn(
            self.player, move, self.rival, rival_move,
            close=arena.is_close(self.player_x, self.rival_x),
        )
```

- [ ] **Step 3: Verify by playing it**

Run: `python3 squirrel-fight/visual_game.py`
Expected:
- The rival squirrel ambles left and right on its own while the move menu is up, turning around at the edges and when it bumps into you.
- Left/Right arrows (and A/D) walk your squirrel; you stop at the stage edges and can't walk through the rival.
- A Tail Smack from across the stage says "swipes at thin air — ... is too far away!" and deals no damage.
- An Acorn Blast from right up close says "... is far too close for Acorn Blast to land!".
- Both connect normally at the right distance.

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS, all tests.

- [ ] **Step 4: Commit**

```bash
git add squirrel-fight/visual_game.py
git commit -m "Walk your squirrel while the rival ambles about"
```

---

## Task 9: Dim the moves that can't reach from here

The buttons stay clickable — picking one anyway and whiffing is part of the fun. They just stop looking inviting.

**Files:**
- Modify: `squirrel-fight/visual_game.py:367-385` (`_draw_buttons`)

- [ ] **Step 1: Dim per button rather than all-or-nothing**

Replace `_draw_buttons` with:

```python
    def _draw_buttons(self):
        frozen = self.state != "battle"
        for top, caption, kind in GROUP_LABELS:
            label = self.label_font.render(caption, True, KIND_STYLE[kind]["text"])
            self.screen.blit(label, (24, top))
        for button in self.buttons:
            style = KIND_STYLE[button.move.kind]
            fill, edge, text_color = style["fill"], style["edge"], style["text"]
            # A move that can't reach from here is dimmed but still clickable —
            # choosing it anyway and whiffing is allowed, and funny.
            out_of_range = not arena.reaches(button.move, self.player_x, self.rival_x)
            if frozen or out_of_range:
                fill = tuple(channel // 2 for channel in fill)
                edge = tuple(channel // 2 for channel in edge)
                text_color = tuple(channel // 2 for channel in text_color)
            elif button is self.hover:
                fill = tuple(min(255, channel + 26) for channel in fill)
            pygame.draw.rect(self.screen, fill, button.rect, border_radius=7)
            pygame.draw.rect(self.screen, edge, button.rect, width=2, border_radius=7)
            caption = "{}  {}".format(button.number, button.move.name)
            text = self.bold.render(caption, True, text_color)
            self.screen.blit(text, text.get_rect(center=button.rect.center))
```

- [ ] **Step 2: Verify by playing it**

Run: `python3 squirrel-fight/visual_game.py`
Expected: at the start of a battle the four melee moves (Tail Smack, Cheek Barrel, Scratch, Steal) are dim and the three ranged ones are bright. Walk toward the rival and they swap over as you cross the threshold. Defenses and Eat Garden never dim during the battle state.

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS, all tests.

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/visual_game.py
git commit -m "Dim the moves that can't reach from where you are standing"
```

---

## Task 10: Tell the player how to play it

**Files:**
- Modify: `squirrel-fight/README.md`

- [ ] **Step 1: Document the controls**

In `squirrel-fight/README.md`, in the "Play in a window" section, after the paragraph beginning "Click a move, or use the number row", add:

```markdown
**Walk your squirrel** with the left and right arrow keys (or `A` and `D`) while
you're choosing a move. The rival wanders about on its own the whole time, so the
gap between you keeps changing.

Where you're standing decides what connects:

| Moves | Only work |
| --- | --- |
| Tail Smack, Cheek Barrel, Scratch, Steal | up close |
| Acorn Blast, Chirp, Chirp Insanely | from a distance |
| Dance, Moonwalk, Scurry, Flex, Eat Garden | anywhere |

A move that can't reach is dimmed — you can still pick it, but it whiffs for no
damage. The rival wanders at random rather than cleverly, so it does this to
itself all the time.

Walking is a window-version feature. The terminal version plays as it always
has, with every move always reaching.
```

- [ ] **Step 2: Verify the whole thing one more time**

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS, all tests.

Run: `python3 squirrel-fight/game.py`
Expected: the terminal version plays exactly as before — no mention of distance, every move connects. Play a couple of turns and quit.

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/README.md
git commit -m "Document walking and what reaches from where"
```

---

## Done when

- All tests pass: `python3 -m pytest squirrel-fight/ -q`
- `python3 squirrel-fight/visual_game.py` — you can walk, the rival wanders, out-of-range moves dim and whiff with a message explaining why.
- `python3 squirrel-fight/game.py` — unchanged from before this plan.
