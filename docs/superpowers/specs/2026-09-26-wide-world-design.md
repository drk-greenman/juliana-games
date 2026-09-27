# Squirrel Fight — A World Worth Wandering

Widens the window version's stage from one screen to three, adds a camera that follows
the fight, and splits the range rule into three bands so backing away has a cost. The
terminal version (`game.py`) stays untouched.

This is **sub-project 1 of 4**. The others — several different backgrounds, terrain you
can use (bush, log, mud), and climbing — each get their own spec and are deliberately
not designed here. This one comes first because a bush or a branch needs somewhere to
be, and scenery painted for a 960px stage is the wrong shape once the world is wider.

## Why

Squirrels currently walk a single screen, from x140 to x820, in front of one background
stretched to fit. Walking is a real decision now, but there is nowhere to walk *to* —
the pair paces a small box. Making the world wider gives the wandering somewhere to
happen, and gives the later terrain work room to put things.

## The world and the camera

The world becomes **2880px wide** — exactly three windows — while the window stays 960.
Squirrels get world coordinates, and drawing subtracts a camera offset.

The camera sits **midway between the two squirrels**, clamped so it never scrolls past
either end of the world. It needs no state of its own and no smoothing: it is computed
fresh from the two positions every frame, and because the squirrels move smoothly, so
does it.

Neither squirrel can get more than **700px** from the other — a mutual leash. That number
falls out of the geometry rather than being picked: at a 700 gap each squirrel sits 350px
from the centre of the screen, plus roughly 125px of sprite, giving 475 — just inside the
480px half-window. The leash is exactly "as far apart as they can get while both stay
fully visible."

It has to bind **both** of them, not just the wandering rival. Leashing only the rival
would let the player walk to the world's edge with nothing pulling the rival after them,
and the guarantee that both stay on screen would break on the first turn someone decided
to run away.

The player feels this as a soft limit: walk far enough from the rival and you simply stop,
until its wandering drifts your way and gives you more rope. In practice the pair migrates
across the world together rather than either one touring it alone — which is the intent,
not a side effect.

So the wide world is **not extra fighting distance**. It is ground the pair roams across
together, which is what the request was actually about.

### It opens looking exactly like today

Starting positions are the world centre ± 230: player at 1210, rival at 1670. The gap is
460, the same as today. The camera therefore starts at 960, which puts the two squirrels
at screen x250 and x710 — the exact marks they stand on now. The game opens identical
and only reveals itself as wider once someone walks.

## Three range bands

| Gap | Band | What lands |
| --- | --- | --- |
| ≤ 300 | `close` | melee |
| 300–550 | `mid` | ranged |
| > 550 | `far` | nothing but defenses and Eat Garden |

The far band runs from 550 to the 700 leash. Backing off that far means your acorns drop
short, so retreating has a cost and holding the middle band is a real thing to do. Two
bands would have made "walk to the far edge and throw" the obviously best move once the
world got big.

Defenses and Eat Garden continue to work at any distance, so there is always something
useful to do wherever you are standing.

An attack used in the wrong band whiffs for no damage, as it does today, with a message
saying why:

| Move | Band | Message |
| --- | --- | --- |
| melee | `mid` or `far` | "*Nutsy* swipes at thin air — *Chompy* is too far away!" |
| ranged | `close` | "*Chompy* is far too close for Acorn Blast to land!" |
| ranged | `far` | "*Nutsy*'s Acorn Blast drops well short!" |

This applies to the rival too, which wanders at random and so does it to itself.

## Numbers

First-pass values, expected to be retuned after it's played. They join the existing
tunables at the top of `arena.py`.

| Thing | Value | Why |
| --- | --- | --- |
| `WORLD_WIDTH` | 2880 | Three windows. Wide enough to feel like somewhere, small enough not to feel empty. |
| `WALK_LEFT` / `WALK_RIGHT` | 140 / 2740 | The same 140px inset from each world edge as today. |
| `LEASH` | 700 | The furthest apart they can get with both fully on screen. |
| `CLOSE_RANGE` | 300 | Unchanged. |
| `LONG_RANGE` | 550 | Leaves a 150px far band inside the leash. |
| `PLAYER_START` / `RIVAL_START` | 1210 / 1670 | World centre ± 230, preserving today's 460 opening gap and screen positions. |
| `MIN_GAP`, speeds, wander timings | unchanged | |

## How it fits the code

The pure/I-O split holds: `arena.py`, `battle.py` and `choreography.py` stay free of
pygame and keep their tests.

### `arena.py`

Gains `WORLD_WIDTH`, `LEASH`, `LONG_RANGE`, the band names, and two functions:

- `band(player_x, rival_x)` returning `"close"`, `"mid"` or `"far"`
- `camera_x(player_x, rival_x)` returning the left edge of the view, centred between the
  fighters and clamped to `[0, WORLD_WIDTH - 960]`

**Both** `clamp_player` and `clamp_rival` enforce the leash, so neither squirrel can get
further than `LEASH` from the other. `reaches()` is rewritten in terms of `band()`.

### `battle.py`

`resolve_turn`'s `close: bool | None` parameter becomes `band: str | None`. `None`
still means "distance isn't part of the game", which is how `game.py` stays untouched —
it is never modified by this work.

`FighterTurnOutcome` gains `whiff_reason` (`"too_far"` or `"too_close"`, `None` when the
move landed) so the caption can explain itself without `choreography.py` learning any
geometry.

This is a breaking change to `resolve_turn`'s signature, and the seven tests added in the
previous sub-project that pass `close=True`/`close=False` must be migrated to `band=`.

### `choreography.py`

The existing whiff branch gains a third caption, chosen from `whiff_reason` together with
`move.reach` per the message table above.

### `visual_game.py`

Holds no camera state — it asks `arena.camera_x()` when drawing. Squirrel world
positions are converted to screen by subtracting it. Button dimming already goes through
`arena.reaches()`, so it picks up the three bands for free.

### `sprites.py` — no change needed

`load_background()` already returns a 960×240 surface, and the world is exactly three of
those wide, so `visual_game` simply blits it at each visible tile offset. Nothing in the
loader changes.

The honest weakness: `background.png` is a 64×36 arena *frame*, so tiling it repeats its
edges. It reads acceptably as a continuous burrow wall, but it is a stopgap — properly
wide scenery is the whole point of sub-project 2.

## Testing

- **`test_arena.py`**: band boundaries at and either side of 300 and 550; the leash
  holding in *both* directions — over many wander steps, and when the player walks hard
  away from a stationary rival; `camera_x` clamping at both world ends and centring in
  the middle; and that the starting positions put the squirrels at screen x250 and x710.
- **`test_battle.py`**: melee and ranged across all three bands, the far band whiffing
  everything, `whiff_reason` values, defenses and heals unaffected in every band, and
  `band=None` behaving exactly as before so the terminal version is provably unchanged.
- **`test_choreography.py`**: all three whiff captions.

The existing 100 tests must keep passing, with only the seven `close=` call sites
migrated.

## Out of scope

- Several different backgrounds (sub-project 2).
- Terrain that does something — bush, log, mud (sub-project 3).
- Climbing, jumping, and attacks between heights (sub-project 4).
- Parallax scrolling. The background tiles at 1:1 with the world.
- Vertical movement of any kind. Squirrels still walk one line.
- A tactical rival. The wander stays random, now leashed.
