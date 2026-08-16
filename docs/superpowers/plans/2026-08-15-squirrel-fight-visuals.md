# Squirrel Fight Visual Version Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pygame window version of Squirrel Fight with hand-drawn squirrels that lunge, stagger, flash and heal as each turn resolves, leaving the existing terminal version untouched.

**Architecture:** Three new modules beside the existing ones. `choreography.py` is pure Python with no pygame import — it turns the `TurnResult` that `resolve_turn()` already returns into a timeline of timed cues, exactly as `game.py`'s `format_turn_result_lines()` turns the same object into text. `sprites.py` loads PNGs from `assets/` and falls back to a code-drawn squirrel when a file is missing, so the game runs before any art exists. `visual_game.py` is the pygame shell: window, input, and drawing whatever `choreography.sample()` reports for the current millisecond. `battle.py` and `moves.py` are shared verbatim and never modified.

**Tech Stack:** Python 3.9.6 (system python at `/usr/bin/python3`), pygame-ce, pytest 8.4.2.

**Design spec:** `docs/superpowers/specs/2026-08-15-squirrel-fight-visuals-design.md`

---

## Critical environment constraints

Read these before writing any code. Getting them wrong causes failures that look mysterious.

1. **Python is 3.9.6, not 3.10+.** The `X | None` union syntax is a syntax error at runtime on 3.9 unless the module starts with `from __future__ import annotations`. Every new module in this plan starts with that line, the same way `battle.py` and `moves.py` already do. (`list[str]` and `dict[str, int]` are fine on 3.9 without it, but the future import makes both safe.)
2. **No `match` statements, no `tomllib`, no PEP 604 at runtime.** 3.9 only.
3. **Run everything with `python3`,** not `python`. There is no `python` on the PATH.
4. **Tests import modules as top-level names** (`import battle`, not `from squirrel_fight import battle`). There is no `__init__.py` in `squirrel-fight/`, and pytest inserts the test file's own directory onto `sys.path`. This is how `test_battle.py` already works — follow it exactly.
5. **The project folder has a hyphen** (`squirrel-fight`), so it can never be a Python package. Do not add one.

## File structure

| File | Status | Responsibility |
| --- | --- | --- |
| `squirrel-fight/moves.py` | unchanged | The 12 moves as data |
| `squirrel-fight/battle.py` | unchanged | Pure turn resolution |
| `squirrel-fight/game.py` | unchanged | Terminal version, plus `RIVAL_NAMES` which the window version imports |
| `squirrel-fight/test_battle.py` | unchanged | Existing battle tests, must keep passing |
| `squirrel-fight/requirements.txt` | create | pygame-ce only |
| `squirrel-fight/sprites.py` | create | Load `assets/*.png`, fall back to a code-drawn squirrel |
| `squirrel-fight/choreography.py` | create | Pure: `TurnResult` → animation timeline. No pygame import. |
| `squirrel-fight/test_choreography.py` | create | Tests for the timeline |
| `squirrel-fight/visual_game.py` | create | pygame window: main loop, input, drawing |
| `squirrel-fight/assets/` | create | Hand-drawn PNGs (empty at first) |
| `squirrel-fight/README.md` | modify | Document the second way to run it |

**Task order note.** The design spec's step 2 ("art loads") is built here as Task 2, *before* the window, rather than after it. This follows the spec's own stated principle — "no step gets rewritten by a later one" — because building `sprites.py` first means the window never needs a throwaway inline placeholder that gets deleted one task later. The capability milestones the spec describes are unchanged.

---

### Task 1: Add the pygame dependency

**Files:**
- Create: `squirrel-fight/requirements.txt`

- [ ] **Step 1: Create the project-level requirements file**

The root `requirements.txt` stays as it is. `CLAUDE.md` names pygame as exactly the case for a per-project requirements file, so `word-combo-story` does not inherit a graphics library it never uses.

`squirrel-fight/requirements.txt`:

```
pygame-ce>=2.4
```

`pygame-ce` is the maintained community fork. It is imported as `import pygame`, identically to upstream pygame — no code differences anywhere in this plan.

- [ ] **Step 2: Install it**

Run: `python3 -m pip install -r squirrel-fight/requirements.txt`

Expected: ends with `Successfully installed pygame-ce-2.x.x`. Packages land in `~/Library/Python/3.9/lib/python/site-packages/`, the same place pytest already lives. A `pip` version warning is normal and harmless.

- [ ] **Step 3: Verify pygame imports and can open a window**

Run: `python3 -c "import pygame; pygame.init(); s = pygame.display.set_mode((320, 200)); print('pygame ok', pygame.version.ver); pygame.quit()"`

Expected: a small window flickers open and closes, and stdout shows `pygame ok 2.x.x`. If this fails with `pygame.error: No available video device`, the machine has no display and only the terminal version can run.

- [ ] **Step 4: Commit**

```bash
git add squirrel-fight/requirements.txt
git commit -m "Add pygame-ce as a squirrel-fight-only dependency"
```

---

### Task 2: `sprites.py` — art loading with a code-drawn fallback

**Files:**
- Create: `squirrel-fight/sprites.py`
- Create: `squirrel-fight/assets/.gitkeep`

There are no automated tests for this module. It is pygame I/O, and this repo tests logic rather than I/O — the same reason `game.py` has no tests. Step 4 is a manual verification instead.

- [ ] **Step 1: Create the assets folder**

```bash
mkdir -p squirrel-fight/assets
touch squirrel-fight/assets/.gitkeep
```

The `.gitkeep` file exists only so the empty folder survives a git checkout. Delete it once real PNGs live there.

- [ ] **Step 2: Write `squirrel-fight/sprites.py`**

```python
from __future__ import annotations

from pathlib import Path

import pygame

ASSETS_DIR = Path(__file__).parent / "assets"
SPRITE_SIZE = (200, 200)

# Body colours for the code-drawn stand-in squirrels, so the two fighters are
# still tellable apart before any real art exists.
PLACEHOLDER_COLORS = {
    "player": (168, 106, 58),
    "rival": (116, 116, 132),
}

_cache: dict = {}


def load_pose(actor: str, pose: str) -> pygame.Surface:
    """Return the drawing for `actor` in `pose`, facing right.

    Falls back to the actor's `idle` drawing, and then to a code-drawn
    placeholder, so a missing or unreadable file is never fatal. Results are
    cached, so the placeholder is drawn once rather than every frame.
    """
    key = (actor, pose)
    if key not in _cache:
        surface = _load_file(actor, pose)
        if surface is None and pose != "idle":
            surface = _load_file(actor, "idle")
        if surface is None:
            surface = _draw_placeholder(actor)
        _cache[key] = surface
    return _cache[key]


def clear_cache() -> None:
    """Forget every loaded drawing. Only needed if assets change while running."""
    _cache.clear()


def _load_file(actor: str, pose: str):
    path = ASSETS_DIR / "{}_{}.png".format(actor, pose)
    if not path.is_file():
        return None
    try:
        image = pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        # Corrupt or unreadable file. Treat it exactly like a missing one.
        return None
    return pygame.transform.smoothscale(image, SPRITE_SIZE)


def _draw_placeholder(actor: str) -> pygame.Surface:
    """A simple squirrel built from ellipses and circles, facing right."""
    surface = pygame.Surface(SPRITE_SIZE, pygame.SRCALPHA)
    body = PLACEHOLDER_COLORS.get(actor, (150, 150, 150))
    dark = tuple(max(0, channel - 38) for channel in body)

    pygame.draw.ellipse(surface, dark, (6, 28, 84, 146))          # bushy tail
    pygame.draw.ellipse(surface, body, (66, 78, 96, 104))         # body
    pygame.draw.polygon(surface, dark, [(124, 46), (134, 10), (152, 44)])   # near ear
    pygame.draw.polygon(surface, dark, [(158, 44), (174, 12), (182, 48)])   # far ear
    pygame.draw.circle(surface, body, (152, 74), 40)              # head
    pygame.draw.circle(surface, (24, 24, 24), (166, 66), 6)       # eye
    pygame.draw.circle(surface, (24, 24, 24), (188, 74), 5)       # nose
    return surface
```

