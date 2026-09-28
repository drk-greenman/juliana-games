# Several Backgrounds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deal three different scenes across the three-screen world each battle, instead of tiling one picture three times.

**Architecture:** Presentation only. `sprites.py` learns to find and load scenes by name; `visual_game.py` picks three at the start of a battle and draws the right one per tile. Task 1 first fixes a live bug the new filenames would otherwise double.

**Tech Stack:** Python 3.9 (system interpreter, no venv), pygame-ce, pytest.

**Spec:** `docs/superpowers/specs/2026-09-26-backgrounds-design.md`

---

## File Structure

| File | Responsibility |
| --- | --- |
| `squirrel-fight/sprites.py` | **Modify.** Reserve non-squirrel assets properly; `available_backgrounds()`; `load_background(stem)`. |
| `squirrel-fight/test_sprites.py` | **Modify.** The bug regression test, plus scene discovery. |
| `squirrel-fight/visual_game.py` | **Modify.** Pick three scenes per battle; draw per tile. |
| `squirrel-fight/test_visual_game.py` | **Modify.** Smoke coverage for the new draw path. |
| `squirrel-fight/README.md` | **Modify.** How to add a scene; the seam advice. |

**Not modified:** `arena.py`, `battle.py`, `choreography.py`, `moves.py`, `game.py`. This
changes what is drawn, not what happens. If a task needs to edit one of these, stop and
report it.

**Keep the suite green** — every task updates its callers in the same task.
Baseline: **146 tests passing.** All commands run from the repo root.

---

## Task 1: Stop non-squirrel art turning up in duels

A live bug: `available_squirrels()` currently offers `tree` as a fighter, so the moment
`assets/tree.png` is drawn a tree trunk becomes selectable as the player's borrowed art.
Fixing it first, on its own, because it is worth having even if the rest of this plan is
never built.

**Files:**
- Modify: `squirrel-fight/sprites.py:43-46`, `:113-118`
- Test: `squirrel-fight/test_sprites.py`

- [ ] **Step 1: Write the failing test**

Append to `squirrel-fight/test_sprites.py`:

```python
def test_only_squirrels_are_offered_as_fighters(tmp_path, monkeypatch):
    """Non-squirrel art must never be dealt as a fighter.

    `tree.png` really was offered before this test existed — a drawn tree would
    have turned up in a duel as the player's borrowed squirrel. When a new kind
    of asset is added, reserve it here and this test will say so.
    """
    import sprites

    for name in ("john-cena.png", "big-bumboy.png", "background.png",
                 "background-forest.png", "tree.png",
                 "player_idle.png", "john-cena_hurt.png"):
        (tmp_path / name).touch()
    monkeypatch.setattr(sprites, "ASSETS_DIR", tmp_path)

    assert sprites.available_squirrels() == {"john-cena", "big-bumboy"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_sprites.py -q`
Expected: FAIL — the returned set also contains `tree` and `background-forest`.

- [ ] **Step 3: Reserve by prefix as well as by exact name**

In `squirrel-fight/sprites.py`, replace lines 43-46:

```python
# Stems in `assets/` that name something other than an individual squirrel, so
# `available_squirrels()` doesn't offer them as fighters. Anything new that is
# art but not a squirrel belongs here — `tree.png` was missed once already, and
# a drawn tree would have turned up in a duel.
RESERVED_STEMS = {"background", "tree"}
RESERVED_PREFIXES = ("player_", "rival_", "background-")
```

and in `available_squirrels`, change the skip line to use the renamed constant:

```python
        if stem in RESERVED_STEMS or stem.startswith(RESERVED_PREFIXES) or "_" in stem:
```

Also update that function's docstring, which currently says only "the background":

```python
def available_squirrels() -> set:
    """The stems of every individual squirrel drawing in `assets/`.

    Skips anything reserved — backgrounds, the tree, and the generic
    `player_*`/`rival_*` art — and skips pose files like `john-cena_hurt.png`. A
    squirrel is offered here only if it has a plain `<name>.png` to stand
    around in.
    """
```

- [ ] **Step 4: Verify and commit**

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS, 147 tests.

```bash
git add squirrel-fight/sprites.py squirrel-fight/test_sprites.py
git commit -m "Stop trees and backgrounds being dealt as squirrels"
```

---

## Task 2: Find and load scenes by name

