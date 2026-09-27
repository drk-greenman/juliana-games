# Squirrel Fight — Up a Tree

Gives squirrels height. Trees stand at fixed spots across the wide world, squirrels climb
them freely, and range becomes straight-line distance so the rules we already have absorb
the new dimension without changing. The terminal version (`game.py`) stays untouched.

This is **sub-project 4 of 4**, taken out of order at request. Sub-project 2 (several
backgrounds) and the ground-level half of sub-project 3 (bush, log, mud) remain undone.
Because nothing in the world is climbable yet, this spec absorbs the slice of 3 that
climbing actually needs — trees — and nothing more.

## Why

The wide world gave squirrels somewhere to walk. It is still a corridor: one line, no
landmarks, and nothing to do with the space except pace it. Trees give the world features
worth walking *to*, and height turns range into something you can change two ways instead
of one.

## Making room comes first

Climbing cannot be built on the current layout. The stage band is 240px tall and squirrels
are 128–184px, so a standing squirrel's head already sits about 50px below the ceiling.
Lifting one by its own height would put its head outside the stage entirely.

So the stage grows to **440px** and everything below it shifts down by exactly 200. This
is a pure layout change with no new behaviour, and should land and be verified on its own
before any climbing exists.

| | Now | After |
| --- | --- | --- |
| `WINDOW_SIZE` | 960×640 | 960×840 |
| `STAGE_TOP` | 92 | 92 (unchanged) |
| `GROUND_Y` | 316 | 516 |
| `STAGE_BOTTOM` / `MESSAGE_TOP` | 332 | 532 |
| `BUTTON_ROWS` tops | 408, 456, 520, 584 | 608, 656, 720, 784 |
| `GROUP_LABELS` tops | 388, 500, 564 | 588, 700, 764 |

The bottom margin is preserved: buttons currently end at 626 of 640, and afterwards end at
826 of 840.

### `MAX_CLIMB` is 240, and the number is forced

Feet are planted at `GROUND_Y + 10` = 526. The tallest squirrel (Big Bumboy, 184px) at full
climb has its feet at 286 and its head at **102**, against a stage ceiling of 92. Ten pixels
of margin. This is not a tuning knob like the others — raise it and ears start leaving the
stage. If squirrel art ever gets taller, this has to come down.

Because height is capped this tightly, **the camera never needs to scroll vertically**: a
climbed squirrel is always fully visible.

## Climbing

Trees stand at fixed world positions. Get within `CLIMB_REACH` of a trunk and Up/Down
climbs it continuously — no levels, no snapping.

**While off the ground, Left and Right do nothing.** The squirrel is gripping a trunk;
climb down to move. This is the one deliberate trade of squirrel-realism for simplicity,
and it earns a lot: no gravity, no falling, no collision, and no question about what
happens if a turn resolves while someone is mid-air. Free climbing without it drags a
platformer engine in behind it.

A squirrel that is off the ground is therefore always at a tree, so "can I climb?" is
simply "is there a trunk within reach of my x?"

## Range becomes straight-line distance

This is what lets free climbing work without touching the fight rules. `gap()` stops
meaning horizontal distance and starts meaning true distance:

```
gap = √(dx² + dy²)
```

The three bands, the dimmed buttons and the whiff messages are all unchanged. Climbing
simply becomes a second way to change range: go up a tree while a rival stands below and
you slide out of `close` and into `mid`, turning your melee off and your acorns on.

**`battle.py`, `choreography.py` and `moves.py` are not modified by this spec.** Two
dimensions still collapse to one band string, so the rules module never learns that height
exists. If climbing had required changes there, the abstraction would be leaking — that is
the test of whether this idea is right.

### The leash stays horizontal

The mutual leash exists to keep both squirrels on a screen that only scrolls sideways.
Height is already capped by `MAX_CLIMB` and always visible, so the leash keeps measuring
horizontal distance only. Making it 2D would mean climbing a tree could drag the other
squirrel sideways, which is nonsense.

Note the consequence: two squirrels at the same x, one at full climb, are 240 apart in the
`close` band — so climbing alone cannot take you out of melee range, but climbing plus a
little walking can.

## Passing underneath

`MIN_GAP` applies **only when the two squirrels are at similar heights** — within
`CLIMB_CLEARANCE` of each other. Further apart vertically than that and they ignore each
other horizontally, so you can walk right under a squirrel that is up a tree, and out the
other side.

### Squirrels can now cross

This retires the invariant the walking code was built on. Until now neither squirrel could
pass the other, so the player was permanently the left fighter and the rival the right, and
`clamp_player`/`clamp_rival` each clamped to a fixed side. With overlap that is no longer
true: walk under an occupied tree and you come out on the far side.

The two side-specific clamps are therefore replaced by one side-agnostic
`clamp_walk(x, other_x, other_y, my_y)` which, in order:

1. clamps to the world, `[WALK_LEFT, WALK_RIGHT]`
2. clamps to the leash, `[other_x - LEASH, other_x + LEASH]`
3. applies `MIN_GAP` **only if** `abs(my_y - other_y) < CLIMB_CLEARANCE`, pushing to
   whichever side of `other_x` it is already nearer

### Landing on someone

When a descending squirrel comes down to within `CLIMB_CLEARANCE` of a grounded one that is
within `MIN_GAP` horizontally, **the grounded one is shoved aside** to exactly `MIN_GAP`
away. The descender always lands; nobody gets stuck up a tree.

Two edges this has to survive, both resolved rather than left open:

- **A shove against a world edge.** The shoved squirrel goes to whichever side it is
  already nearer; if that would put it outside `[WALK_LEFT, WALK_RIGHT]`, it goes to the
  other side instead. The walkable world is 2600px against a 170px `MIN_GAP`, so there is
  always room on at least one side.