- [ ] **Step 3: Verify the placeholder renders**

Save this throwaway script to the scratch path and run it — it is not committed.

```bash
cat > /tmp/sprite_check.py <<'PY'
import sys
sys.path.insert(0, "squirrel-fight")
import pygame
from sprites import load_pose

pygame.init()
screen = pygame.display.set_mode((440, 240))
screen.fill((150, 200, 230))
screen.blit(load_pose("player", "idle"), (10, 20))
screen.blit(pygame.transform.flip(load_pose("rival", "idle"), True, False), (230, 20))
pygame.display.flip()
pygame.time.wait(2500)
pygame.quit()
PY
python3 /tmp/sprite_check.py
```

Expected: a window shows two squirrel shapes for 2.5 seconds — a brown one on the left facing right, a grey one on the right facing left. Both should read as "some kind of rodent": bushy tail, round head, two ears, an eye. If a shape looks wrong, adjust the coordinates in `_draw_placeholder` and re-run before moving on.

- [ ] **Step 4: Verify the missing-file path does not raise**

Run: `python3 -c "
import sys; sys.path.insert(0, 'squirrel-fight')
import pygame; pygame.init(); pygame.display.set_mode((10, 10))
from sprites import load_pose
print('missing pose ok:', load_pose('player', 'nonexistent').get_size())
pygame.quit()"`

Expected: `missing pose ok: (200, 200)` with no traceback.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/sprites.py squirrel-fight/assets/.gitkeep
git commit -m "Add sprite loading with a code-drawn squirrel fallback"
```

---

### Task 3: `choreography.py` — types and a neutral `sample()`

**Files:**
- Create: `squirrel-fight/choreography.py`
- Test: `squirrel-fight/test_choreography.py`

This module imports **no pygame**. Keeping it pure is what makes it testable.

- [ ] **Step 1: Write the failing test**

`squirrel-fight/test_choreography.py`:

```python
from choreography import PLAYER, RIVAL, ActorState, Timeline, sample


