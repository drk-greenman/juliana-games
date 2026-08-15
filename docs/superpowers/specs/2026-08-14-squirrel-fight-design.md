# Squirrel Fight — Design Spec

Console-only 1v1 squirrel dueling game. New project folder `squirrel-fight/` in this
multi-project repo, following the pattern established by `word-combo-story/`.

## Premise

You name your squirrel and duel a randomly-named rival squirrel, computer-controlled,
in a single battle to 0 HP. No graphics, no network calls — fully offline, terminal only.

## Game structure

- **Single duel**: one battle per game, win/lose/draw, then "play again? (y/n)" like
  `word-combo-story/game.py`.
- **Simultaneous reveal turns**: each turn, both fighters pick a move at the same time
  (no seeing the opponent's choice first), then both moves resolve together.
- **AI opponent**: picks uniformly at random from all 12 moves each turn. No difficulty
  levels, no adaptive strategy — out of scope for this version.
- **Both squirrels named**: player is prompted to name their squirrel (defaults to
  "You" if left blank); the rival's name is chosen at random from a fixed list of
  silly names (same pattern as `ADJECTIVES`/`NOUNS` in `word-combo-story/game.py`),
  e.g. "Sir Fluffington", "Nutsy McGee", "Bushy Malone", "Duchess Acorn",
  "Mr. Wigglebottom", "Chompy Von Nutsalot".
- **Starting HP**: 60 for both fighters.
- **HP display**: ASCII bar + exact number each turn, e.g. `[########--] 42/60`.

## Moves

12 total moves, in three kinds: **attack**, **defense**, **heal**. Every move is always
available every turn — no cost, no cooldowns. Numbers below are a first pass; they're
just data in `moves.py` and easy to retune later if something feels off in play.

### Attacks (7)

Damage is a random integer range rolled fresh each use. Ranges intentionally vary in
width (some safe, some risky) since there's no accuracy/typing system to otherwise
differentiate them.

| Move | Damage | Notes |
|---|---|---|
| Tail Smack | 10–13 | reliable melee whack |
| Cheek Barrel | 9–15 | barreling tackle |
| Acorn Blast | 8–16 | balanced ranged throw |
| Scratch | 7–17 | quick claws |
| Chirp | 4–20 | risky shriek |
| Chirp Insanely | 0–26 | can whiff completely or be devastating |
| Steal | 6–14 | **lifesteal**: attacker heals for `damage_actually_dealt // 2` (see Turn Resolution) |

### Defenses (4)

Two dodge-type (all-or-nothing chance to fully avoid the incoming attack), two
block-type (guaranteed partial/flat reduction, no chance involved).

| Move | Type | Effect |
|---|---|---|
| Dance | dodge | 50% chance to fully avoid the incoming attack; otherwise take full damage |
| Moonwalk | dodge | 35% chance to fully avoid the incoming attack; otherwise take full damage |
| Scurry | block | always reduces incoming damage by 50% (floored) |
| Flex | block | always deflects a flat 36 damage (floored at 0 remaining) — **intentionally a guaranteed full block against any current attack**, since the highest possible attack roll is 26 (Chirp Insanely). Confirmed as intended, not a balance bug. |

### Heal (1)

A move kind distinct from attack/defense: it doesn't touch the opponent at all, and it
provides no protection against an incoming attack the same turn.

| Move | Effect |
|---|---|
| Eat Garden | restores 12–18 HP to self (capped at max HP); if the rival attacks the same turn, you still take full damage — healing does not defend |

## Turn resolution

Both fighters' moves are chosen before either resolves; mitigation and healing both use
the *other* fighter's move choice from the same turn (not sequential — nothing about
fighter A's action changes what fighter B's move does to them).

For each fighter's chosen move, evaluated against the opponent's chosen move:

- **Attack vs. Attack** — both take the other's rolled damage in full; order doesn't matter.
- **Attack vs. Defense** — the defender's move mitigates the attacker's rolled damage:
  - dodge: roll the dodge chance; success → 0 damage taken; failure → full damage taken
  - block (Scurry): damage taken = `raw_damage * 0.5`, floored
  - block (Flex): damage taken = `max(0, raw_damage - 36)`
- **Attack vs. Heal** — the healer takes the attacker's full rolled damage (heal doesn't
  defend) *and* separately restores their heal amount the same turn.
