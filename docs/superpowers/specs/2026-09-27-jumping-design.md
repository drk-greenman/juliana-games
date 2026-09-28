# Squirrel Fight — Leaping Between Trees

Adds jumping and falling to the window version. Squirrels push off a trunk, arc through
the air steering as they go, and catch the next tree along. Gravity applies only once
you have jumped; climbing itself is unchanged.

This extends **sub-project 4 (climbing)**, which shipped with gravity, falling and jumping
explicitly out of scope. Sub-project 2 (several backgrounds) is specced and planned but
not built, and the ground props from 3 remain undone.

## Why

Climbing gave squirrels height but nowhere to go with it: up a trunk you are stuck there
until you climb back down, because horizontal movement is locked while off the ground.
Trees are destinations with no route between them. Jumping turns five isolated poles into
a route through the world.

## The reach problem, and what it decided

The first thing to check was whether a jump can actually cross the gap between trees. At
the current ~500px spacing it cannot — even with floaty gravity, nearly double walking
speed in the air and a launch from full climb height, the best reach is about 440px.

So **trees move closer: 230px apart, eleven of them** instead of five at ~500.

230 is not a round number chosen for looks. The two fighters start 460px apart, and 460 is
exactly two spacings — so **both start at a trunk**, and climbing is available to each of
them on turn one. At 290px spacing the player would start at a tree and the rival would
not, which is a small unfairness baked into every battle.

### The numbers, and the rule that falls out of them

| | Value |
| --- | --- |
| `JUMP_SPEED` | 380 px/sec upward |
| `GRAVITY` | 950 px/sec² |
| `AIR_SPEED` | 260 px/sec sideways, against 220 walking |

| Launched from | Hang time | Horizontal reach | |
| --- | --- | --- | --- |
| the ground | 0.80s | 208px | **falls short** of the 230px gap by 22px |
| a full climb (240) | 1.22s | 316px | **clears it** by 86px |

Both figures are from simulating the actual 16ms steps rather than the continuous
formula. An earlier `AIR_SPEED` of 280 put the ground jump at 224 against a 230 gap — a
6px margin, too fine to survive discrete stepping, and a rule that fragile is one bad
frame away from behaving differently than it reads.

That gap between 224 and 230 is deliberate and worth protecting: **you can only leap from
tree to tree if you jump from up a tree.** A jump from the ground is a hop that doesn't
quite make it. Nobody has to be told this — it teaches itself the first time someone tries
it from the ground and lands in the dirt.

Reach of 340 also cannot clear *two* gaps (460px), so you travel one tree at a time.

These three numbers are tightly coupled to the 230 spacing. Changing one means rechecking
the table, and the spec calls for a test that asserts both rows so the property cannot be
tuned away by accident.

## How jumping works

**Space jumps.** Up and Down are already climbing, so the jump needs its own key. It works
from the ground and from a trunk.

**Gravity applies only once airborne.** On a trunk you are gripping it and stay put whether
or not a key is held, exactly as today. Jumping is how you leave. This keeps the climbing
that already works and makes the whole rule explainable in one sentence: *grip unless you
jump.*

**Left and Right steer you in the air** at `AIR_SPEED`. This is the only time horizontal
movement is faster than walking, and it is what makes a leap feel like a leap rather than
a fall.

**You catch a trunk you pass near while descending.** Catching restores the grip at
whatever height you are, and gravity switches off. Without this tree-to-tree is impossible —
you would sail past everything.

Catching requires **descending**, not merely being near a trunk. Otherwise launching
sideways off a tree would re-grab the same trunk on the way up and nobody would ever leave.
Jumping straight up from a trunk correctly lands you back on it.

**Landing is free.** Drop from any height and you simply arrive. No fall damage, which
keeps `battle.py` the only thing in the game that can change a squirrel's HP.

## Mid-air turns need no new rule

If a move is chosen while airborne, `update()` already skips all movement during the
`animating` state — so the squirrel hangs in the air, the turn resolves, and the fall
resumes when the animation ends. Straight-line distance already handles fighting from
mid-air.

This is worth stating precisely because it is the kind of thing that looks like it needs
designing and does not. It falls out of the existing architecture.

## The rival

Its wander gains a jump whim alongside the walking and climbing ones, taken at random when
it is somewhere it could jump from. It stays untactical: it will fling itself off a trunk
for no reason and land somewhere useless.

While airborne its horizontal drift uses the same steering as the player's, so it arcs
rather than dropping straight down.

## What this costs

With eleven trees at 230px, a squirrel on the ground is within `CLIMB_REACH` of a trunk
about half the time. "Walk to a tree" therefore stops being much of a decision — it used
to be a real detour. That is the price of leaping being possible at all, and it is a real
loss, not a neutral change.

## How it fits the code

`battle.py`, `choreography.py`, `moves.py` and `game.py` are **not modified** — a sixth
consecutive feature for `game.py`. Nothing here changes what a move does, only where a
squirrel is when it does it.

### `arena.py`

- `TREES` regenerated at 230 spacing; `TREE_SPACING` named so the relationship to the
  reach table is visible.
- `JUMP_SPEED`, `GRAVITY`, `AIR_SPEED` beside the other tunables.
- A `Flight` record holding whether a squirrel is airborne and its vertical speed.
- `launch()` starts a jump; `step_flight()` advances one, applying gravity, steering,
  landing and trunk-catching, and reusing `clamp_walk` so the world and leash still bind
  in the air.
- The rival's `Wander` gains a jump whim.

### `visual_game.py`

`player_flight`/`rival_flight` beside the existing positions; Space handled in `_walk`;
and the three movement modes separated — airborne steers, gripping climbs, grounded walks.

## Testing

- **`test_arena.py`**: a launch leaves the ground; gravity brings a jump back down and
  lands it at exactly 0; a descending squirrel near a trunk catches it; an *ascending* one
  does not; steering in the air still respects the world edges and the leash.
- **`test_arena.py`, the property**: a ground jump falls short of `TREE_SPACING` and a jump
  from `MAX_CLIMB` clears it. This encodes the design rule so retuning any of the three
  numbers without rechecking the others fails the suite.
- **`test_arena.py`, the rival**: its jump whim only fires where it could actually jump,
  and over many steps it always ends up either grounded or gripping — never left airborne
  forever.
- **`test_visual_game.py`**: a battle draws with a squirrel mid-air; taking a turn while
  airborne resolves and then the fall continues.

The existing 146 tests must keep passing, with only `TREES`-dependent tests updated for
the new spacing.

## Out of scope

- Fall damage, or any HP change outside a resolved turn.
- Double jumps, wall jumps, or gliding.
- Jumping over the other squirrel — `MIN_GAP` still applies at similar heights.
- Branches to land on. Trunks remain bare poles.
- A tactical rival. The jump whim is random like the rest.
- Several backgrounds (specced, planned, unbuilt) and ground props.
