# Squirrel Fight — where things stand

Last updated 2026-10-11. Living document: update it rather than adding a second one.

`CLAUDE.md` describes the architecture. This describes **state, open questions, and the
traps** — the things that aren't visible from the code.

## Right now

- Branch `main`, **172 tests passing**. The copse work is merged; `main` is ahead of
  `origin` and not yet pushed.
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
| **Desktop app** | `make_app.py` builds `Squirrel Fight.app` onto the Desktop from Juliana's `assets/app-icon.png`. |

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

## Answered by playing — 2026-10-11

All six open questions went to Juliana after she played the window version. Five came back
"leave it alone", which retires them: those numbers now have play behind them rather than
a first-pass guess.

| Question | Answer | Knob, now settled |
| --- | --- | --- |
| Is a ground hop so useless it's annoying? | Fine — reads as a little hop | `JUMP_SPEED`, `AIR_SPEED` |
| Is chaining along the treetops too strong? | Fun and about right | `JUMP_MIN_MS`/`MAX_MS` |
| Does the rival jumping make fights drag? | No — fights moved along fine | `JUMP_MIN_MS`/`MAX_MS` |
| Does walking into the leash's stop feel broken? | Never noticed it | `LEASH` |
| Does "drops well short" ever come up? | Occasionally — which is its job | `LONG_RANGE` |
| Is 11 trees too many? | **Yes — "trees are everywhere"** | `TREE_SPACING`, `COPSES` |

The sixth was the real finding: there was always a trunk within a step, so walking to a
tree was never a decision. Fixed by breaking up the grid — see
`docs/superpowers/specs/2026-10-11-copses-design.md`.

### The copses worked — played 2026-10-13

**"It worked."** The forest reads thinner, and the clearings are noticeable as their own
kind of place rather than as a few trees having gone missing. The question the whole change
existed to answer is answered: walking to a tree is a decision again.

**A prediction that was wrong, in the useful direction.** This document argued twice that
the thinning might not register, because every battle opens inside the centre copse and the
opening screen only went from 5 trunks to 4 — the rival's jump guard forces trunks into
exactly the window the opening camera frames. That worry was real but it did not matter:
what registers is apparently the *travelling*, not the opening frame. Worth remembering
before anyone redesigns the opening geometry to "fix" a problem play says isn't there.

Note this took **two** play sessions, and the first one said the opposite — see the play
worktree trap below. The first report was *"didn't notice anything about the trees being
different"*, which read exactly like this prediction coming true. It was a stale build.

### Still unplayed

- Does being caught in a clearing, with the rival up a trunk, feel unfair?
- Is the lone tree at 2590 a trap worth having, or just a tree nobody visits? Not visited
  yet in two sessions, which is itself mildly suggestive.
- **Painted trees are not climbable trees.** The background art contains drawn trees; only
  the 7 trunks in `TREES` can be climbed. At 11 trunks the real ones outnumbered the
  painted ones and at 7 they do not, so "I tried to climb that tree and couldn't" is now a
  likelier complaint. Pre-existing, but thinning made it easier to trip over.

**This loop already works.** Four rounds of it so far, none of them findable by reasoning:

1. *"The rival keeps getting stuck on trees."* Its vertical whim averaged zero, so height
   was an aimless walk that sits at every height equally: it clung to a trunk 71% of the
   fight and, unable to walk while off the ground, stopped the fight dead. Fixed in
   `fc712f5` by weighting the whim downwards.
2. *"The rival didn't jump very much or really climb at all."* That fix overshot. Pulled
   down hard, the walk never commits — it bobbed at the foot of trunks, 1.6% of the fight
   above 120px, and jumps (which can only launch from up a trunk) halved. Fixed in
   `1a6f78a`: the whim now depends on where the rival is, so a climb is a committed run.
   **One weighted draw cannot mean both "come down" and "go all the way up".**