- **Defense vs. Defense** — nothing happens; print a flavor line (e.g. "both squirrels
  eye each other warily").
- **Defense vs. Heal** — nothing happens to the defender; the healer restores HP.
- **Heal vs. Heal** — both restore HP.
- **Steal specifically**: after computing `damage_actually_dealt` (i.e. post-mitigation,
  using the rules above), the Steal user heals `damage_actually_dealt // 2`, capped at
  max HP. If Steal is fully dodged, damage dealt is 0, so the heal is also 0.

All HP changes for the turn are computed from each fighter's HP at the *start* of the
turn, then applied together. HP is clamped to a minimum of 0 for display and win checks.

**Win condition**: after applying both fighters' results, if both HP are ≤ 0, the game
is a **draw**. If exactly one is ≤ 0, that fighter loses. Otherwise, the battle continues.

## Architecture

```
squirrel-fight/
  game.py     — CLI entry point: banner, naming prompt, the turn loop, all print()/input()
  battle.py   — pure logic, no I/O: Fighter dataclass, resolve_turn()
  moves.py    — static data: Move dataclass + the MOVES list (12 entries)
  test_battle.py — pytest tests for battle.py
  README.md   — what it is, how to run it (mirrors word-combo-story/README.md)
```

`battle.py` has no `print()`/`input()` calls at all — it's the one piece of this game
worth unit testing, and keeping it free of I/O is what makes that possible.

### Data model

```python
# moves.py
@dataclass(frozen=True)
class Move:
    name: str
    kind: Literal["attack", "defense", "heal"]
    description: str
    dmg_range: tuple[int, int] | None = None       # attacks
    lifesteal: bool = False                          # Steal only
    dodge_chance: float | None = None                 # dodge-type defenses
    block_reduction: float | None = None               # Scurry (fraction, e.g. 0.5)
    block_flat: int | None = None                       # Flex (flat amount)
    heal_range: tuple[int, int] | None = None            # Eat Garden
```

```python
# battle.py
@dataclass
class Fighter:
    name: str
    hp: int
    max_hp: int

@dataclass
class FighterTurnOutcome:
    move_name: str
    damage_dealt: int = 0     # damage this fighter's move inflicted on the opponent
    healed: int = 0            # HP this fighter restored to themselves
    dodged: bool = False        # true if this fighter's dodge defense succeeded

@dataclass
class TurnResult:
    fighter_a: FighterTurnOutcome
    fighter_b: FighterTurnOutcome
    flavor_text: str | None = None   # set for the defense-vs-defense clash case

def resolve_turn(fighter_a, move_a, fighter_b, move_b) -> TurnResult: ...
```

## Game loop / CLI flow

```
1. Print banner
2. Prompt: "Name your squirrel:" (default "You" if blank)
3. Randomly pick the rival's name from the fixed name list
4. Battle loop, each turn:
   a. Print both squirrels' HP as a bar + number
   b. Print the move menu, grouped by category, each with a one-line description:
        Attacks:  1) Tail Smack  2) Cheek Barrel  3) Acorn Blast
                  4) Scratch  5) Chirp  6) Chirp Insanely  7) Steal
        Defenses: 8) Dance  9) Moonwalk  10) Scurry  11) Flex
        Heal:     12) Eat Garden
   c. Prompt for a choice 1-12; reject anything else and re-prompt without
      ending the turn
   d. Computer picks uniformly at random from all 12 moves
   e. Resolve the turn via battle.resolve_turn() and print a short recap of
      what both squirrels did and the resulting HP
   f. If either squirrel's HP is 0, end the loop
5. Announce the winner (or a draw, if both hit 0 the same turn)
6. "Play again? (y/n)" — same pattern as word-combo-story/game.py
```

## Error handling

The only input surface is the per-turn move choice (1-12). Non-numeric or
out-of-range input prints a short message ("Not a valid move, try again") and
re-prompts — it never crashes or silently skips a turn. No network calls means no
API-key/connectivity handling is needed (unlike `word-combo-story`).

## Testing

This is the first test-related addition to the repo (previously no test suite
existed anywhere). Add `pytest` as a dependency and write a handful of tests against
`battle.py`'s `resolve_turn()`, covering:

- Scurry halves incoming damage; Flex fully blocks any current attack
- A successful dodge (mock/seed the random roll) results in 0 damage taken
- Steal's self-heal equals half of the damage actually dealt (post-mitigation),
  including the 0-heal case when fully dodged
- Eat Garden restores HP and is capped at max HP
- A double KO on the same turn resolves as a draw

`game.py`'s I/O loop is not unit tested — it's exercised by playing the game manually.

## Explicitly out of scope (v1)

- Graphics of any kind
- Claude API integration (fully offline, unlike word-combo-story)
- Multiple rounds/matches, tournaments, or a gauntlet of rivals
- Move costs, cooldowns, or resource pools
- Difficulty levels or adaptive AI
- Status effects (stun, buffs/debuffs) beyond the mechanics described above
