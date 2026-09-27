# Wide World Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Widen the window version's world from one screen to three, with a camera that follows the fight and a third range band so backing off has a cost.

**Architecture:** `arena.py` grows world-scale constants, a three-way `band()` and a stateless `camera_x()`; it stays pure. `battle.py` swaps its boolean `close` for a `band` string and records *why* an attack whiffed. `choreography.py` turns that reason into a caption. `visual_game.py` converts world coordinates to screen by subtracting the camera, and tiles the existing one-screen background across the world. `game.py` is never touched.

**Tech Stack:** Python 3.9 (system interpreter, no venv), pygame-ce, pytest.

**Spec:** `docs/superpowers/specs/2026-09-26-wide-world-design.md`

---

## File Structure

| File | Responsibility |
| --- | --- |
| `squirrel-fight/arena.py` | **Modify.** World-scale constants, mutual leash, `band()`, `camera_x()`. Still no pygame. |
| `squirrel-fight/test_arena.py` | **Modify.** Several existing tests assert behaviour that deliberately changes. |
| `squirrel-fight/battle.py` | **Modify.** `close: bool` → `band: str`; `whiffed: bool` → `whiff_reason: str \| None`. |
| `squirrel-fight/test_battle.py` | **Modify.** Migrate 7 `close=` tests, add far-band cases. |
| `squirrel-fight/choreography.py` | **Modify.** A third whiff caption, chosen from `whiff_reason`. |
| `squirrel-fight/test_choreography.py` | **Modify.** Migrate 3 whiff tests, add the "drops short" case. |
| `squirrel-fight/visual_game.py` | **Modify.** Camera, world→screen, tiled background, pass `band`. |
| `squirrel-fight/README.md` | **Modify.** Note that the world is three screens and the background tiles. |

**This plan deliberately changes existing behaviour**, so tests that encode the old rules
must change with it. Every such test is named explicitly below. If a test not named here
starts failing, that is a real regression — investigate, don't edit it.

All commands are run from the repo root, `/Users/kgreenman/git/juliana-games`.
Baseline before starting: **100 tests passing.**

---

## Task 1: A world three screens wide, with a mutual leash

**Files:**
- Modify: `squirrel-fight/arena.py`
- Test: `squirrel-fight/test_arena.py`

- [ ] **Step 1: Replace the constants**

In `squirrel-fight/arena.py`, replace the constants block (from `WALK_LEFT` down to and
including `RIVAL_START`) with:

```python
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
```

Leave `PLAYER_SPEED`, `RIVAL_SPEED`, `WANDER_MIN_MS` and `WANDER_MAX_MS` exactly as they are.

- [ ] **Step 2: Replace `is_close` with `band`, and rewrite `reaches`**

Replace the `is_close` and `reaches` functions with:

```python
def band(player_x, rival_x) -> str:
    """Which of the three range bands these two are standing in."""
    distance = gap(player_x, rival_x)
    if distance <= CLOSE_RANGE:
        return CLOSE
    if distance <= LONG_RANGE:
        return MID
    return FAR


def reaches(move, player_x, rival_x) -> bool:
    """Would `move` connect from where these two are standing?"""
    if move.reach == "any":
        return True
    here = band(player_x, rival_x)
    if move.reach == "melee":
        return here == CLOSE
    return here == MID
```

`gap()` is unchanged. `is_close` is gone — nothing outside this module should call it
after Task 5.

- [ ] **Step 3: Make both clamps enforce the leash**

Replace `clamp_player` and `clamp_rival` with:

```python
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
```

`walk_player` and `step_wander` are unchanged — they already route through these.

- [ ] **Step 4: Update the tests whose meaning changed**

In `squirrel-fight/test_arena.py`, replace these five tests. Each one encoded a rule this
task deliberately changes.

Replace `test_close_and_far_split_at_the_threshold` and `test_fighters_start_far_apart`:

```python
def test_the_three_bands_split_at_their_thresholds():
    assert arena.band(200, 200 + arena.CLOSE_RANGE) == arena.CLOSE
    assert arena.band(200, 200 + arena.CLOSE_RANGE + 1) == arena.MID
    assert arena.band(200, 200 + arena.LONG_RANGE) == arena.MID
    assert arena.band(200, 200 + arena.LONG_RANGE + 1) == arena.FAR


def test_fighters_start_in_the_ranged_band():
    assert arena.band(arena.PLAYER_START, arena.RIVAL_START) == arena.MID
```

