# Squirrel Fight — where things stand

Last updated 2026-10-11. Living document: update it rather than adding a second one.

`CLAUDE.md` describes the architecture. This describes **state, open questions, and the
traps** — the things that aren't visible from the code.

## Right now

- Branch `main`, **168 tests passing**, working tree clean.
- Everything that was planned is built. No half-finished work.
- Two ways to play, one rules engine:
  - `python3 squirrel-fight/game.py` — terminal, deliberately unchanged all along
  - `python3 squirrel-fight/visual_game.py` — the window version, where all the new work is

Controls: arrows or `A`/`D` walk · `W`/`S` or up/down climb at a trunk · **Space** jumps ·
number keys or click pick a move · Esc quits.

## What got built

| | |
| --- | --- |
| **Borrowed squirrels** | All 12 rivals have art. `make_sprites.py` recolours one CC0 sprite per rival. |
| **Movement + range** | Walk freely; the rival wanders at random; melee/ranged whiff at the wrong distance. |
| **Wide world** | Three screens across, camera centred between the fighters, a third "too far" band. |
| **Climbing** | Trees at fixed spots, free climbing, height counts as distance. |
| **Jumping** | Space; leap trunk to trunk, steer mid-air, catch a trunk on the way down. |
| **Backgrounds** | Three scenes dealt across the world per battle. |
| **Borrowed scenery** | A CC0 autumn forest, plus a climbable trunk cut from the same art. |

Every spec is in `docs/superpowers/specs/`, every plan in `docs/superpowers/plans/`. The
specs explain *why* each number is what it is; read the spec before changing one.

## The invariant worth protecting

The project is split by purity, and that split is what has kept six features from
tangling:

- **Pure, no pygame, heavily tested:** `moves.py`, `battle.py`, `choreography.py`,
  `arena.py`
- **I/O at the edges:** `game.py`, `visual_game.py`, `sprites.py`

`battle.py` speaks only in range *bands* (`"close"`/`"mid"`/`"far"`), never pixels.
`arena.py` owns all the geometry. This is why adding a whole second dimension (climbing)
and then gravity (jumping) needed **zero** changes to the rules modules — and why
`game.py` has not been modified by any of the last six features. If a change starts
needing edits in `battle.py` or `choreography.py`, that's the signal something is leaking.

## Open questions — these need playing, not reasoning

Nobody has played most of this. Every number below is a first-pass guess, and they all
live together at the top of `arena.py`.

| Question | Knob |
| --- | --- |
| Is a ground hop so useless it's annoying? | `JUMP_SPEED`, `AIR_SPEED` |
| Is chaining along the treetops (hold Space + a direction) too strong? | `JUMP_MIN_MS`/`MAX_MS` |
| Does the rival jumping make fights drag, the way its climbing did? | `JUMP_MIN_MS`/`MAX_MS` |
| Does walking into the leash's invisible stop feel broken? | `LEASH` |
| Does "drops well short" ever actually come up? | `LONG_RANGE` |
| Is 11 trees too many — "walk to a tree" stopped being a decision | `TREE_SPACING` |

**This loop already works.** The one piece of real play feedback so far — *"the rival keeps
getting stuck on trees"* — found a bug worse than any of the above: its vertical whim
averaged zero, so it clung to a trunk 71% of the fight and, being unable to walk while off
the ground, stopped the fight dead. Fixed in `fc712f5`. That was not findable by reasoning.

## Traps, learned the hard way

**Numbers that look independent are coupled.** `JUMP_SPEED`, `GRAVITY`, `AIR_SPEED`,
`TREE_SPACING` and `CATCH_REACH` only work as a set. A catch radius quietly adds itself to
every jump's reach — at 60 a ground jump grabbed the next trunk and destroyed the whole
"only leap from up a tree" rule. `test_a_ground_jump_does_not_reach_the_next_tree` guards
it. Likewise `MAX_CLIMB` is set by the stage ceiling, and the thing that has to fit under
it is the jump *apex*, not the climb height — getting that wrong clipped squirrels' heads
off.

**Test behaviour, not distances.** Both bugs above were invisible to tests that measured
how far a jump went, and obvious to tests that asserted "lands in the dirt" or "catches the
next trunk".

**`visual_game.py` has only smoke tests, and they matter.** Mid-way through the wide world
the game was completely broken at launch while all 105 tests passed, because nothing
exercised it. `test_visual_game.py` now drives a real `Game` through its states; it is
deliberately shallow and its job is to fail when a rename breaks the game.

**Backgrounds have no alpha.** `load_background` reads without an alpha channel and treats
**pure white as see-through** — real transparency comes out black, and white clouds would
punch holes. Squirrel sprites are the opposite and do want transparency.

**Check pytest's exit code.** `pytest … | tail -2 && git commit` hides failures; a commit
went through red that way. Use `python3 -m pytest squirrel-fight/ -q; echo $?`.

**Another session may be working on this repo.** One landed a commit mid-session. Fetch
and check before pushing.

## What's next

1. **Juliana plays it.** Highest value by a distance, and the only way to answer anything
   above. She doesn't need to diagnose — "this bit is annoying" is the useful signal.
2. **Push** — currently 1 commit ahead of origin.
3. **More scenes**, if wanted: drop `background-<place>.png` into `assets/` and it is found
   automatically. Template at `source-art/background-template.png`, 240×110, white = see-through.

**Deliberately parked:** ground props — bush, log, mud (the unbuilt half of sub-project 3).
They would add rules on top of rules that have had almost no play between them. Leave them
until the six features already in have been lived with.

Also outstanding and trivial: the stale `squirrel-fight-visuals` branch still exists on the
remote, fully merged.