def test_empty_timeline_samples_neutral():
    timeline = Timeline(hp_start={PLAYER: 60, RIVAL: 60}, total_ms=0)
    frame = sample(timeline, 0)
    assert frame.actors[PLAYER] == ActorState()
    assert frame.actors[RIVAL] == ActorState()
    assert frame.hp == {PLAYER: 60, RIVAL: 60}
    assert frame.caption == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_choreography.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'choreography'`

- [ ] **Step 3: Write the module**

`squirrel-fight/choreography.py`:

```python
"""Turns a resolved turn into a timeline of timed animation cues.

This is to animation what `game.py`'s `format_turn_result_lines()` is to text:
both take the `TurnResult` that `battle.resolve_turn()` returns and turn it into
presentation. Nothing here imports pygame, so it is pure and testable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

PLAYER = "player"
RIVAL = "rival"
ACTORS = (PLAYER, RIVAL)

# +1 faces right, -1 faces left. Used to mirror every effect for the rival.
FACING = {PLAYER: 1, RIVAL: -1}


@dataclass(frozen=True)
class ActorState:
    """Where one squirrel is and what it looks like at a single instant."""

    offset_x: float = 0.0
    offset_y: float = 0.0
    rotation: float = 0.0
    scale: float = 1.0
    tint: float = 0.0    # red "just got hit" flash, 0..1
    glow: float = 0.0    # green "healing" glow, 0..1
    alpha: float = 1.0


@dataclass(frozen=True)
class Cue:
    start_ms: int
    duration_ms: int
    actor: str
    effect: str          # lunge | stagger | flash | hop | brace | glow | faint


@dataclass(frozen=True)
class HpTween:
    actor: str
    start_ms: int
    duration_ms: int
    hp_from: int
    hp_to: int


@dataclass(frozen=True)
class Timeline:
    cues: list = field(default_factory=list)
    captions: list = field(default_factory=list)     # (start_ms, text)
    hp_tweens: list = field(default_factory=list)
    hp_start: dict = field(default_factory=dict)
    total_ms: int = 0


@dataclass(frozen=True)
class FrameState:
    """Everything the renderer needs for one frame, from one `sample()` call."""

    actors: dict
    hp: dict
    caption: str


def sample(timeline: Timeline, t_ms: int) -> FrameState:
    actors = {actor: ActorState() for actor in ACTORS}
    for cue in timeline.cues:
        end_ms = cue.start_ms + cue.duration_ms
        if not (cue.start_ms <= t_ms <= end_ms):
            continue
        elapsed_ms = t_ms - cue.start_ms
        if cue.duration_ms <= 0:
            progress = 1.0
        else:
            progress = min(1.0, max(0.0, elapsed_ms / cue.duration_ms))
        actors[cue.actor] = _compose(
            actors[cue.actor],
            _effect_state(cue.effect, progress, elapsed_ms, FACING[cue.actor]),
        )

    hp = dict(timeline.hp_start)
    for tween in timeline.hp_tweens:
        if t_ms >= tween.start_ms + tween.duration_ms:
            hp[tween.actor] = tween.hp_to
        elif t_ms > tween.start_ms:
            progress = (t_ms - tween.start_ms) / tween.duration_ms
            hp[tween.actor] = round(tween.hp_from + (tween.hp_to - tween.hp_from) * progress)

    caption = ""
    for start_ms, text in timeline.captions:
        if t_ms >= start_ms:
            caption = text

    return FrameState(actors=actors, hp=hp, caption=caption)


def _compose(base: ActorState, extra: ActorState) -> ActorState:
    """Two cues on the same squirrel at the same moment stack."""
    return ActorState(
        offset_x=base.offset_x + extra.offset_x,
        offset_y=base.offset_y + extra.offset_y,
        rotation=base.rotation + extra.rotation,
        scale=base.scale * extra.scale,
        tint=max(base.tint, extra.tint),
        glow=max(base.glow, extra.glow),
        alpha=min(base.alpha, extra.alpha),
    )


def _effect_state(effect: str, progress: float, elapsed_ms: int, facing: int) -> ActorState:
    return ActorState()
```

`_effect_state` is deliberately a stub returning neutral. Task 4 fills it in.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest squirrel-fight/test_choreography.py -v`
Expected: PASS — 1 passed

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/choreography.py squirrel-fight/test_choreography.py
git commit -m "Add choreography timeline types and neutral sampling"
```

---

### Task 4: The seven visual effects

**Files:**
- Modify: `squirrel-fight/choreography.py` (replace the `_effect_state` stub, add the two easing helpers)
- Test: `squirrel-fight/test_choreography.py`

Every effect must return a neutral `ActorState` at `progress == 0`, except `flash`, which is an instant hit that fades. That rule is what makes "nothing has moved at the start of a cue" true, and it is asserted below.

- [ ] **Step 1: Write the failing tests**

First extend the import block at the top of `squirrel-fight/test_choreography.py` — keep all imports together at the top rather than letting them accumulate mid-file:

```python
import pytest

from choreography import PLAYER, RIVAL, ActorState, Cue, Timeline, _effect_state, sample
```

Then append the tests:

```python
@pytest.mark.parametrize("effect", ["lunge", "stagger", "hop", "brace", "glow", "faint"])
def test_effects_start_neutral(effect):
    assert _effect_state(effect, 0.0, 0, 1) == ActorState()


def test_lunge_moves_player_right_and_rival_left():
    forward = _effect_state("lunge", 0.5, 350, 1)
    backward = _effect_state("lunge", 0.5, 350, -1)
    assert forward.offset_x > 0
    assert backward.offset_x == -forward.offset_x


def test_lunge_returns_home_at_the_end():
    assert _effect_state("lunge", 1.0, 700, 1).offset_x == pytest.approx(0.0, abs=1e-9)


def test_flash_is_brightest_immediately_and_fades_out():
    assert _effect_state("flash", 0.0, 0, 1).tint == 1.0
    assert _effect_state("flash", 1.0, 220, 1).tint == 0.0


def test_hop_lifts_the_dodger_off_the_ground():
    assert _effect_state("hop", 0.5, 160, 1).offset_y < 0


def test_brace_crouches_without_leaving_the_ground():
    braced = _effect_state("brace", 0.5, 200, 1)
    assert braced.scale < 1.0
    assert braced.offset_y == 0.0


def test_faint_topples_and_fades():
    down = _effect_state("faint", 1.0, 500, 1)
    assert abs(down.rotation) == 90.0
    assert down.alpha < 1.0


def test_faint_holds_its_final_pose_long_after_the_cue_started():
    # The faint cue is stretched to the end of the timeline so the squirrel stays
    # down, but the topple itself must still finish quickly.
    late = _effect_state("faint", 0.2, 4000, 1)
    assert abs(late.rotation) == 90.0


def test_two_cues_on_one_squirrel_stack():
    timeline = Timeline(
        cues=[Cue(0, 200, RIVAL, "stagger"), Cue(0, 200, RIVAL, "flash")],
        hp_start={PLAYER: 60, RIVAL: 60},
        total_ms=200,
    )
    frame = sample(timeline, 100)
    assert frame.actors[RIVAL].tint > 0
    assert frame.actors[RIVAL].offset_x != 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest squirrel-fight/test_choreography.py -v`
Expected: FAIL — the effect tests fail because `_effect_state` returns `ActorState()` for everything (e.g. `assert forward.offset_x > 0` gets `0.0 > 0`). `test_effects_start_neutral` and `test_empty_timeline_samples_neutral` already pass.

- [ ] **Step 3: Add the timing constants and easing helpers**

Insert into `squirrel-fight/choreography.py`, just below the `FACING` definition:

```python
# All timings in milliseconds.
ACTION_MS = 700      # how long one fighter's action window lasts
GAP_MS = 120         # pause between the two fighters' windows
IMPACT_MS = 260      # when a lunge connects, measured from its window start
DODGE_MS = 180       # when a dodger starts moving, measured from the window start
STAGGER_MS = 340
FLASH_MS = 220
HOP_MS = 320
BRACE_MS = 400
GLOW_MS = 420
HP_MS = 340          # how long an HP bar takes to slide to its new value
FAINT_MS = 500       # how long the topple takes (the cue itself lasts longer)
TAIL_MS = 400        # dead air after the last cue so the last line can be read
```

- [ ] **Step 4: Replace the `_effect_state` stub**

Replace the stub in `squirrel-fight/choreography.py` with:

```python
def _arc(progress: float) -> float:
    """0 -> 1 -> 0, smoothly. Zero at both ends, so cues start and finish home."""
    return math.sin(math.pi * progress)


def _shudder(progress: float) -> float:
    """A quick wobble that dies away. Zero at progress 0."""
    return math.sin(progress * math.pi * 3.0) * (1.0 - progress)


def _effect_state(effect: str, progress: float, elapsed_ms: int, facing: int) -> ActorState:
    if effect == "lunge":
        swing = _arc(progress)
        return ActorState(offset_x=facing * 70.0 * swing, rotation=-facing * 12.0 * swing)
    if effect == "stagger":
        knock = _shudder(progress)
        return ActorState(offset_x=-facing * 26.0 * knock, rotation=facing * 9.0 * knock)
    if effect == "flash":
        # Instant on impact, then fades. This is the one effect that is loudest
        # at progress 0 rather than silent.
        return ActorState(tint=1.0 - progress)
    if effect == "hop":
        swing = _arc(progress)
        return ActorState(offset_x=-facing * 34.0 * swing, offset_y=-52.0 * swing)
    if effect == "brace":
        crouch = _arc(progress)
        return ActorState(offset_x=-facing * 12.0 * crouch, scale=1.0 - 0.09 * crouch)
    if effect == "glow":
        lift = _arc(progress)
        return ActorState(glow=lift, offset_y=-10.0 * lift)
    if effect == "faint":
        # Driven by absolute elapsed time, not progress: the cue is stretched to
        # the end of the timeline so the squirrel stays down, but the topple
        # itself always takes FAINT_MS.
        fallen = min(1.0, elapsed_ms / FAINT_MS)
        return ActorState(
            rotation=facing * 90.0 * fallen,
            offset_y=26.0 * fallen,
            alpha=1.0 - 0.45 * fallen,
        )
    return ActorState()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest squirrel-fight/test_choreography.py -v`
Expected: PASS — 15 passed (1 from Task 3, 6 parametrised neutrality cases, 8 behaviour cases)

- [ ] **Step 6: Commit**

```bash
git add squirrel-fight/choreography.py squirrel-fight/test_choreography.py
git commit -m "Add the seven squirrel animation effects"
```

---

### Task 5: `build_timeline()` — attack, dodge, block, heal, lifesteal

**Files:**
- Modify: `squirrel-fight/choreography.py`
- Test: `squirrel-fight/test_choreography.py`

- [ ] **Step 1: Write the failing tests**

Again, extend the import block at the top of `squirrel-fight/test_choreography.py` rather than importing mid-file. It should now read:

```python
import pytest

from battle import FighterTurnOutcome, TurnResult
from choreography import (
    ACTION_MS, GAP_MS, PLAYER, RIVAL, ActorState, Cue, Timeline,
    _effect_state, build_timeline, sample,
)
from moves import Move
```

Then append the helpers and tests:

```python
FULL_HP = {PLAYER: 60, RIVAL: 60}


def attack_move(name="Tail Smack", lifesteal=False):
    return Move(name=name, kind="attack", description="", dmg_range=(10, 13), lifesteal=lifesteal)


def dodge_move(name="Dance"):
    return Move(name=name, kind="defense", description="", dodge_chance=0.5)


def block_move(name="Flex"):
    return Move(name=name, kind="defense", description="", block_flat=36)


def heal_move(name="Eat Garden"):
    return Move(name=name, kind="heal", description="", heal_range=(12, 18))


def build(player_move, rival_move, result, hp_before=None, hp_after=None):
    hp_before = FULL_HP if hp_before is None else hp_before
    hp_after = hp_before if hp_after is None else hp_after
    return build_timeline(
        "Juliana", "JOHN CENA", player_move, rival_move, result, hp_before, hp_after, 60
    )


def effects_for(timeline, actor):
    return {cue.effect for cue in timeline.cues if cue.actor == actor}


def test_landed_attack_lunges_and_staggers_the_defender():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 60, RIVAL: 48})
    assert "lunge" in effects_for(timeline, PLAYER)
    assert "stagger" in effects_for(timeline, RIVAL)
    assert "flash" in effects_for(timeline, RIVAL)


def test_dodged_attack_hops_instead_of_flashing():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=0),
        fighter_b=FighterTurnOutcome(move_name="Dance", dodged=True),
    )
    timeline = build(attack_move(), dodge_move(), result)
    assert "hop" in effects_for(timeline, RIVAL)
    assert "flash" not in effects_for(timeline, RIVAL)


def test_fully_blocked_attack_braces_instead_of_flashing():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=0),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result)
    assert "brace" in effects_for(timeline, RIVAL)
    assert "flash" not in effects_for(timeline, RIVAL)
    assert "stagger" not in effects_for(timeline, RIVAL)


def test_heal_move_glows():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Eat Garden", healed=15),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(heal_move(), block_move(), result,
                     hp_before={PLAYER: 40, RIVAL: 60}, hp_after={PLAYER: 55, RIVAL: 60})
    assert "glow" in effects_for(timeline, PLAYER)


def test_lifesteal_both_hurts_the_rival_and_glows_the_thief():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Steal", damage_dealt=10, healed=5),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move("Steal", lifesteal=True), block_move(), result,
                     hp_before={PLAYER: 40, RIVAL: 60}, hp_after={PLAYER: 45, RIVAL: 50})
    assert "glow" in effects_for(timeline, PLAYER)
    assert "flash" in effects_for(timeline, RIVAL)


def test_the_rival_acts_after_the_player():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=9),
    )
    timeline = build(attack_move(), attack_move("Scratch"), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 51, RIVAL: 48})
    player_lunge = next(c for c in timeline.cues if c.actor == PLAYER and c.effect == "lunge")
    rival_lunge = next(c for c in timeline.cues if c.actor == RIVAL and c.effect == "lunge")
    assert player_lunge.start_ms == 0
    assert rival_lunge.start_ms == ACTION_MS + GAP_MS


def test_a_defender_facing_no_attack_still_braces_once():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Dance"),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
        flavor_text="Both squirrels eye each other warily, neither committing to a move.",
    )
    timeline = build(dodge_move(), block_move(), result)
    assert "brace" in effects_for(timeline, PLAYER)
    assert "brace" in effects_for(timeline, RIVAL)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest squirrel-fight/test_choreography.py -v`
Expected: FAIL — `ImportError: cannot import name 'build_timeline' from 'choreography'`

- [ ] **Step 3: Add `build_timeline` to `choreography.py`**

Append to `squirrel-fight/choreography.py`:

```python
def build_timeline(
    player_name,
    rival_name,
    player_move,
    rival_move,
    result,
    hp_before,
    hp_after,
    max_hp,
) -> Timeline:
    """Lay out one resolved turn as cues, captions and HP slides.

    `hp_before` and `hp_after` are `{PLAYER: int, RIVAL: int}`. The caller must
    capture `hp_before` *before* calling `battle.resolve_turn()`, which mutates
    `Fighter.hp` in place. Nothing here re-simulates the fight; it only shows a
    result that has already been computed. Both fighters share one `max_hp`.
    """
    names = {PLAYER: player_name, RIVAL: rival_name}
    moves = {PLAYER: player_move, RIVAL: rival_move}
    cues = []
    captions = []
    hp_events = {PLAYER: [], RIVAL: []}

    rival_start_ms = ACTION_MS + GAP_MS
    sides = (
        (PLAYER, RIVAL, result.fighter_a, result.fighter_b, 0),
        (RIVAL, PLAYER, result.fighter_b, result.fighter_a, rival_start_ms),
    )

    for actor, other, own, other_outcome, start_ms in sides:
        move = moves[actor]
        captions.append((start_ms, "{} uses {}!".format(names[actor], move.name)))

        if move.kind == "attack":
            cues.append(Cue(start_ms, ACTION_MS, actor, "lunge"))
            hit_ms = start_ms + IMPACT_MS
            if other_outcome.dodged:
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
            if move.lifesteal and own.healed > 0:
                cues.append(Cue(hit_ms, GLOW_MS, actor, "glow"))
                captions.append((hit_ms + 120, "{} steals {} HP!".format(
                    names[actor], own.healed)))
                hp_events[actor].append((hit_ms + 120, HP_MS, own.healed))

        elif move.kind == "defense":
            # If the other squirrel is attacking, this one already gets a hop or
            # brace as a reaction inside that attack's window. Only add a stance
            # of its own when there is no attack to react to.
            if moves[other].kind != "attack":
                cues.append(Cue(start_ms, BRACE_MS, actor, "brace"))

        elif move.kind == "heal":
            cues.append(Cue(start_ms, GLOW_MS, actor, "glow"))
            if own.healed > 0:
                captions.append((start_ms + 200, "{} heals {} HP!".format(
                    names[actor], own.healed)))
                hp_events[actor].append((start_ms + 200, HP_MS, own.healed))

    if result.flavor_text:
        captions.append((rival_start_ms + 350, result.flavor_text))

    hp_tweens = _build_hp_tweens(hp_events, hp_before, hp_after, max_hp)

    end_of_action_ms = rival_start_ms + ACTION_MS
    knocked_out = [actor for actor in ACTORS if hp_after[actor] <= 0]

    candidates = (
        [end_of_action_ms]
        + [cue.start_ms + cue.duration_ms for cue in cues]
        + [start for start, _ in captions]
        + [tween.start_ms + tween.duration_ms for tween in hp_tweens]
    )
    if knocked_out:
        # The timeline has to outlast the topple, or the faint cue gets cut off
        # part-way and the squirrel freezes at a half-fallen angle.
        candidates.append(end_of_action_ms + FAINT_MS)
    total_ms = max(candidates) + TAIL_MS

    for actor in knocked_out:
        # Stretched to the end of the timeline so the squirrel stays down.
        cues.append(Cue(end_of_action_ms, total_ms - end_of_action_ms, actor, "faint"))
        captions.append((end_of_action_ms + 120, "{} is down!".format(names[actor])))

    captions.sort(key=lambda caption: caption[0])
    return Timeline(
        cues=cues,
        captions=captions,
        hp_tweens=hp_tweens,
        hp_start=dict(hp_before),
        total_ms=total_ms,
    )


def _build_hp_tweens(hp_events, hp_before, hp_after, max_hp):
    """Chain each squirrel's HP changes so the last one lands exactly on `hp_after`.

    A squirrel can both heal and take damage in one turn (Eat Garden against an
    attack), so it can need two slides. `battle.py` clamps the *net* change, so
    intermediate values are clamped for display only and the final slide is
    pinned to the real post-turn HP rather than recomputed.
    """
    tweens = []
    for actor in ACTORS:
        events = sorted(hp_events[actor])
        current = hp_before[actor]
        for index, (start_ms, duration_ms, delta) in enumerate(events):
            is_last = index == len(events) - 1
            if is_last:
                target = hp_after[actor]
            else:
                target = max(0, min(max_hp, current + delta))
            if target != current:
                tweens.append(HpTween(actor, start_ms, duration_ms, current, target))
            current = target
    tweens.sort(key=lambda tween: tween.start_ms)
    return tweens
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest squirrel-fight/test_choreography.py -v`
Expected: PASS — 22 passed

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/choreography.py squirrel-fight/test_choreography.py
git commit -m "Build animation timelines from resolved turns"
```

---

### Task 6: Timeline HP slides, captions, faint and length

**Files:**
- Test: `squirrel-fight/test_choreography.py`

No production code changes — Task 5 implemented all of this. These tests pin the behaviour the spec calls out, and they will catch regressions in the trickiest parts (HP chaining and the stretched faint cue). If any fails, fix `choreography.py` rather than the test.

- [ ] **Step 1: Write the tests**

Append to `squirrel-fight/test_choreography.py`:

```python
def test_hp_slide_ends_on_the_real_post_turn_value():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 60, RIVAL: 48})
    assert sample(timeline, timeline.total_ms).hp == {PLAYER: 60, RIVAL: 48}


def test_hp_starts_at_the_pre_turn_value():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 60, RIVAL: 48})
    assert sample(timeline, 0).hp == {PLAYER: 60, RIVAL: 60}


def test_healing_and_taking_damage_in_one_turn_still_lands_exactly():
    # Eat Garden while the rival attacks: two slides for the player, and the
    # last one must land on the real post-turn HP.
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Eat Garden", healed=15),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=10),
    )
    timeline = build(heal_move(), attack_move("Scratch"), result,
                     hp_before={PLAYER: 55, RIVAL: 60}, hp_after={PLAYER: 60, RIVAL: 60})
    player_tweens = [tween for tween in timeline.hp_tweens if tween.actor == PLAYER]
    assert len(player_tweens) >= 1
    assert sample(timeline, timeline.total_ms).hp[PLAYER] == 60


def test_captions_are_ordered_and_sample_returns_the_most_recent():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=9),
    )
    timeline = build(attack_move(), attack_move("Scratch"), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 51, RIVAL: 48})
    starts = [start for start, _ in timeline.captions]
    assert starts == sorted(starts)
    assert sample(timeline, 0).caption == "Juliana uses Tail Smack!"
    assert "JOHN CENA" in sample(timeline, timeline.total_ms).caption


def test_total_ms_covers_every_cue():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=9),
    )
    timeline = build(attack_move(), attack_move("Scratch"), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 51, RIVAL: 48})
    assert timeline.total_ms >= max(c.start_ms + c.duration_ms for c in timeline.cues)


def test_a_knocked_out_squirrel_faints_and_stays_down():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before={PLAYER: 60, RIVAL: 12}, hp_after={PLAYER: 60, RIVAL: 0})
    assert "faint" in effects_for(timeline, RIVAL)
    assert abs(sample(timeline, timeline.total_ms).actors[RIVAL].rotation) == 90.0


def test_nobody_faints_while_both_are_standing():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 60, RIVAL: 48})
    assert "faint" not in effects_for(timeline, PLAYER)
    assert "faint" not in effects_for(timeline, RIVAL)
```

- [ ] **Step 2: Run the whole suite**

Run: `python3 -m pytest squirrel-fight/ -v`
Expected: PASS — every `test_choreography.py` test plus every existing `test_battle.py` test. `test_battle.py` must be untouched and still green.

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/test_choreography.py
git commit -m "Test timeline HP slides, captions, faint and length"
```

---

### Task 7: `visual_game.py` — window, title screen, and the battle layout

**Files:**
- Create: `squirrel-fight/visual_game.py`

This task gets a window on screen with a working title screen and a fully drawn (but not yet playable) battle screen. Task 8 makes the buttons do something.

- [ ] **Step 1: Write the module**

`squirrel-fight/visual_game.py`:

```python
"""The pygame window version of Squirrel Fight.