3. *"I climbed a tree and jumped at the top and flew off the map."* Catching a trunk
   mid-air returned the catch height uncapped, so chained jumps each launched from the
   last one's apex and ratcheted ~73px higher forever — 3531px against a 240px budget.
   Fixed in `b6ff85b` by capping a grip at `MAX_CLIMB`.
4. *"Is the icon supposed to be used as my fighter?"* It was not. `app-icon.png` went into
   `assets/` with the Desktop app and was never added to `RESERVED_STEMS`, so
   `available_squirrels()` offered it as a thirteenth squirrel either side could borrow.
   Fixed in `a6f0abc`. This is the *second* time an unreserved drawing was dealt as a
   fighter — `tree.png` was the first — and the test guarding the rule could not catch
   either, because it builds a synthetic folder from a hardcoded list of filenames and so
   only ever sees art someone remembered to tell it about.
   **A test that invents its own inputs cannot catch a real input nobody listed.**
   `test_the_real_assets_folder_offers_exactly_the_rivals` now reads `assets/` itself.

Findings 1 and 2 are opposite failures of the same knob, and the two tests that bracket
them (`test_the_rival_does_not_live_up_a_tree`, `test_the_rival_really_climbs_when_it_climbs`)
are deliberately in tension — a plain random walk cannot satisfy both. If you are tuning
`GROUND_WHIMS`/`TRUNK_WHIMS`, run both and expect to be squeezed.

Note what finding 1's test got wrong: it guarded the *share* of time off the ground, which
stopped meaning "stuck" the moment jumping existed — a rival climbing, perching, leaping
and descending is off the ground half the time while never standing still. Guarding that
share is what caused finding 2. It now guards the longest stint and distance travelled.

## Traps, learned the hard way

**Numbers that look independent are coupled.** `JUMP_SPEED`, `GRAVITY`, `AIR_SPEED`,
`TREE_SPACING` and `CATCH_REACH` only work as a set. A catch radius quietly adds itself to
every jump's reach — at 60 a ground jump grabbed the next trunk and destroyed the whole
"only leap from up a tree" rule. `test_a_ground_jump_does_not_reach_the_next_tree` guards
it. Likewise `MAX_CLIMB` is set by the stage ceiling, and the thing that has to fit under
it is the jump *apex*, not the climb height — getting that wrong clipped squirrels' heads
off.

**`TREE_SPACING` is not a free knob — it is pinned at 230.** Three constraints meet on it:
a ground jump must fall short of the next trunk, a treetop jump must reach it, and it must
divide the fighters' 460px opening gap so neither starts favoured. The legal window is
(212, 285] and the only value in it that divides 460 is 230. This is why the forest was
thinned by *removing* trees rather than by spreading them out.

**Removing trees throttles the rival's jumping.** It can only launch from up a trunk, so
trunk density sets its jump rate — and only trunks within `LEASH` of the player can ever
affect it, which with the player mid-map is about 510–1910. Layouts differing only outside
that window simulate identically. The first copse layout tried dropped the rival to 6.1
jumps/min against the `> 8` guard in `test_the_rival_really_climbs_when_it_climbs`; keeping
the centre copse out to 1900 restored it to 8.9. **The tunable quantity is trunks inside
the leash window, not trees in the world — thin the edges, never the middle.** This is the
same shape as findings 1 and 2 above: two pieces of play feedback pulling opposite ways on
one knob.

**The Desktop app can't be patched in place, and it plays a different checkout.** The
bundle is ad-hoc code-signed, so editing anything inside it — dropping in a new `.icns`
being the obvious temptation — breaks the seal and macOS refuses to open it as "damaged".
`make_app.py` therefore rebuilds the whole bundle and re-signs it; Finder also caches icons
per bundle, so the app is touched at the end or it goes on showing the old picture. The app
currently on the Desktop was built pointing at the **`juliana-games-play` worktree**, not
this checkout, which is why a change made here doesn't show up when Juliana double-clicks.
Rebuild with that folder as the argument to keep it that way.