Replace `test_ranged_reaches_only_when_far` — ranged now fails in the far band too, which
is the whole point of the third band:

```python
def test_ranged_reaches_only_in_the_middle_band():
    move = Move("Acorn Blast", "attack", "", dmg_range=(1, 1), reach="ranged")
    assert arena.reaches(move, 400, 400 + arena.LONG_RANGE) is True
    assert arena.reaches(move, 400, 500) is False              # too close
    assert arena.reaches(move, 400, 400 + arena.LONG_RANGE + 1) is False   # drops short
```

Replace `test_player_stops_at_the_left_edge` — the player now usually stops at the leash,
so reaching the world edge needs a rival that is itself near the left edge:

```python
def test_player_stops_at_the_world_edge():
    # Rival close enough to the left edge that the leash isn't the binding limit.
    assert arena.clamp_player(-500, 600) == arena.WALK_LEFT


def test_player_is_held_back_by_the_leash():
    assert arena.clamp_player(-500, 1670) == 1670 - arena.LEASH
```

Replace `test_rival_stops_at_the_right_edge` for the same reason:

```python
def test_rival_stops_at_the_world_edge():
    assert arena.clamp_rival(9999, arena.WALK_RIGHT - arena.MIN_GAP) == arena.WALK_RIGHT


def test_rival_is_held_back_by_the_leash():
    assert arena.clamp_rival(9999, 1210) == 1210 + arena.LEASH
```

Replace the two walking tests, whose old start positions now fall outside the leash:

```python
def test_walking_right_moves_at_the_given_speed():
    # Player at 1200 with the rival at RIVAL_START has room either way inside the leash.
    moved = arena.walk_player(1200, 1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == 1200 + 220.0


def test_walking_left_moves_the_other_way():
    moved = arena.walk_player(1200, -1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == 1200 - 220.0
```

Replace `test_walking_is_clamped_like_everything_else`:

```python
def test_walking_is_clamped_like_everything_else():
    # Hard left with the rival near the left edge: the world edge stops us.
    moved = arena.walk_player(arena.WALK_LEFT + 10, -1, 1000, 600, speed=220.0)
    assert moved == arena.WALK_LEFT
```

Replace `test_wander_stays_inside_the_band_over_many_steps` to also assert the leash:

```python
def test_wander_stays_inside_the_band_and_the_leash_over_many_steps():
    import random as real_random
    real_random.seed(1)
    wander = arena.Wander()
    x = arena.RIVAL_START
    for _ in range(2000):
        x, wander = arena.step_wander(wander, x, arena.PLAYER_START, 16)
        assert arena.WALK_LEFT <= x <= arena.WALK_RIGHT
        assert arena.PLAYER_START + arena.MIN_GAP <= x <= arena.PLAYER_START + arena.LEASH
```

Replace the three `FakeRandom` wander tests. They place the rival at positions the leash
now forbids — `clamp_rival` silently drags it back, so two of them still pass while
testing nothing, and `test_wander_turns_around_at_the_right_wall` fails outright because
the rival can no longer reach the world edge while the player sits at `PLAYER_START`:

```python
def test_wander_picks_a_direction_when_its_stretch_runs_out():
    rng = FakeRandom(choices=[1], ints=[800])
    x, wander = arena.step_wander(arena.Wander(direction=-1, remaining_ms=0),
                                  arena.RIVAL_START, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 800
    assert x > arena.RIVAL_START


def test_wander_keeps_going_while_its_stretch_lasts():
    rng = FakeRandom(choices=[], ints=[])
    x, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  arena.RIVAL_START, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 400
    assert x > arena.RIVAL_START


def test_wander_turns_around_at_the_world_edge():
    rng = FakeRandom(choices=[], ints=[])
    # The player has to be pressed against the right edge for the rival to reach it.
    _, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  arena.WALK_RIGHT, arena.WALK_RIGHT - arena.MIN_GAP,
                                  100, rng=rng)
    assert wander.direction == -1


def test_wander_turns_around_at_the_leash():
    rng = FakeRandom(choices=[], ints=[])
    at_leash = arena.PLAYER_START + arena.LEASH
    _, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  at_leash, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == -1
```

- [ ] **Step 5: Add a test that the leash binds the player too**

Append to `squirrel-fight/test_arena.py`:

```python
def test_the_player_cannot_outrun_the_leash():
    """Walking hard away from a stationary rival stops at the leash, not the edge."""
    player_x = arena.PLAYER_START
    for _ in range(600):
        player_x = arena.walk_player(player_x, -1, 16, arena.RIVAL_START)
    assert arena.gap(player_x, arena.RIVAL_START) == arena.LEASH


def test_neither_squirrel_can_be_pushed_out_of_the_world():
    assert arena.clamp_player(9999, arena.WALK_RIGHT) <= arena.WALK_RIGHT - arena.MIN_GAP
    assert arena.clamp_rival(-9999, arena.WALK_LEFT) >= arena.WALK_LEFT + arena.MIN_GAP
```

- [ ] **Step 6: Run the arena tests**

Run: `python3 -m pytest squirrel-fight/test_arena.py -v`
Expected: PASS. `test_battle.py` and `visual_game.py` still call the removed `is_close`
at this point, so the *full* suite is expected to fail until Tasks 3 and 5 — that is fine.

- [ ] **Step 7: Commit**

```bash
git add squirrel-fight/arena.py squirrel-fight/test_arena.py
git commit -m "Widen the world to three screens and add a third range band"
```

---

## Task 2: The camera

Stateless: computed fresh from the two positions each frame. Because the squirrels move
smoothly, so does it — no smoothing or lerp needed.

**Files:**
- Modify: `squirrel-fight/arena.py`
- Test: `squirrel-fight/test_arena.py`

- [ ] **Step 1: Write the failing test**

Append to `squirrel-fight/test_arena.py`:

```python
def test_camera_centres_between_the_two_squirrels():
    # Well inside the world, so no clamping interferes.
    assert arena.camera_x(1200, 1600) == 1400 - arena.WINDOW_WIDTH / 2


def test_camera_stops_at_the_left_of_the_world():
    assert arena.camera_x(arena.WALK_LEFT, arena.WALK_LEFT + arena.MIN_GAP) == 0


def test_camera_stops_at_the_right_of_the_world():
    assert arena.camera_x(arena.WALK_RIGHT - arena.MIN_GAP, arena.WALK_RIGHT) == (
        arena.WORLD_WIDTH - arena.WINDOW_WIDTH
    )


def test_opening_positions_look_exactly_like_the_old_one_screen_stage():
    """The game should open on the marks the squirrels always stood on."""
    camera = arena.camera_x(arena.PLAYER_START, arena.RIVAL_START)
    assert arena.PLAYER_START - camera == 250
    assert arena.RIVAL_START - camera == 710
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_arena.py -v`
Expected: FAIL with `AttributeError: module 'arena' has no attribute 'camera_x'`

- [ ] **Step 3: Write the minimal implementation**

Add to `squirrel-fight/arena.py`, after `band()`:

```python
def camera_x(player_x, rival_x) -> float:
    """The left edge of the view: centred between the fighters, inside the world.

    Deliberately stateless — recomputed every frame rather than stored and eased.
    The squirrels already move smoothly, so the camera does too, and there is no
    scroll position that can drift out of step with where they actually are.
    """
    middle = (player_x + rival_x) / 2.0
    return max(0.0, min(WORLD_WIDTH - WINDOW_WIDTH, middle - WINDOW_WIDTH / 2.0))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest squirrel-fight/test_arena.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/arena.py squirrel-fight/test_arena.py
git commit -m "Add a stateless camera centred between the fighters"
```

---

## Task 3: Battle takes a band and records why a move missed

`whiffed: bool` is replaced by `whiff_reason: str | None` rather than joined by it —
two fields meaning the same thing would be redundant state that can disagree.

**On the band strings:** `battle.py` compares against the literals `"close"` and `"mid"`
rather than importing `arena.CLOSE`/`arena.MID`. That is deliberate — the spec keeps the
rules module free of stage geometry, and importing `arena` for two strings would drag
pixel constants into it. The cost is that the two modules must agree on the spellings;
`arena.band()` is the only thing that produces them and `battle._reaches()` the only
thing that consumes them, so they are three lines apart in practice.

**Files:**
- Modify: `squirrel-fight/battle.py`
- Test: `squirrel-fight/test_battle.py`

- [ ] **Step 1: Change the outcome and the helper**

In `squirrel-fight/battle.py`, change `FighterTurnOutcome`:

```python
@dataclass
class FighterTurnOutcome:
    move_name: str
    damage_dealt: int = 0
    healed: int = 0
    dodged: bool = False
    # None when the move landed; otherwise "too_far" or "too_close", so the
    # caption can explain itself without choreography learning any geometry.
    whiff_reason: str | None = None
```

Replace `_reaches` with:

```python
def _reaches(move: Move, band: str | None) -> bool:
    """Can this move connect from this range band?

    `band` is "close", "mid" or "far", or None when distance isn't part of the
    game at all — which is how the terminal version in `game.py` keeps playing
    exactly as it always has.
    """
    if band is None or move.reach == "any":
        return True
    if move.reach == "melee":
        return band == "close"
    return band == "mid"


def _whiff_reason(move: Move, band: str | None) -> str:
    """Why a move that didn't reach didn't reach."""
    if move.reach == "ranged" and band == "close":
        return "too_close"
    return "too_far"
```

- [ ] **Step 2: Change `resolve_turn`**

Change the signature's last parameter from `close: bool | None = None` to:

```python
    band: str | None = None,
```

and in both attack branches replace the whiff line. The first becomes:

```python
    if move_a.kind == "attack":
        if not _reaches(move_a, band):
            outcome_a.whiff_reason = _whiff_reason(move_a, band)
        else:
```

and the second:

```python
    if move_b.kind == "attack":
        if not _reaches(move_b, band):
            outcome_b.whiff_reason = _whiff_reason(move_b, band)
        else:
```

Everything below the attack branches is unchanged.

- [ ] **Step 3: Migrate the seven existing range tests**

In `squirrel-fight/test_battle.py`, these seven tests pass `close=True`/`close=False` and
assert `whiffed`. Rewrite them as follows.

```python
def test_melee_whiffs_when_far_apart(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Tail Smack", (10, 13), reach="melee")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, band="mid")
    assert result.fighter_a.whiff_reason == "too_far"
    assert result.fighter_a.damage_dealt == 0
    assert b.hp == 60


def test_melee_lands_when_close(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Tail Smack", (10, 13), reach="melee")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, band="close")
    assert result.fighter_a.whiff_reason is None
    assert result.fighter_a.damage_dealt == 13


def test_ranged_whiffs_when_close(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16), reach="ranged")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, band="close")
    assert result.fighter_a.whiff_reason == "too_close"
    assert b.hp == 60


def test_ranged_lands_in_the_middle_band(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16), reach="ranged")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, band="mid")
    assert result.fighter_a.whiff_reason is None
    assert result.fighter_a.damage_dealt == 16


def test_a_whiffed_steal_heals_nothing(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=30, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Steal", (6, 14), lifesteal=True, reach="melee")
    move_b = make_heal("Eat Garden", (0, 0))
    result = resolve_turn(a, move_a, b, move_b, band="far")
    assert result.fighter_a.whiff_reason == "too_far"
    assert result.fighter_a.healed == 0
    assert a.hp == 30


def test_defenses_and_heals_ignore_distance(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    for band in ("close", "mid", "far"):
        a = Fighter(name="A", hp=30, max_hp=60)
        b = Fighter(name="B", hp=60, max_hp=60)
        move_a = make_heal("Eat Garden", (12, 18))
        move_b = make_block_pct("Scurry", 0.5)
        result = resolve_turn(a, move_a, b, move_b, band=band)
        assert result.fighter_a.healed == 18
        assert a.hp == 48


def test_no_distance_given_means_everything_reaches(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Tail Smack", (10, 13), reach="melee")
    move_b = make_attack("Acorn Blast", (8, 16), reach="ranged")
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.whiff_reason is None
    assert result.fighter_b.whiff_reason is None
    assert result.fighter_a.damage_dealt == 13
    assert result.fighter_b.damage_dealt == 16
```

- [ ] **Step 4: Add the far-band tests**

Append to `squirrel-fight/test_battle.py`:

```python
def test_nothing_reaches_from_the_far_band(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    for reach in ("melee", "ranged"):
        a = Fighter(name="A", hp=60, max_hp=60)
        b = Fighter(name="B", hp=60, max_hp=60)
        move_a = make_attack("Whatever", (10, 13), reach=reach)
        move_b = make_heal("Eat Garden", (0, 0))
        result = resolve_turn(a, move_a, b, move_b, band="far")
        assert result.fighter_a.whiff_reason == "too_far"
        assert result.fighter_a.damage_dealt == 0
        assert b.hp == 60


def test_only_a_close_ranged_move_counts_as_too_close(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    # A melee move in the far band is too far, never "too close".
    result = resolve_turn(a, make_attack("Tail Smack", (10, 13), reach="melee"),
                          b, make_heal("Eat Garden", (0, 0)), band="far")
    assert result.fighter_a.whiff_reason == "too_far"
```