The text version in `game.py` still works and is unaffected. Both import the
same `battle.py` and `moves.py`, so the fight rules live in exactly one place.
"""

from __future__ import annotations

import random
import sys

try:
    import pygame
except ImportError:
    sys.exit(
        "\n  Squirrel Fight's window version needs pygame.\n\n"
        "  Install it with:\n"
        "    python3 -m pip install -r squirrel-fight/requirements.txt\n\n"
        "  Or play the text version instead:\n"
        "    python3 squirrel-fight/game.py\n"
    )

from battle import Fighter, battle_outcome, resolve_turn
from choreography import PLAYER, RIVAL, ActorState, build_timeline, sample
from game import RIVAL_NAMES
from moves import MOVES
from sprites import load_pose

WINDOW_SIZE = (960, 640)
FPS = 60
START_HP = 60

COLOR_BG = (32, 36, 46)
COLOR_PANEL = (22, 26, 34)
COLOR_TEXT = (201, 209, 217)
COLOR_DIM = (125, 133, 144)
COLOR_SKY = (168, 220, 240)
COLOR_GRASS = (124, 186, 96)
COLOR_TRACK = (12, 14, 18)
COLOR_HP_GOOD = (46, 160, 67)
COLOR_HP_BAD = (218, 54, 51)

# Matches the terminal version's red/cyan/green move categories.
KIND_STYLE = {
    "attack": {"fill": (74, 31, 31), "edge": (184, 67, 61), "text": (255, 180, 174)},
    "defense": {"fill": (18, 54, 66), "edge": (61, 151, 184), "text": (169, 228, 245)},
    "heal": {"fill": (21, 58, 34), "edge": (63, 163, 92), "text": (167, 232, 187)},
}

STAGE_TOP = 92
GROUND_Y = 316
STAGE_BOTTOM = 332
MESSAGE_TOP = 332
PLAYER_X = 250
RIVAL_X = 710

# (row top, first move index, last move index exclusive)
BUTTON_ROWS = ((408, 0, 4), (456, 4, 7), (520, 7, 11), (584, 11, 12))
GROUP_LABELS = ((388, "ATTACKS", "attack"), (500, "DEFENSES", "defense"), (564, "HEAL", "heal"))

# Moves 1-9 sit on the number row; 10, 11 and 12 continue onto 0, - and =.
SHORTCUT_KEYS = (
    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6,
    pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0, pygame.K_MINUS, pygame.K_EQUALS,
)


class Button:
    def __init__(self, rect, move, number):
        self.rect = rect
        self.move = move
        self.number = number


def build_buttons():
    margin, gap, height = 24, 10, 42
    width = (WINDOW_SIZE[0] - 2 * margin - 3 * gap) // 4
    buttons = []
    for top, first, last in BUTTON_ROWS:
        for column, index in enumerate(range(first, last)):
            left = margin + column * (width + gap)
            buttons.append(Button(pygame.Rect(left, top, width, height), MOVES[index], index + 1))
    return buttons


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("helveticaneue,helvetica,arial", 40, bold=True)
        self.font = pygame.font.SysFont("helveticaneue,helvetica,arial", 18)
        self.bold = pygame.font.SysFont("helveticaneue,helvetica,arial", 16, bold=True)
        self.label_font = pygame.font.SysFont("helveticaneue,helvetica,arial", 12, bold=True)
        self.buttons = build_buttons()

        self.running = True
        self.state = "title"
        self.typed_name = ""
        self.player = None
        self.rival = None
        self.message = ""
        self.timeline = None
        self.frame = None
        self.elapsed_ms = 0
        self.outcome = "ongoing"
        self.hover = None

    # ----- state changes -------------------------------------------------

    def start_battle(self):
        name = self.typed_name.strip() or "You"
        self.player = Fighter(name=name, hp=START_HP, max_hp=START_HP)
        self.rival = Fighter(name=random.choice(RIVAL_NAMES), hp=START_HP, max_hp=START_HP)
        self.message = "{} vs. {}! Let the fight begin!".format(self.player.name, self.rival.name)
        self.timeline = None
        self.frame = None
        self.elapsed_ms = 0
        self.outcome = "ongoing"
        self.hover = None
        self.state = "battle"

    # ----- input ---------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return
        if self.state == "title":
            self._handle_title(event)
        elif self.state == "battle":
            self._handle_battle(event)
        elif self.state == "result":
            self._handle_result(event)
        # "animating" ignores everything except quitting.

    def _handle_title(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.start_battle()
        elif event.key == pygame.K_BACKSPACE:
            self.typed_name = self.typed_name[:-1]
        elif event.unicode and event.unicode.isprintable() and len(self.typed_name) < 18:
            self.typed_name += event.unicode

    def _handle_battle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self._button_at(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            button = self._button_at(event.pos)
            if button is not None:
                self.take_turn(button.move)
        elif event.type == pygame.KEYDOWN and event.key in SHORTCUT_KEYS:
            self.take_turn(MOVES[SHORTCUT_KEYS.index(event.key)])

    def _handle_result(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.start_battle()

    def _button_at(self, position):
        for button in self.buttons:
            if button.rect.collidepoint(position):
                return button
        return None

    def take_turn(self, move):
        raise NotImplementedError("Task 8 wires this up")

    # ----- per-frame -----------------------------------------------------

    def update(self, dt_ms):
        pass

    def draw(self):
        if self.state == "title":
            self._draw_title()
        else:
            self._draw_battle()
            if self.state == "result":
                self._draw_result_overlay()

    # ----- drawing -------------------------------------------------------

    def _draw_title(self):
        self.screen.fill(COLOR_BG)
        self._centered(self.title_font, "SQUIRREL FIGHT", COLOR_TEXT, 150)
        self._centered(self.font, "Name your squirrel, then press Enter.", COLOR_DIM, 220)

        box = pygame.Rect(0, 0, 440, 56)
        box.center = (WINDOW_SIZE[0] // 2, 300)
        pygame.draw.rect(self.screen, COLOR_PANEL, box, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_DIM, box, width=2, border_radius=8)
        caret = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        typed = self.font.render(self.typed_name + caret, True, COLOR_TEXT)
        self.screen.blit(typed, (box.x + 16, box.centery - typed.get_height() // 2))

        self._centered(self.font, "Click a move, or use the number row: 1-9, then 0, - and =",
                       COLOR_DIM, 420)
        self._centered(self.font, "Esc quits at any time.", COLOR_DIM, 450)

    def _centered(self, font, text, color, top):
        surface = font.render(text, True, color)
        self.screen.blit(surface, (WINDOW_SIZE[0] // 2 - surface.get_width() // 2, top))

    def _draw_battle(self):
        self.screen.fill(COLOR_BG)
        self._draw_hp_panel()
        self._draw_stage()
        self._draw_message()
        self._draw_buttons()

    def _current_hp(self):
        if self.frame is not None:
            return self.frame.hp
        return {PLAYER: self.player.hp, RIVAL: self.rival.hp}

    def _draw_hp_panel(self):
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, WINDOW_SIZE[0], STAGE_TOP))
        hp = self._current_hp()
        self._draw_hp_bar(24, self.player.name, hp[PLAYER], COLOR_HP_GOOD, False)
        self._draw_hp_bar(WINDOW_SIZE[0] - 24 - 380, self.rival.name, hp[RIVAL],
                          COLOR_HP_BAD, True)

    def _draw_hp_bar(self, left, name, hp, color, right_aligned):
        width = 380
        label = self.bold.render(name, True, COLOR_TEXT)
        amount = self.font.render("{} / {}".format(max(0, hp), START_HP), True, COLOR_DIM)
        if right_aligned:
            self.screen.blit(label, (left + width - label.get_width(), 14))
            self.screen.blit(amount, (left + width - amount.get_width(), 62))
        else:
            self.screen.blit(label, (left, 14))
            self.screen.blit(amount, (left, 62))

        track = pygame.Rect(left, 40, width, 16)
        pygame.draw.rect(self.screen, COLOR_TRACK, track, border_radius=8)
        filled = int(width * max(0, min(START_HP, hp)) / START_HP)
        if filled > 0:
            fill = pygame.Rect(left + (width - filled if right_aligned else 0), 40, filled, 16)
            pygame.draw.rect(self.screen, color, fill, border_radius=8)

    def _draw_stage(self):
        pygame.draw.rect(self.screen, COLOR_SKY, (0, STAGE_TOP, WINDOW_SIZE[0], GROUND_Y - STAGE_TOP))
        pygame.draw.rect(self.screen, COLOR_GRASS, (0, GROUND_Y, WINDOW_SIZE[0], STAGE_BOTTOM - GROUND_Y))
        self._draw_squirrel(PLAYER, PLAYER_X)
        self._draw_squirrel(RIVAL, RIVAL_X)

    def _draw_squirrel(self, actor, center_x):
        state = self.frame.actors[actor] if self.frame is not None else ActorState()
        image = load_pose(actor, "idle")
        if actor == RIVAL:
            image = pygame.transform.flip(image, True, False)
        if state.scale != 1.0:
            size = (max(1, int(image.get_width() * state.scale)),
                    max(1, int(image.get_height() * state.scale)))
            image = pygame.transform.smoothscale(image, size)
        if state.rotation:
            image = pygame.transform.rotate(image, -state.rotation)
        if state.tint > 0 or state.glow > 0 or state.alpha < 1.0:
            # Copy first: never colour the cached surface that sprites.py hands back.
            image = image.copy()
            if state.tint > 0:
                image.fill((int(210 * state.tint), 0, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if state.glow > 0:
                image.fill((0, int(170 * state.glow), 50, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if state.alpha < 1.0:
                image.set_alpha(int(255 * state.alpha))
        rect = image.get_rect()
        rect.midbottom = (int(center_x + state.offset_x), int(GROUND_Y + 10 + state.offset_y))
        self.screen.blit(image, rect)

    def _message_text(self):
        if self.state == "animating" and self.frame is not None:
            return self.frame.caption
        if self.hover is not None:
            return "{} — {}".format(self.hover.move.name, self.hover.move.description)
        return self.message

    def _draw_message(self):
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, MESSAGE_TOP, WINDOW_SIZE[0], 52))
        text = self.font.render(self._message_text(), True, COLOR_TEXT)
        self.screen.blit(text, (24, MESSAGE_TOP + 26 - text.get_height() // 2))

    def _draw_buttons(self):
        dimmed = self.state != "battle"
        for top, caption, kind in GROUP_LABELS:
            label = self.label_font.render(caption, True, KIND_STYLE[kind]["text"])
            self.screen.blit(label, (24, top))
        for button in self.buttons:
            style = KIND_STYLE[button.move.kind]
            fill, edge, text_color = style["fill"], style["edge"], style["text"]
            if dimmed:
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

    def _draw_result_overlay(self):
        pass


def main():
    pygame.init()
    try:
        screen = pygame.display.set_mode(WINDOW_SIZE)
    except pygame.error:
        pygame.quit()
        sys.exit(
            "\n  No display available, so the window version can't run here.\n\n"
            "  Play the text version instead:\n"
            "    python3 squirrel-fight/game.py\n"
        )
    pygame.display.set_caption("Squirrel Fight")
    clock = pygame.time.Clock()
    game = Game(screen)
    while game.running:
        dt_ms = clock.tick(FPS)
        for event in pygame.event.get():
            game.handle_event(event)
        game.update(dt_ms)
        game.draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it and check the title screen**

Run: `python3 squirrel-fight/visual_game.py`

Expected: a 960×640 window titled "Squirrel Fight" showing the title, a text box with a blinking caret, and the keyboard hint. Typing letters fills the box; Backspace deletes. Pressing Enter switches to the battle screen: HP bars at 60/60, two squirrels on grass, the "let the fight begin" line, and 12 colour-coded buttons. Hovering a button shows its description in the message strip. Clicking one crashes with `NotImplementedError` — that is expected and Task 8 fixes it. Esc quits.

- [ ] **Step 3: Verify the existing tests are unaffected**

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS — same count as Task 6.

- [ ] **Step 4: Commit**

```bash
git add squirrel-fight/visual_game.py
git commit -m "Add pygame window with title screen and battle layout"
```

---

### Task 8: Wire up turns, the result screen, and playing again

**Files:**
- Modify: `squirrel-fight/visual_game.py` (`take_turn`, `update`, `_draw_result_overlay`)

At the end of this task the window is fully playable, with turns resolving instantly. Task 9 adds the motion.

- [ ] **Step 1: Replace `take_turn`**

Replace the `take_turn` stub in `squirrel-fight/visual_game.py` with:

```python
    def take_turn(self, move):
        rival_move = random.choice(MOVES)
        # resolve_turn() mutates Fighter.hp in place, so snapshot first.
        hp_before = {PLAYER: self.player.hp, RIVAL: self.rival.hp}
        result = resolve_turn(self.player, move, self.rival, rival_move)
        hp_after = {PLAYER: self.player.hp, RIVAL: self.rival.hp}
        self.timeline = build_timeline(
            self.player.name, self.rival.name, move, rival_move, result,
            hp_before, hp_after, self.player.max_hp,
        )
        self.elapsed_ms = 0
        self.frame = sample(self.timeline, 0)
        self.outcome = battle_outcome(self.player, self.rival)
        self.hover = None
        self.state = "animating"
```

- [ ] **Step 2: Replace `update`**

Replace the `update` stub with:

```python
    def update(self, dt_ms):
        if self.state != "animating":
            return
        self.elapsed_ms = min(self.elapsed_ms + dt_ms, self.timeline.total_ms)
        self.frame = sample(self.timeline, self.elapsed_ms)
        if self.elapsed_ms >= self.timeline.total_ms:
            self.message = self.frame.caption
            self.state = "result" if self.outcome != "ongoing" else "battle"
```

- [ ] **Step 3: Add the outcome text and the result overlay**

Replace the `_draw_result_overlay` stub with:

```python
    def _outcome_text(self):
        if self.outcome == "draw":
            return "Both squirrels are down! It's a draw!"
        if self.outcome == "a_wins":
            return "{} wins!".format(self.player.name)
        if self.outcome == "b_wins":
            return "{} wins!".format(self.rival.name)
        return ""

    def _draw_result_overlay(self):
        shade = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        self.screen.blit(shade, (0, 0))

        panel = pygame.Rect(0, 0, 560, 190)
        panel.center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_DIM, panel, width=2, border_radius=12)

        headline = self.title_font.render(self._outcome_text(), True, COLOR_TEXT)
        if headline.get_width() > panel.width - 40:
            headline = self.bold.render(self._outcome_text(), True, COLOR_TEXT)
        self.screen.blit(headline, headline.get_rect(center=(panel.centerx, panel.centery - 28)))

        prompt = self.font.render("Press Enter to play again, or Esc to quit.", True, COLOR_DIM)
        self.screen.blit(prompt, prompt.get_rect(center=(panel.centerx, panel.centery + 36)))
```

The `headline.get_width()` check exists because rival names like `Chompy Von Nutsalot` overflow the panel at 40pt; it drops to the smaller bold font rather than spilling over the edge.

- [ ] **Step 4: Play a full battle**

Run: `python3 squirrel-fight/visual_game.py`

Expected, in order:
1. Type a name, press Enter.
2. Click a move — the message strip shows what happened and an HP bar drops. The turn resolves and re-enables the buttons after about two seconds of dead air (no motion yet — that is Task 9).
3. Number keys `1`–`9`, `0`, `-` and `=` pick moves 1–12.
4. Keep going until someone hits 0 HP. The result overlay appears with the winner.
5. Enter starts a fresh battle against a newly chosen rival, with both fighters back at 60 HP.
6. Esc quits with no traceback.

Also verify closing the window with the red button exits cleanly.

- [ ] **Step 5: Commit**

```bash
git add squirrel-fight/visual_game.py
git commit -m "Make the window version fully playable"
```

---

### Task 9: Play the animation

**Files:**
- Modify: `squirrel-fight/visual_game.py`

The wiring from Task 8 already samples the timeline every frame and draws whatever it reports — the animation is genuinely already running. This task is a verification pass plus the one thing Task 8 left out: a hurt/attack pose swap hook is *not* added here (that is Task 11), but the timing needs checking against a real fight.

- [ ] **Step 1: Watch each outcome happen**

Run: `python3 squirrel-fight/visual_game.py`

Play until you have seen each of these, and confirm what you see:

| Do this | Expect to see |
| --- | --- |
| Pick `1 Tail Smack` | Your squirrel leans and lunges right, the rival jolts and flashes red, its HP bar slides down |
| Pick `11 Flex` repeatedly | When the rival attacks you, you crouch slightly instead of flashing |
| Pick `8 Dance` repeatedly | Sometimes you hop up and back and take no damage |
| Pick `12 Eat Garden` | You glow green and lift slightly; your HP bar slides up |
| Pick `7 Steal` | The rival flashes red *and* you glow green |
| Win a battle | The loser topples 90° and fades, and stays down behind the result overlay |

- [ ] **Step 2: Fix the timing if it drags**

The whole turn is `ACTION_MS + GAP_MS + ACTION_MS + TAIL_MS` = 1920 ms. If that feels slow in practice, lower `ACTION_MS` and `TAIL_MS` in `choreography.py` — nothing else depends on their absolute values, and `test_total_ms_covers_every_cue` will catch a change that breaks the arithmetic.

Run after any change: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS

- [ ] **Step 3: Commit any tuning**

```bash
git add squirrel-fight/choreography.py
git commit -m "Tune squirrel fight animation timing"
```

If nothing needed tuning, skip the commit and move on.

---

### Task 10: Document it

**Files:**
- Modify: `squirrel-fight/README.md`

- [ ] **Step 1: Rewrite the README**

Replace the contents of `squirrel-fight/README.md` with:

````markdown
# Squirrel Fight

A 1v1 squirrel duel. Name your squirrel, pick from 12 silly attack/defense/heal
moves each turn, and battle a randomly-named rival squirrel controlled by the
computer.

There are two ways to play the same fight.

## Play in the terminal

No extra installs, works anywhere:

```bash
python3 squirrel-fight/game.py
```

## Play in a window

Squirrels that lunge, stagger and flash, with clickable moves:

```bash
python3 -m pip install -r squirrel-fight/requirements.txt
python3 squirrel-fight/visual_game.py
```

Click a move, or use the number row — `1`–`9` for the first nine moves, then
`0`, `-` and `=` for moves 10, 11 and 12. Esc quits.

Neither version needs an API key. Both are fully offline.

## Drawing your own squirrels

The window version draws simple placeholder squirrels until you give it real
art. Drop PNG files into `squirrel-fight/assets/` and they show up next run —
no code changes needed.

Start with these two:

- `assets/player_idle.png`
- `assets/rival_idle.png`

Make them PNGs with a see-through background, roughly 200×200, with the
squirrel **facing right**. The rival gets flipped automatically, so both
drawings face the same way.

Once those work, these are all optional and each one replaces a placeholder:

| File | When it shows |
| --- | --- |
| `player_hurt.png`, `rival_hurt.png` | While getting hit |
| `player_attack.png`, `rival_attack.png` | While lunging |
| `background.png` | Instead of the plain sky and grass |

Any file you haven't drawn yet just falls back to the one you have, so you can
add them one at a time.

## Run the tests

```bash
python3 -m pytest squirrel-fight/
```

`test_battle.py` covers the fight maths and `test_choreography.py` covers the
animation timeline. The pygame drawing code has no tests — like `game.py`, it's
checked by playing it.

## How the code is split

| File | What it does |
| --- | --- |
| `moves.py` | The 12 moves, as data |
| `battle.py` | Turn resolution. Pure logic, no input or output |
| `game.py` | The terminal version |
| `visual_game.py` | The window version |
| `choreography.py` | Turns a resolved turn into animation. Pure, no pygame |
| `sprites.py` | Loads drawings, falls back to code-drawn squirrels |
````

- [ ] **Step 2: Verify every command in the README actually works**

```bash
python3 -m pytest squirrel-fight/ -q
python3 squirrel-fight/game.py </dev/null
```

Expected: tests pass. The second command starts the terminal game and exits when stdin closes — it must not raise a traceback before that.

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/README.md
git commit -m "Document both ways to play Squirrel Fight"
```

---

### Task 11: Pose swapping and a hand-drawn background

**Files:**
- Modify: `squirrel-fight/visual_game.py`

This is the spec's step 4. It is what makes `player_hurt.png` and `player_attack.png` mean something, and it needs no changes to `choreography.py` or `sprites.py` — both already support poses by name.

- [ ] **Step 1: Add pose selection to `_draw_squirrel`**

In `squirrel-fight/visual_game.py`, replace the first two lines of `_draw_squirrel`:

```python
    def _draw_squirrel(self, actor, center_x):
        state = self.frame.actors[actor] if self.frame is not None else ActorState()
        image = load_pose(actor, "idle")
```

with:

```python
    def _draw_squirrel(self, actor, center_x):
        state = self.frame.actors[actor] if self.frame is not None else ActorState()
        image = load_pose(actor, self._pose_for(actor))
```

- [ ] **Step 2: Add the `_pose_for` helper**

Add this method to `Game`, directly above `_draw_squirrel`:

```python
    def _pose_for(self, actor):
        """Pick a drawing by what the squirrel is currently doing.

        `sprites.load_pose` falls back to `idle` for any pose that has no PNG,
        so this is safe whether or not the extra drawings have been made yet.
        """
        if self.state not in ("animating", "result") or self.timeline is None:
            return "idle"
        active = {
            cue.effect
            for cue in self.timeline.cues
            if cue.actor == actor
            and cue.start_ms <= self.elapsed_ms <= cue.start_ms + cue.duration_ms
        }
        if "stagger" in active or "faint" in active:
            return "hurt"
        if "lunge" in active:
            return "attack"
        return "idle"
```

- [ ] **Step 3: Add background support to `_draw_stage`**

Replace the first two lines of `_draw_stage`:

```python
        pygame.draw.rect(self.screen, COLOR_SKY, (0, STAGE_TOP, WINDOW_SIZE[0], GROUND_Y - STAGE_TOP))
        pygame.draw.rect(self.screen, COLOR_GRASS, (0, GROUND_Y, WINDOW_SIZE[0], STAGE_BOTTOM - GROUND_Y))
```

with:

```python
        background = load_background()
        if background is None:
            pygame.draw.rect(self.screen, COLOR_SKY,
                             (0, STAGE_TOP, WINDOW_SIZE[0], GROUND_Y - STAGE_TOP))
            pygame.draw.rect(self.screen, COLOR_GRASS,
                             (0, GROUND_Y, WINDOW_SIZE[0], STAGE_BOTTOM - GROUND_Y))
        else:
            self.screen.blit(background, (0, STAGE_TOP))
```

- [ ] **Step 4: Add `load_background` to `sprites.py`**

Append to `squirrel-fight/sprites.py`:

```python
STAGE_SIZE = (960, 240)
_background_cache = {}


def load_background():
    """Return `assets/background.png` scaled to the stage, or None if there isn't one."""
    if "background" not in _background_cache:
        path = ASSETS_DIR / "background.png"
        surface = None
        if path.is_file():
            try:
                surface = pygame.transform.smoothscale(
                    pygame.image.load(str(path)).convert(), STAGE_SIZE
                )
            except pygame.error:
                surface = None
        _background_cache["background"] = surface
    return _background_cache["background"]