**Files:**
- Modify: `squirrel-fight/sprites.py`, `squirrel-fight/visual_game.py`
- Test: `squirrel-fight/test_sprites.py`

- [ ] **Step 1: Write the failing test**

Append to `squirrel-fight/test_sprites.py`:

```python
def test_available_backgrounds_finds_every_scene(tmp_path, monkeypatch):
    import sprites

    for name in ("background.png", "background-forest.png", "background-snow.png",
                 "john-cena.png", "tree.png"):
        (tmp_path / name).touch()
    monkeypatch.setattr(sprites, "ASSETS_DIR", tmp_path)

    assert sprites.available_backgrounds() == [
        "background", "background-forest", "background-snow"]


def test_available_backgrounds_copes_with_no_art(tmp_path, monkeypatch):
    import sprites

    monkeypatch.setattr(sprites, "ASSETS_DIR", tmp_path)
    assert sprites.available_backgrounds() == []


def test_a_missing_scene_loads_as_nothing(tmp_path, monkeypatch):
    import sprites

    monkeypatch.setattr(sprites, "ASSETS_DIR", tmp_path)
    sprites.clear_cache()
    assert sprites.load_background("background-nowhere") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest squirrel-fight/test_sprites.py -q`
Expected: FAIL with `AttributeError: module 'sprites' has no attribute 'available_backgrounds'`

- [ ] **Step 3: Write the implementation**

In `squirrel-fight/sprites.py`, add before `load_background`:

```python
def available_backgrounds() -> list:
    """The stems of every scene drawing in `assets/`, in a stable order.

    A scene is `background.png` or any `background-<place>.png`. Sorted rather
    than a set so that a given pick is reproducible for a given seed.
    """
    found = []
    if not ASSETS_DIR.is_dir():
        return found
    for path in sorted(ASSETS_DIR.glob("*.png")):
        stem = path.stem
        if stem == "background" or stem.startswith("background-"):
            found.append(stem)
    return found
```

and replace `load_background` with a version that takes which scene:

```python
def load_background(stem: str = "background") -> pygame.Surface | None:
    """Return one scene scaled to the stage, or None if it isn't there.

    None means "nothing drawn yet", which the caller answers with its own sky
    and grass — so this is the one loader with no placeholder of its own.
    """
    if stem not in _background_cache:
        path = ASSETS_DIR / "{}.png".format(stem)
        surface = None
        if path.is_file():
            try:
                surface = pygame.transform.scale(
                    pygame.image.load(str(path)).convert(), STAGE_SIZE
                )
                if BACKGROUND_KEY_COLOR is not None:
                    # Safe to key after scaling because scale() is
                    # nearest-neighbour: it copies colours rather than blending
                    # them, so no almost-white pixels appear along the edges.
                    surface.set_colorkey(BACKGROUND_KEY_COLOR)
            except (pygame.error, OSError):
                surface = None
        _background_cache[stem] = surface
    return _background_cache[stem]
```

- [ ] **Step 4: Verify and commit**

`visual_game` still calls `load_background()` with no argument, which now defaults to
`"background"` — exactly its old behaviour, so nothing breaks yet.

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS, 150 tests.

```bash
git add squirrel-fight/sprites.py squirrel-fight/test_sprites.py
git commit -m "Find and load background scenes by name"
```

---

## Task 3: Three places per battle

**Files:**
- Modify: `squirrel-fight/visual_game.py`
- Test: `squirrel-fight/test_visual_game.py`

- [ ] **Step 1: Import what's needed and add the picker**

In `squirrel-fight/visual_game.py`, extend the sprites import:

```python
from sprites import (
    available_backgrounds, available_squirrels, load_background, load_pose,
    load_tree, slug, STAGE_SIZE,
)
```

and add beside `pick_player_art`:

```python
# The world is a whole number of screens wide, and each scene covers one screen.
SCENE_SLOTS = arena.WORLD_WIDTH // STAGE_SIZE[0]


def pick_scenes(count=SCENE_SLOTS):
    """Deal `count` scenes for the world, in the order they'll be walked past.

    Sampled without replacement where there is enough art, so a battle takes you
    through different places rather than the same one repeatedly. With fewer
    scenes than slots it repeats to fill, and with exactly one it behaves the way
    a single tiled background always did.
    """
    scenes = available_backgrounds()
    if not scenes:
        return []
    if len(scenes) >= count:
        return random.sample(scenes, count)
    return [random.choice(scenes) for _ in range(count)]
```

