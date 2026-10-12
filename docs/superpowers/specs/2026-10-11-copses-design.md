# Squirrel Fight — Copses Instead of a Grid

Replaces the eleven evenly-spaced trees with seven trees in three copses, separated by
clearings too wide for any jump to cross. Nothing about jumping, climbing or the range
bands changes; the only production edit is how `TREES` is built.

It closes the last of the six open questions listed in `docs/HANDOFF.md`. The same play
session also produced three bug reports, fixed separately in `fc712f5`, `1a6f78a` and
`b6ff85b` and recorded in the handoff — this is the *tuning* half of that feedback, and it
has to live alongside those fixes rather than in front of them.

## Why

Juliana played the window version on 2026-10-11 and answered the handoff's six tuning
questions. Five came back "leave it alone":

| Question | Answer |
| --- | --- |
| Is a ground hop so useless it's annoying? | Fine — reads as a little hop |
| Is chaining along the treetops too strong? | Fun and about right |
| Does the rival jumping make fights drag? | No — fights moved along fine |
| Does walking into the leash's stop feel broken? | Never noticed it |
| Does "drops well short" ever come up? | Saw it occasionally |

The sixth found a real problem: **eleven trees is too many — "walk to a tree" stopped
being a decision.** There was always a trunk within a step, so climbing was never
something you chose to go and do.

## Why the spacing cannot simply be widened

The obvious fix is a bigger `TREE_SPACING`. It is not available, for two reasons that only
became clear from measuring.

**The legal window is narrow.** The design rule is that a ground jump must *not* reach the
next trunk while a treetop jump must. Simulating the real 16ms steps:

| `TREE_SPACING` | Ground jump | Treetop jump | Trees |
| --- | --- | --- | --- |
| 230 | dirt | catches at **y=124** | 11 |
| 250 | dirt | catches at y=84 | 10 |
| 260 | dirt | catches at y=57 | 9 |
| 280 | dirt | catches at y=7 | 9 |
| 290 | dirt | **dirt** | 8 |

Note that caught-versus-dirt is the *wrong* thing to read off this table. At 280 the jump
still technically catches the trunk, 7px off the ground — a squirrel scrabbling onto the
base of a tree, not a leap between treetops. **Catch height is the quality signal**, which
puts the honest ceiling around 250 rather than 280.

**And the pitch is locked anyway.** Both fighters must start at a trunk — the original
spec's reason for 230, so that climbing is available to each of them on turn one. They
start 460px apart, so a uniform grid needs 460 to be a multiple of its pitch. The only
such pitch inside the legal window is **230: the value it already has.**

So widening the grid buys at most one fewer tree, and costs the fairness property. The
grid is at its sparsest possible setting already.

## The actual cause

A grid whose pitch is pinned to the jump distance is dense *everywhere* by construction.
"Trees are everywhere" is not the value of `TREE_SPACING` — it is the uniformity. Every
part of the world has to look like every other part, because the one spacing that makes
chaining work is also the only spacing allowed.

Breaking the uniformity is free. The jump rules care only about the distance between
*adjacent* trunks; they say nothing about trunks being evenly distributed.

## The design

Seven trees: two copses and a lone tree. Within a copse, trunks are `TREE_SPACING` apart
exactly as before. Between them there is a clearing of `3 * TREE_SPACING`.

Three spacings, not two, is a judgement about feel rather than safety — a 460px gap is
also too wide to jump, but it reads as "two trees got deleted", whereas 690 is most of a
screen width and reads as open ground. This was the choice between candidate layouts, and
the sparser one was picked deliberately.

```
|   T   T             P    T   R    T            T   |

left copse    290,  520
centre copse  1210, 1440, 1670, 1900      <- both fighters start here
lone tree     2590
clearings     690px, twice
```

The lone tree at 2590 is a climbable dead end: the nearest trunk is a clearing away, so
you can go up it but you cannot leap out of it. That is a different kind of place from a
copse, and it costs no rules — only the tuple.

The centre copse runs to 1900 rather than stopping at 1670, which is not a cosmetic
choice. See *What nearly broke this* below.

Every trunk still sits on the old grid — this is the grid with two of every five removed —
so `PLAYER_START` (1210) and `RIVAL_START` (1670) keep their trunks and no other geometry
moves.

In `arena.py`:

```python
TREE_SPACING = 230          # within a copse — the distance a treetop jump clears
CLEARING = 3 * TREE_SPACING # 690 — wider than any jump, so leaving a copse means walking

# Each copse is (leftmost trunk, how many trunks).
COPSES = ((290, 2), (1210, 4), (2590, 1))
TREES = tuple(first + i * TREE_SPACING
              for first, count in COPSES
              for i in range(count))
```

`CLEARING` is written as `3 * TREE_SPACING` rather than `690` so that the number it has to
beat stays visible next to it. The figure to beat is **285px** — the furthest a jump can
ever travel, measured as the 265px ballistic reach from `MAX_CLIMB` with nothing to catch,
plus the 20px `CATCH_REACH` that adds itself to every jump. At 690 the clearing clears
that by 405px, so it is not a marginal call.

