# Squirrel Fight — Moving Your Squirrel

Adds player-controlled movement to the window version of Squirrel Fight, and makes
where you're standing matter. The terminal version (`game.py`) is untouched and keeps
playing exactly as it does today.

## Why

Right now both squirrels stand on fixed marks (`PLAYER_X`/`RIVAL_X` in
`visual_game.py`) and the only movement is the lunging and staggering that
`choreography.py` plays during a turn's animation. The player picks a move and watches.
Letting the player walk their squirrel around gives them something to *do* between
decisions, and tying the moves' reach to distance turns the 12-move menu from a flat
list into a set of choices that depend on where you've put yourself.

## The shape of it

Still turn-based. Every turn you walk your squirrel wherever you like, then pick a move
as you do now. The catch is that the rival is ambling around the whole time you're
deciding, so the gap between you is always changing and you have to commit at a moment
when the move you want will actually reach.

### Free movement plus a wandering rival

These two decisions depend on each other and neither works alone:

- **You can walk as far as you like** before choosing. No step budget, no movement
  resource to manage.
- **The rival wanders at random the entire time the move menu is up** — not one hop
  between turns, but continuously.

Free movement on its own would kill the range rule: if the rival stood still you could
always stroll to your preferred distance, so no attack would ever be out of range and
the whole mechanic would go quiet. A moving target is what puts the pressure back in.
The rival's wander is genuinely random rather than tactical, so it will frequently
drift out of position and whiff on itself — that is intended, not a bug to fix later.

## Range

Distance is simply `abs(player_x - rival_x)`. A single threshold splits it into
**close** and **far**; there are no middle bands or falloff curves.

| Moves | Reach | Needs |
| --- | --- | --- |
| Tail Smack, Cheek Barrel, Scratch, Steal | `melee` | close |
| Acorn Blast, Chirp, Chirp Insanely | `ranged` | far |
| Dance, Moonwalk, Scurry, Flex, Eat Garden | `any` | works anywhere |

### Numbers to start from

These are first-pass values, in the window version's pixel coordinates. Like the damage
ranges in `moves.py`, they are data and expected to be retuned once it's been played.

| Thing | Value | Why |
| --- | --- | --- |
| Walking band | x 140 to 820 | Inside the 960-wide window, with room for the widest squirrel (~250px) not to clip the edges. |
| Minimum gap | 170 | Squirrels stop short of each other instead of overlapping. |
| Close/far threshold | 300 | Today's fixed gap is 460, so both fighters start **far** and have to close in for melee — the mechanic announces itself on turn one. |
| Walking speed | 220 px/sec | Crosses the band in about three seconds; brisk without being twitchy. |
| Rival wander speed | 90 px/sec | Slower than you, so chasing it down is winnable. |

The split follows the descriptions the moves already have in `moves.py` — "a reliable
melee whack" and "a barreling tackle" are close-up; "a balanced ranged acorn throw" and
"a piercing shriek" want room. Nobody has to learn a new rule that contradicts the text
in front of them.

An attack used at the wrong distance **whiffs**: zero damage, no lifesteal, and a
message saying why ("Tail Smack swipes at thin air — too far away!"). Defenses and
Eat Garden are unaffected by distance and always work, so there is always something
useful to do no matter where you are standing.

Whiffing applies to both fighters equally. The rival picks its move and wanders
independently, so it will regularly shriek at an empty stage.

## How it fits the existing code

The project keeps its rules pure and its I/O at the edges — `battle.py` and
`choreography.py` import no pygame and are the tested parts. This design keeps that
line intact rather than letting position leak into the drawing code.

### `moves.py` — one new field

`Move` gains `reach: Literal["melee", "ranged", "any"] = "any"`, and the 12 moves get
their values per the table above. Pure data; defaulting to `"any"` means nothing breaks
if a move is added without thinking about range.

### `arena.py` — new, pure

Everything about where squirrels are, with no pygame import so it can be tested like
`battle.py` and `choreography.py`:

- the walking band's left and right limits, and the minimum gap so squirrels can't
  walk through each other
- clamping a proposed walk to those limits
- `gap(player_x, rival_x)` and `is_close(gap)`
- the rival's random wander step, given a position and elapsed time

Keeping this separate is what lets the wander and the clamping be tested without
opening a window.

### `battle.py` — gap-aware, still pure

`resolve_turn()` takes an optional gap. When a move's `reach` doesn't match the gap, the
attack resolves as a whiff. **`gap=None` means "everything reaches"** — which is how the
terminal version keeps working untouched.

### `visual_game.py` — the moving parts

Holds the live `player_x`/`rival_x` that replace today's fixed constants, walks the
player on Left/Right (and A/D) during the `battle` state, steps the rival's wander every
frame, and draws both squirrels at their live positions. `choreography.py`'s `offset_x`
still applies on top during the animation, so lunges and staggers work as they do now.

Two pieces of feedback, both cheap because the furniture already exists:

- **Move buttons dim when they're out of range.** The buttons already carry `KIND_STYLE`
  colours, so a dimmed variant teaches the range rule without anyone reading this
  document.
- **The whiff gets a message** in the existing message strip, same as any other turn
  result.

## Testing

- **`test_arena.py`** (new): walking clamps at both limits, squirrels can't overlap,
  gap and close/far classification at and either side of the threshold, and the rival's
  wander staying inside the band over many random steps.
- **`test_battle.py`** (extended): melee whiffing when far and landing when close,
  ranged the reverse, defenses and heals unaffected at any distance, whiffs dealing no
  damage and granting no lifesteal, and `gap=None` behaving exactly as the current tests
  expect so the terminal version is provably unchanged.

The existing 68 tests must keep passing untouched.

## Out of scope

- Movement in the terminal version. `game.py` is not modified; the README notes that
  walking is a window-version feature.
- Vertical movement, jumping, or climbing. The squirrels walk on one line.
- A tactical rival that chases a range on purpose — the wander is random by choice.
- Two-player control. One human, one computer, as now.