```

`convert()` rather than `convert_alpha()`: a backdrop fills the whole stage, so it needs no transparency and blits faster opaque.

- [ ] **Step 5: Import it in `visual_game.py`**

Change the import line:

```python
from sprites import load_pose
```

to:

```python
from sprites import load_background, load_pose
```

- [ ] **Step 6: Verify nothing changed with no art present**

Run: `python3 squirrel-fight/visual_game.py`

Expected: identical to Task 9 — placeholder squirrels on plain sky and grass, because every pose and the background all fall back. This is the important check: adding pose support must not break the no-art case.

- [ ] **Step 7: Verify a dropped-in drawing appears**

Generate a throwaway test PNG and confirm it loads:

```bash
python3 -c "
import sys; sys.path.insert(0, 'squirrel-fight')
import pygame
pygame.init(); pygame.display.set_mode((10, 10))
s = pygame.Surface((200, 200), pygame.SRCALPHA)
pygame.draw.circle(s, (255, 0, 255), (100, 100), 90)
pygame.image.save(s, 'squirrel-fight/assets/player_idle.png')
print('wrote a magenta test circle')
"
python3 squirrel-fight/visual_game.py
```

Expected: your squirrel is now a magenta circle; the rival is still the grey placeholder. That proves the drop-in path works end to end.

Then remove it so no test art gets committed:

```bash
rm squirrel-fight/assets/player_idle.png
```

- [ ] **Step 8: Run the full suite**

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add squirrel-fight/visual_game.py squirrel-fight/sprites.py
git commit -m "Swap poses during animation and support a drawn background"
```