`COPSES` spells out leftmost trunks rather than deriving them from `CLEARING`, because an
explicit list is easier to read and to retune. That makes `CLEARING` documentation unless
something checks it, so **the test asserts that every between-copse gap equals
`CLEARING`** — which is what stops the constant and the layout drifting apart.

## The rule that falls out, for free

Measured on layout A, not assumed:

| Treetop jump, aiming right | Result |
| --- | --- |
| from a copse-interior trunk | catches the next trunk at y=124 |
| from a copse-edge trunk, into the clearing | **lands in the dirt** |

Chaining stays exactly as it was *inside* a copse — the thing Juliana said was "fun and
about right" is untouched, because within-copse spacing is unchanged. But crossing a
clearing now costs you the trees: you come down, and you walk.

That is a new tactical shape in the game and it needed no new code. A copse is a place you
can move around in the air; the clearing between them is ground you have to cross on foot.

## What nearly broke this: trees feed the rival's jumping

The first version of this layout was three copses of 2-3-2 — seven trees, the same count,
with the centre copse stopping at 1670. It failed
`test_the_rival_really_climbs_when_it_climbs`, a guard added the same evening in `1a6f78a`
from Juliana's complaint *"the rival didn't jump very much or really climb at all"*.

**A rival can only launch a jump from up a trunk, so trunk density sets its jump rate.**

| Layout | Trees | Rival jumps/min (guard needs >8) |
| --- | --- | --- |
| 11 uniform | 11 | 8.9 |
| 2-3-2 | 7 | **6.1 — fails** |
| 2-4-1 (this design) | 7 | 8.9 |

Two of Juliana's own findings pull against each other here: *fewer trees* starves the thing
that fixed *"the rival didn't jump much"*. It is the same shape as the `GROUND_WHIMS` /
`TRUNK_WHIMS` tension already recorded in the handoff — two pieces of play feedback that
cannot both be satisfied by turning one knob further.

What resolves it is **where** the trees are, not how many. The rival is leashed to within
`LEASH` of the player, so only trunks inside that window can ever affect it; with the
player at `PLAYER_START` the window is roughly 510–1910. Layouts that differ only outside
it produce byte-identical simulations. The trunk at **1900** is the one carrying the jump
rate, which is why the centre copse runs to 1900 and the thinning is taken out of the
right-hand side instead.

**The lesson worth keeping:** tree *count* is not the tunable thing — trunk count inside
the leash window is. A future thinning that leaves the centre copse alone is free; one that
narrows it is not.

## Testing

Measured against the real suite, layout 2-4-1 breaks exactly **one** existing test. The
other 169 pass, including the rival-climbing guard above.

**`test_trees_are_spaced_for_jumping`** asserts that the set of all gaps is exactly
`{TREE_SPACING}`. It becomes two assertions: neighbours *within* a copse are
`TREE_SPACING` apart, and every gap *between* copses equals `CLEARING` — which is both the
sparseness the change is for and the check that keeps `CLEARING` honest.

**`test_a_jump_from_up_a_tree_catches_the_next_one`** keeps passing, but only by luck. It
hardcodes `TREES[4]`, which is 1670 under both layouts, and 1670 happens to still have a
neighbour at 1900 — under the rejected 2-3-2 it was a copse edge and the test failed. A
test that passes by coincidence is the kind that stops guarding anything quietly, so it and
`test_a_ground_jump_does_not_reach_the_next_tree` get a small helper returning "a trunk
with a copse-neighbour to its right", stating the condition they need instead of trusting
an index to keep meaning the same thing. This is the handoff's own *test behaviour, not
distances* lesson: **an index into `TREES` is a disguised distance.**

**One test is added** for the new rule: a treetop jump from a copse edge into a clearing
lands in the dirt. Without it, nothing stops a future tidy-up from restoring a uniform
grid and quietly undoing the entire change.

`test_visual_game.py` uses `TREES[2]` and `TREES[4]` in four places, both of which are
still trunks under the new layout. Those tests need no edits.

## Out of scope

- **Dealing copses per battle.** The backgrounds already shuffle each battle and the copses
  could too, but landing both at once makes it impossible to tell which one you are
  reacting to. Decided deliberately: keep one fixed layout until the sparser forest has
  been played.
- **Every other tuning knob.** `JUMP_SPEED`, `GRAVITY`, `AIR_SPEED`, `CATCH_REACH`,
  `MAX_CLIMB`, `LEASH`, `LONG_RANGE` and `JUMP_MIN_MS`/`MAX_MS` are all unchanged — five of
  the six play answers said so. The coupled four in particular stay untouched because
  within-copse spacing does not move.
- **Ground props** (bush, log, mud) remain parked, as in the handoff.

## The invariant

Unchanged, and worth saying out loud because this change gets near it: `battle.py` and
`choreography.py` need no edits, and neither does `game.py` or `visual_game.py`.
`visual_game.py` draws whatever is in `TREES` and does not care how it was built. All the
geometry still lives in `arena.py`.