- [ ] **Step 5: Run the battle tests**

Run: `python3 -m pytest squirrel-fight/test_battle.py squirrel-fight/test_moves.py -v`
Expected: PASS. `test_choreography.py` still asserts `whiffed` and `visual_game.py` still
passes `close=`, so the full suite stays red until Tasks 4 and 5.

- [ ] **Step 6: Commit**

```bash
git add squirrel-fight/battle.py squirrel-fight/test_battle.py
git commit -m "Resolve turns by range band and record why a move missed"
```

---

## Task 4: A caption for the acorn that drops short

**Files:**
- Modify: `squirrel-fight/choreography.py`
- Test: `squirrel-fight/test_choreography.py`

- [ ] **Step 1: Update the whiff branch**

In `squirrel-fight/choreography.py`, replace the `if own.whiffed:` branch inside
`build_timeline` with:

```python
            if own.whiff_reason is not None:
                # The lunge still plays — it just doesn't arrive anywhere, and
                # the other squirrel has nothing to react to.
                if own.whiff_reason == "too_close":
                    captions.append((hit_ms, "{} is far too close for {} to land!".format(
                        names[other], move.name)))
                elif move.reach == "melee":
                    captions.append((hit_ms, "{} swipes at thin air — {} is too far away!".format(
                        names[actor], names[other])))
                else:
                    captions.append((hit_ms, "{}'s {} drops well short!".format(
                        names[actor], move.name)))
```

The rest of the attack chain (`elif other_outcome.dodged:` onward) is unchanged.

- [ ] **Step 2: Migrate the three whiff tests and add the new one**

In `squirrel-fight/test_choreography.py`, the three tests added last time construct
`FighterTurnOutcome(..., whiffed=True)`, which no longer exists. Replace them with:

```python
def test_melee_whiff_says_the_rival_is_too_far():
    move = Move("Tail Smack", "attack", "", dmg_range=(10, 13), reach="melee")
    outcome = FighterTurnOutcome(move_name="Tail Smack", whiff_reason="too_far")
    captions = " ".join(captions_of(build_one_sided(move, outcome)))
    assert "too far away" in captions
    assert "shrugs it off" not in captions


def test_ranged_whiff_up_close_says_too_close():
    move = Move("Acorn Blast", "attack", "", dmg_range=(8, 16), reach="ranged")
    outcome = FighterTurnOutcome(move_name="Acorn Blast", whiff_reason="too_close")
    captions = " ".join(captions_of(build_one_sided(move, outcome)))
    assert "too close" in captions
    assert "shrugs it off" not in captions


def test_ranged_whiff_from_the_far_band_drops_short():
    move = Move("Acorn Blast", "attack", "", dmg_range=(8, 16), reach="ranged")
    outcome = FighterTurnOutcome(move_name="Acorn Blast", whiff_reason="too_far")
    captions = " ".join(captions_of(build_one_sided(move, outcome)))
    assert "drops well short" in captions
    assert "too close" not in captions


def test_a_whiff_does_not_stagger_the_other_squirrel():
    move = Move("Tail Smack", "attack", "", dmg_range=(10, 13), reach="melee")
    outcome = FighterTurnOutcome(move_name="Tail Smack", whiff_reason="too_far")
    timeline = build_one_sided(move, outcome)
    effects = {cue.effect for cue in timeline.cues if cue.actor == RIVAL}
    assert "stagger" not in effects
    assert "flash" not in effects
    assert "brace" not in effects
```

Note the added `"brace"` assertion: the previous version of this test passed whether or
not the whiff branch existed, because the old zero-damage path also avoided stagger and
flash. Asserting no `brace` cue is what actually distinguishes a whiff from a shrug.

- [ ] **Step 3: Run the choreography tests**

Run: `python3 -m pytest squirrel-fight/test_choreography.py -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add squirrel-fight/choreography.py squirrel-fight/test_choreography.py
git commit -m "Say when an acorn drops short rather than missing"
```

---

## Task 5: Scroll the window across the world

This is the task that makes the full suite green again.

**Files:**
- Modify: `squirrel-fight/visual_game.py` (`take_turn` ~line 202, `_draw_stage` ~line 324)

- [ ] **Step 1: Pass the band instead of a boolean**

In `take_turn`, replace the `resolve_turn` call with:

```python
        result = resolve_turn(
            self.player, move, self.rival, rival_move,
            band=arena.band(self.player_x, self.rival_x),
        )
```

- [ ] **Step 2: Scroll the stage and tile the background**