---

### Task 12: Final check

**Files:** none

- [ ] **Step 1: Confirm the terminal version is genuinely untouched**

Run: `git diff --stat main -- squirrel-fight/game.py squirrel-fight/battle.py squirrel-fight/moves.py squirrel-fight/test_battle.py`

Expected: no output at all. Any output here means a shared file was modified, which the spec forbids — revert it.

- [ ] **Step 2: Run everything**

```bash
python3 -m pytest squirrel-fight/ -v
python3 squirrel-fight/game.py </dev/null
python3 squirrel-fight/visual_game.py
```

Expected: all tests pass, the terminal game still starts, and the window game plays a full battle through to a result and a rematch.

- [ ] **Step 3: Confirm nothing stray got committed**

Run: `git status --short`

Expected: clean, with no test PNGs left in `squirrel-fight/assets/`.

---

## Optional follow-up: a flying acorn for Acorn Blast

Not required for the feature to be complete. Recorded here so the idea isn't lost.

`Acorn Blast` is the one ranged attack among the seven, and it currently animates as a lunge like the rest. Giving it a projectile would mean adding a `"projectile"` effect to `choreography.py` (a cue on the *attacker* whose `ActorState` carries a separate `projectile_progress` field), drawing `assets/acorn.png` interpolated between the two squirrels in `_draw_squirrel`'s caller, and picking the effect in `build_timeline` when `move.name == "Acorn Blast"`. It touches the `ActorState` shape, which is why it is deliberately not folded into the tasks above.