**And the play worktree is a *detached* checkout — it does not follow `main`.** Merging and
pushing changes nothing about what Juliana plays; the worktree has to be moved deliberately
(`cd ../juliana-games-play && git checkout --detach main`) and the app rebuilt afterwards.

This has already cost a full round of play feedback. The copses shipped, Juliana played,
and reported *"didn't notice anything about the trees being different"* — which read
exactly like the predicted "the thinning is too subtle to register". It wasn't: the play
worktree was pinned five commits back at `b41275b` and still had all eleven trees. The
feedback was real and the conclusion would have been completely wrong.

**So: when play feedback says a change had no effect, check what commit the play copy is on
before you believe it.**

```bash
git -C ../juliana-games-play log --oneline -1
python3 -c "import sys; sys.path.insert(0,'../juliana-games-play/squirrel-fight'); \
import arena; print(len(arena.TREES), 'trees')"
```

**Test behaviour, not distances.** Both bugs above were invisible to tests that measured
how far a jump went, and obvious to tests that asserted "lands in the dirt" or "catches the
next trunk". A corollary learned while thinning the trees: **an index into `TREES` is a
disguised distance.** Three jump tests used `TREES[4]` to mean "a trunk with another one
230px to its right", which was only true while the trees were a uniform grid — they now ask
for that condition by name.

**For jump tuning, read catch *height*, not caught-versus-dirt.** At a spacing of 280 a
treetop jump still "catches" the next trunk — 7px off the ground, which on screen is a
squirrel scrabbling at the base of a tree, not a leap between treetops. At 230 it catches
at y=124. A pass/fail assertion cannot see the difference, so sweep the height.

**`visual_game.py` has only smoke tests, and they matter.** Mid-way through the wide world
the game was completely broken at launch while all 105 tests passed, because nothing
exercised it. `test_visual_game.py` now drives a real `Game` through its states; it is
deliberately shallow and its job is to fail when a rename breaks the game.

**Backgrounds have no alpha.** `load_background` reads without an alpha channel and treats
**pure white as see-through** — real transparency comes out black, and white clouds would
punch holes. Squirrel sprites are the opposite and do want transparency.

**Check pytest's exit code.** `pytest … | tail -2 && git commit` hides failures; a commit
went through red that way. Use `python3 -m pytest squirrel-fight/ -q; echo $?`.

**Another session may be working on this repo — this keeps happening.** It has now
occurred twice. The second time, three commits (`b6ff85b`, `1a6f78a`, `b41275b`) landed in
the working tree *while another session was mid-task*, and one of them added the rival
jump guard that the copse work then had to satisfy. Fetch and `git log` before you start,
not just before you push — and if you are about to rewrite a section of this file, re-read
it first rather than trusting line numbers from a plan written ten minutes ago.

## What's next

**The copse work is finished and has play behind it.** Nothing is outstanding from it.

1. **Keep playing, and keep saying what's annoying.** It is still the highest-value thing
   by a distance — four rounds, four findings, none of them reachable by reasoning. Two
   small things remain unanswered above: whether a clearing feels unfair when the rival is
   up a trunk, and whether the lone tree ever gets used.
2. **More scenes**, if wanted: drop `background-<place>.png` into `assets/` and it is found
   automatically. Template at `source-art/background-template.png`, 240×110, white = see-through.
   Remember to reserve the stem if a new drawing is *not* a squirrel — finding 4 above.

**Deliberately parked:** ground props — bush, log, mud (the unbuilt half of sub-project 3).
They would add rules on top of rules that have had almost no play between them. Leave them
until the six features already in have been lived with.

Nothing is outstanding in the repo itself: `main` is pushed and in sync, the working tree
is clean, and both merged branches (`squirrel-copses`, `squirrel-fight-visuals`) have been
deleted locally and on the remote.