Replace `_draw_stage` with:

```python
    def _draw_stage(self):
        # Everything on the stage is drawn relative to the camera, which is just
        # the midpoint between the fighters clamped to the world.
        camera = arena.camera_x(self.player_x, self.rival_x)

        # The arena drawing is a frame — trunks down the sides, leaves above,
        # dirt below — with a see-through middle, so the sky and grass are laid
        # down first and show through it rather than being replaced by it.
        pygame.draw.rect(self.screen, COLOR_SKY,
                         (0, STAGE_TOP, WINDOW_SIZE[0], GROUND_Y - STAGE_TOP))
        pygame.draw.rect(self.screen, COLOR_GRASS,
                         (0, GROUND_Y, WINDOW_SIZE[0], STAGE_BOTTOM - GROUND_Y))
        background = load_background()
        if background is not None:
            # One screen of scenery repeated across a world several screens wide.
            # A tiled frame repeats its edges, which reads as a continuous burrow
            # wall — good enough until there is proper wide scenery to draw.
            tile_width = background.get_width()
            left = int(camera // tile_width) * tile_width
            while left < camera + WINDOW_SIZE[0]:
                self.screen.blit(background, (left - camera, STAGE_TOP))
                left += tile_width

        # Squirrels are drawn after the HP panel, so a big enough hop or a wide
        # rotation would otherwise paint over the HP bars. The effects are tuned
        # to stay inside the stage; this makes that a guarantee rather than a
        # thing to remember every time an effect is added.
        self.screen.set_clip(pygame.Rect(0, STAGE_TOP, WINDOW_SIZE[0], STAGE_BOTTOM - STAGE_TOP))
        self._draw_squirrel(PLAYER, self.player_x - camera)
        self._draw_squirrel(RIVAL, self.rival_x - camera)
        self.screen.set_clip(None)
```

`_draw_squirrel` itself needs no change — it already takes a screen-space centre.
`_draw_buttons` needs no change either: it goes through `arena.reaches()`, which now
answers in three bands.

- [ ] **Step 3: Run the whole suite**

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS — everything green again for the first time since Task 1.

- [ ] **Step 4: Verify by playing it**

Run: `python3 squirrel-fight/visual_game.py`
Expected:
- The game **opens looking exactly as it did before** — squirrels on the same marks.
- Walking scrolls the world past you instead of hitting a wall at the screen edge.
- Walk far enough from the rival and you stop, until its wandering gives you more rope.
- Backing off past the middle band makes ranged moves dim, and using one anyway says
  "…drops well short!".
- All twelve buttons dim in the far band except the defenses and Eat Garden.

Run: `python3 squirrel-fight/game.py`
Expected: the terminal version plays exactly as before. Play a few turns and quit.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/visual_game.py
git commit -m "Scroll the window across the wide world"
```

---

## Task 6: Document the wider world

**Files:**
- Modify: `squirrel-fight/README.md`

- [ ] **Step 1: Update the walking section**

In `squirrel-fight/README.md`, replace the range table under "Play in a window" with:

```markdown
| Moves | Only work |
| --- | --- |
| Tail Smack, Cheek Barrel, Scratch, Steal | up close |
| Acorn Blast, Chirp, Chirp Insanely | at middle distance |
| Dance, Moonwalk, Scurry, Flex, Eat Garden | anywhere |

Back off too far and even an acorn drops short, so there's a middle distance worth
holding rather than just running away.

The world is three screens wide and scrolls as you walk. Neither squirrel can get more
than about a screen from the other, so you'll sometimes walk into a soft stop until the
rival's wandering gives you more rope — the two of you roam the world together rather
than either one touring it alone.
```

- [ ] **Step 2: Note the tiling in the terrain section**

In the "Drawing your own terrain" section, append:

```markdown
The world is three screens wide, so your background is **tiled** across it — the same
picture repeated three times. Something with no strong left or right edge tiles best.
(Several different scenes, painted to the full world width, is the next thing planned.)
```

- [ ] **Step 3: Verify and commit**

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS.

```bash
git add squirrel-fight/README.md
git commit -m "Document the three-screen world and its tiled background"
```

---

## Done when

- `python3 -m pytest squirrel-fight/ -q` is green.
- `python3 squirrel-fight/visual_game.py` opens on the old marks, scrolls as you walk,
  holds you inside the leash, and says "drops well short" when you retreat too far.
- `python3 squirrel-fight/game.py` is unchanged from before this plan.
