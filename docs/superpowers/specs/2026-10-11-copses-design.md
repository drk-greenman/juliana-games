# Squirrel Fight — Copses Instead of a Grid

Replaces the eleven evenly-spaced trees with seven trees in three copses, separated by
clearings too wide for any jump to cross. Nothing about jumping, climbing or the range
bands changes; the only production edit is how `TREES` is built.

This is the first change driven by **play feedback rather than reasoning**. It closes the
last of the six open questions listed in `docs/HANDOFF.md`.

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

Seven trees in three copses. Within a copse, trunks are `TREE_SPACING` apart exactly as
before. Between copses there is a clearing of `3 * TREE_SPACING`.

Three spacings, not two, is a judgement about feel rather than safety — a 460px gap is
also too wide to jump, but it reads as "two trees got deleted", whereas 690 is most of a
screen width and reads as open ground. This was the choice between candidate layouts, and
the sparser one was picked deliberately.

```
|   T   T             P    T   R             T   T   |

left copse    290,  520
centre copse  1210, 1440, 1670      <- both fighters start here
right copse   2360, 2590
clearings     690px, twice
```

Every trunk still sits on the old grid — this is the grid with two of every five removed —
so `PLAYER_START` (1210) and `RIVAL_START` (1670) keep their trunks and no other geometry
moves.

In `arena.py`:

```python
TREE_SPACING = 230          # within a copse — the distance a treetop jump clears
CLEARING = 3 * TREE_SPACING # 690 — wider than any jump, so leaving a copse means walking

# Each copse is (leftmost trunk, how many trunks).
COPSES = ((290, 2), (1210, 3), (2360, 2))
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

## Testing

Two existing tests fail, and both because they encode "the grid" — the thing being
deleted.

**`test_trees_are_spaced_for_jumping`** asserts that the set of all gaps is exactly
`{TREE_SPACING}`. It becomes two assertions: neighbours *within* a copse are
`TREE_SPACING` apart, and every gap *between* copses equals `CLEARING` — which is both the
sparseness the change is for and the check that keeps `CLEARING` honest.

**`test_a_jump_from_up_a_tree_catches_the_next_one`** hardcodes `TREES[4]`, which is now a
copse edge — so it would fail, correctly but for the wrong reason. It and
`test_a_ground_jump_does_not_reach_the_next_tree` get a small test helper returning "a
trunk with a copse-neighbour to its right", so they state the condition they need rather
than trusting an index to keep meaning the same thing. This is the handoff's own *test
behaviour, not distances* lesson: an index into `TREES` is a disguised distance.

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