- [ ] **Step 2: Deal them at the start of each battle**

In `Game.__init__`, beside the other per-battle state:

```python
        self.scenes = pick_scenes()
```

and the same line in `start_battle`, just before `self.state = "battle"`, so every
rematch gets a fresh set of places.

- [ ] **Step 3: Draw the right scene per tile**

In `_draw_stage`, replace the background block with:

```python
        if self.scenes:
            # One scene per screen-width slot, so walking the world takes you
            # from one place into another instead of past the same picture.
            tile_width = STAGE_SIZE[0]
            left = int(camera // tile_width) * tile_width
            while left < camera + WINDOW_SIZE[0]:
                scene = load_background(self.scenes[int(left // tile_width) % len(self.scenes)])
                if scene is not None:
                    self.screen.blit(scene, (left - camera, STAGE_TOP))
                left += tile_width
```

The `% len(self.scenes)` matters: the camera clamps inside the world, but a slot index
should never be able to run off the end of the list.

- [ ] **Step 4: Add smoke coverage**

Append to `squirrel-fight/test_visual_game.py`:

```python
def test_a_battle_deals_a_scene_for_every_slot(game):
    assert len(game.scenes) == visual_game.SCENE_SLOTS


def test_drawing_works_with_several_scenes(game, monkeypatch):
    # Patch the name ON visual_game, not on sprites: visual_game does
    # `from sprites import available_backgrounds`, so it holds its own
    # reference and patching sprites would quietly do nothing.
    #
    # Three names, only one of which is a file that exists: the other two load
    # as None, which the draw path has to survive rather than crash on.
    monkeypatch.setattr(visual_game, "available_backgrounds",
                        lambda: ["background", "background-nowhere", "background-else"])
    game.scenes = visual_game.pick_scenes()
    assert len(game.scenes) == visual_game.SCENE_SLOTS
    game.draw()


def test_drawing_works_with_no_scenes_at_all(game, monkeypatch):
    monkeypatch.setattr(visual_game, "available_backgrounds", lambda: [])
    game.scenes = visual_game.pick_scenes()
    assert game.scenes == []
    game.draw()
```

- [ ] **Step 5: Verify**

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS, 153 tests.

Run: `python3 squirrel-fight/visual_game.py`
Expected: identical to before, because there is still only one scene drawn — which is the
point. Walk the full width to confirm nothing flickers or gaps at the tile joins.

- [ ] **Step 6: Commit**

```bash
git add squirrel-fight/visual_game.py squirrel-fight/test_visual_game.py
git commit -m "Deal three scenes across the world each battle"
```

---

## Task 4: Say how to add a place

**Files:**
- Modify: `squirrel-fight/README.md`

- [ ] **Step 1: Document scenes**

In `squirrel-fight/README.md`, in "Drawing your own terrain", after the existing bullets,
add:

```markdown
### More than one place

Name extra scenes `background-<place>.png` — `background-forest.png`,
`background-snow.png`, `background-burrow.png` — and they're found automatically. Plain
`background.png` still counts as one.

Each battle deals **three** of them across the world, so walking takes you from one place
into another, and the next fight deals a different three. With only one scene it looks
exactly as it always has, so nothing changes until there's a second.

Where two scenes meet there's a join. Nothing blends them, so scenes with darker or busier
left and right edges butt together most neatly — which the tree-trunk edges of the
original arena already do. If a seam looks wrong, redraw the edge rather than worrying
about the code.
```

- [ ] **Step 2: Verify and commit**

Run: `python3 -m pytest squirrel-fight/ -q`
Expected: PASS.

```bash
git add squirrel-fight/README.md
git commit -m "Document how to add more places to fight in"
```

---

## Done when

- `python3 -m pytest squirrel-fight/ -q` is green, and was after every task.
- `available_squirrels()` no longer offers `tree` or `background-*`, with a test that
  fails if a future asset type is added without being reserved.
- `python3 squirrel-fight/visual_game.py` looks unchanged with one scene, and shows three
  different places once two more are drawn.
- `git diff --stat -- squirrel-fight/arena.py squirrel-fight/battle.py squirrel-fight/choreography.py squirrel-fight/moves.py squirrel-fight/game.py`
  shows no changes from this plan.
