# Squirrel Fight — Somewhere Else To Fight

Lets the arena be several different places. Each battle deals three scenes across the
three-screen world, so walking takes you from one place into another instead of past the
same picture three times. Presentation only — no rules change.

This is **sub-project 2 of 4**. Sub-projects 1 (wide world) and 4 (climbing) are built;
the ground props from 3 — bush, log, mud — remain undone and are deliberately not
designed here.

## Why

The world is three screens wide and the single `background.png` is tiled across all
three, so the same trunk goes past every 960 pixels. It reads as wallpaper rather than
somewhere. The world is also identical every battle.

Both fall out of the same limitation: `sprites.load_background()` loads exactly one file.

## Three places per fight

The world is exactly three tiles of 960. Each battle fills those three slots with scenes
picked at random from whatever has been drawn, **sampled without replacement** when there
are enough — so you get three different places, and a different three next battle.

With fewer scenes than slots it repeats to fill. With exactly one it behaves precisely as
today, which means this ships without changing anything visible until a second scene is
drawn.

**This feature is worth nothing without art.** The code is small; the value is entirely
in someone drawing two or three places. That is the real dependency, and it is worth
being honest that shipping this alone changes nothing on screen.

## Scenes are files named by place

`assets/background-forest.png`, `assets/background-snow.png`,
`assets/background-burrow.png` — the same convention the squirrels already use, where the
filename is the content.

The existing `assets/background.png` stays valid as an unnamed scene, so current art keeps
working and nothing has to be renamed.

## Seams are accepted, not engineered around

Where two scenes meet there is a visible join. This design does not blend them, constrain
their edges, or generate transition strips.

The existing arena drawing is a *frame* — trunks down both sides, dirt above and below —
so its edges already hide a cut. The README will note that scenes with darker or busier
left and right edges butt together best. Blending would be real machinery to solve a
problem that good art avoids for free, and a wrong-looking seam is a prompt to redraw an
edge rather than a reason to write code.

## The bug this uncovers

`available_squirrels()` decides who can be a fighter by globbing `assets/*.png` and
skipping a hardcoded set: the stem `"background"`, anything starting `player_`/`rival_`,
and anything containing `_`.

That rule is already wrong, and this feature would make it worse:

- **`tree.png` is offered as a fighter.** Climbing added `sprites.load_tree()`, which
  reads `assets/tree.png` when it exists. Nothing bites today because the trunk is
  code-drawn — but the moment a tree is drawn, a tree trunk becomes a squirrel that can
  be dealt as the player's borrowed art. This is a live latent bug on main.
- **`background-forest.png` would be offered too**, since its stem is neither exactly
  `"background"` nor contains an underscore.

Both are the same root cause: the exclusion list is a hardcoded special case that nobody
updates when a new kind of asset arrives. The fix is to reserve by prefix as well as by
exact stem:

```python
RESERVED_STEMS = {"background", "tree"}
RESERVED_PREFIXES = ("player_", "rival_", "background-")
```

and — more importantly — to give it a test that fails when a new non-squirrel asset is
added without being reserved, so the next person to add one finds out from the suite
rather than from a tree turning up in a duel.

## How it fits the code

Presentation only. `arena.py`, `battle.py`, `choreography.py`, `moves.py` and `game.py`
are **not modified** — `game.py` for the fifth consecutive feature.

### `sprites.py`

- `available_backgrounds()` returns the stems of every scene: `background` if it exists,
  plus every `background-*`. Name matching, pure enough to test properly like `slug()`.
- `load_background(stem)` takes which scene to load, replacing the no-argument version.
  Caching stays keyed per stem.
- `RESERVED_STEMS` / `RESERVED_PREFIXES` as above, fixing the fighter-list bug.

### `visual_game.py`

`start_battle` picks the three stems and stores them; `_draw_stage` blits the scene for
each tile rather than the same one. The tiling loop already computes which tile it is
drawing, so this is choosing from a list rather than new structure.

## Testing

- **`test_sprites.py`**: `available_backgrounds()` finds `background.png` and
  `background-*.png`, ignores squirrels and `tree.png`, and returns empty when there is
  no art at all; `load_background()` returns a surface for a named scene and `None` for a
  missing one.
- **`test_sprites.py`, the bug**: `available_squirrels()` does **not** offer `tree` or
  `background-forest` as fighters — the test that would have caught tonight's latent bug.
- **`test_visual_game.py`**: a battle picks three scene slots and draws without crashing
  with one scene available and with several.

The existing 146 tests must keep passing.

## Out of scope

- Blending, cross-fading or generated transitions between scenes.
- Scenes wider than one tile, or a per-scene tile count.
- Scenes affecting play — no snow that slows you down. Presentation only.
- Choosing a scene deliberately, or tying scenes to particular rivals. Random only.
- Parallax. The background still scrolls 1:1 with the world.
- Ground props — bush, log, mud (the rest of sub-project 3).