- **A shove that would break the leash.** It cannot. The shove leaves the two exactly
  `MIN_GAP` = 170 apart, which is well inside the 700 leash, so a shove always ends closer
  than it started.

**The shove only applies to a squirrel that is on the ground.** If the one in the way is
itself up a trunk, it is not shoved — shoving it sideways would leave it gripping thin air,
breaking the rule that anything off the ground is at a tree. In that case the descent is
blocked instead, and the descender waits. Since trees are 500px apart and `MIN_GAP` is 170,
this only arises when both squirrels are on the same trunk.

## The rival

Its random wander gains a vertical whim: when it is near a trunk it may start going up or
down for a random stretch, exactly as it already picks horizontal directions. It stays
untactical — it will strand itself halfway up a tree, out of range of everything, and
shriek at nothing.

The same grip rule binds it: **while off the ground the rival's horizontal wander is
suppressed.** Without that it would drift sideways off its trunk and hang in the air.

## Numbers

| Thing | Value | Why |
| --- | --- | --- |
| `TREES` | 420, 960, 1440, 1980, 2480 | Five across the 2880 world, all inside the walk band. The one at 1440 sits between the opening positions, so a tree is on screen from turn one. |
| `CLIMB_REACH` | 60 | How near a trunk you must be to start climbing. |
| `MAX_CLIMB` | 240 | Forced by the stage ceiling — see above. |
| `CLIMB_SPEED` | 160 px/sec | A little slower than the 220 walking speed; going up should feel like effort. |
| `RIVAL_CLIMB_SPEED` | 70 px/sec | Slower than the player, matching the existing walk-speed relationship. |
| `CLIMB_MIN_MS` / `CLIMB_MAX_MS` | 300 / 900 | How long a vertical whim lasts, mirroring the horizontal wander timings. |
| `CLIMB_CLEARANCE` | 60 | Height difference above which two squirrels stop bumping into each other and can pass. Also the height a descending squirrel must get within before it shoves. |

## How it fits the code

### `arena.py`

Positions become `(x, y)` where `y` is height above the ground and 0 is standing on it.

- `gap()` takes four coordinates and returns straight-line distance; `band()` and
  `reaches()` follow it.
- `tree_near(x)` returns the trunk within `CLIMB_REACH`, or `None`.
- `climb(y, direction, dt_ms, speed)` clamps to `[0, MAX_CLIMB]`.
- `Wander` gains `climb_direction` and `climb_remaining_ms`; `step_wander` returns
  `(x, y, wander)` and suppresses horizontal drift whenever `y > 0`.
- `clamp_player()` and `clamp_rival()` are **replaced** by one side-agnostic
  `clamp_walk(x, other_x, other_y, my_y)`, since squirrels can now cross.
- `shove(grounded_x, lander_x)` returns where a shoved squirrel ends up, handling the
  world-edge fallback.
- `camera_x()` keeps taking x only.

Still no pygame.

### `visual_game.py`

The layout shift; `player_y`/`rival_y` alongside the existing x's; Up/Down (and W/S) in
`_walk`, with Left/Right ignored when `y > 0`; trunks drawn behind the squirrels; and
squirrels drawn at `GROUND_Y + 10 - y`.

### `sprites.py`

`load_tree()`, following the established pattern: a code-drawn trunk so the game works with
no art at all, replaced by `assets/tree.png` if one is drawn. `STAGE_SIZE` changes from
(960, 240) to (960, 440).

### The terrain template needs redoing

`STAGE_SIZE` changing from 960×240 to 960×440 moves the background's aspect ratio from
**4:1 to roughly 2.2:1**. The template committed earlier (`source-art/background-template.png`,
240×60) and the README's "draw it 4:1" advice both become wrong. The template is regenerated
at **240×110** with the ground line at row 106 and the feet line at row 108, and the README
updated to match.

This is the cost of taking sub-project 4 before 2: anything drawn against the old template
will need redoing. Nothing has been drawn against it yet, so the cost is currently zero —
but it would not have been if we had done backgrounds first.

## Testing

- **`test_arena.py`**: straight-line gap including a pure-vertical case; bands across
  combinations of horizontal and vertical separation; `climb` clamping at 0 and `MAX_CLIMB`;
  `tree_near` hitting and missing; the rival's vertical wander staying in range; the rival
  not drifting horizontally while off the ground; and an arithmetic test that
  `MAX_CLIMB` + the tallest sprite still fits under `STAGE_TOP`, so the constraint is
  guarded rather than just documented.
- **`test_arena.py`, overlap and shoving**: squirrels passing each other freely when more
  than `CLIMB_CLEARANCE` apart vertically and bumping when not; a squirrel ending up on the
  far side after walking under an occupied tree; `clamp_walk` still honouring the world and
  the leash in both directions now that sides are not fixed; a shove landing exactly
  `MIN_GAP` away; a shove against `WALK_LEFT` going the other way instead of leaving the
  world; and a descent onto a squirrel that is itself climbing being blocked rather than
  shoving it off its trunk.
- **`test_sprites.py`**: `load_tree()` returns a surface with no art present.
- The existing 112 tests must keep passing, with only the `gap`/`band`/`reaches` call sites
  updated for their new signatures.

## Out of scope

- Gravity, falling, jumping, or walking off a trunk.
- Height changing anything beyond straight-line distance — no high-ground damage bonus, no
  attacks that work only downward.
- A vertical camera. `MAX_CLIMB` makes it unnecessary.
- A tactical rival. The vertical wander is random, like the horizontal one.
- Several backgrounds (sub-project 2) and ground props — bush, log, mud (the rest of
  sub-project 3).
- Trees doing anything except being climbable. They do not block movement or attacks.
