# Squirrel Fight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the console-only Squirrel Fight game described in `docs/superpowers/specs/2026-08-14-squirrel-fight-design.md`.

**Architecture:** A new `squirrel-fight/` project folder with three modules — `moves.py` (static move data), `battle.py` (pure-logic turn resolution, no I/O), and `game.py` (the CLI loop) — plus `pytest` tests for `battle.py`. Root `requirements.txt`, `README.md`, and `CLAUDE.md` are updated to reflect the new project and its testing pattern.

**Tech Stack:** Python 3 standard library only (`random`, `dataclasses`, `typing`), plus `pytest` for tests.

---

## Reference: full move list

For convenience, the 12 moves from the spec (exact numbers, do not change):

**Attacks** (menu 1-7): Tail Smack 10–13, Cheek Barrel 9–15, Acorn Blast 8–16, Scratch 7–17, Chirp 4–20, Chirp Insanely 0–26, Steal 6–14 (lifesteal: heals attacker `damage_dealt // 2`).

**Defenses** (menu 8-11): Dance (50% dodge), Moonwalk (35% dodge), Scurry (always halves damage), Flex (always deflects a flat 36 — intentionally a guaranteed full block against any current attack).

**Heal** (menu 12): Eat Garden (restores 12–18 HP to self, capped at max HP; provides no protection against an incoming attack the same turn).

Starting HP: 60 for both fighters. Full turn-resolution rules (attack vs. attack, attack vs. defense, attack vs. heal, defense vs. defense, etc.) are in the spec — the code in Task 4 below implements them exactly.

---

### Task 1: Add pytest as a dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add pytest to requirements.txt**

Current content:
```
anthropic
python-dotenv
```

New content:
```
anthropic
python-dotenv
pytest
```

- [ ] **Step 2: Install it**

Run: `pip install -r requirements.txt`
Expected: pytest installs successfully (along with any already-installed packages being confirmed present).

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "Add pytest dependency for Squirrel Fight tests"
```

---

### Task 2: Create the move data model and full move list

**Files:**
- Create: `squirrel-fight/moves.py`

- [ ] **Step 1: Write moves.py**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Move:
    name: str
    kind: Literal["attack", "defense", "heal"]
    description: str
    dmg_range: tuple[int, int] | None = None
    lifesteal: bool = False
    dodge_chance: float | None = None
    block_reduction: float | None = None
    block_flat: int | None = None
    heal_range: tuple[int, int] | None = None


MOVES: list[Move] = [
    Move("Tail Smack", "attack", "A reliable melee whack.", dmg_range=(10, 13)),
    Move("Cheek Barrel", "attack", "A barreling tackle, cheeks first.", dmg_range=(9, 15)),
    Move("Acorn Blast", "attack", "A balanced ranged acorn throw.", dmg_range=(8, 16)),
    Move("Scratch", "attack", "Quick claws, decent spread.", dmg_range=(7, 17)),
    Move("Chirp", "attack", "A risky, piercing shriek.", dmg_range=(4, 20)),
    Move("Chirp Insanely", "attack", "Totally unhinged. Could whiff, could devastate.", dmg_range=(0, 26)),
    Move(
        "Steal",
        "attack",
        "Swipes the rival's acorns; heals you for half the damage dealt.",
        dmg_range=(6, 14),
        lifesteal=True,
    ),
    Move("Dance", "defense", "A flashy juke. 50% chance to fully dodge.", dodge_chance=0.5),
    Move("Moonwalk", "defense", "A cooler, riskier juke. 35% chance to fully dodge.", dodge_chance=0.35),
    Move("Scurry", "defense", "Duck and cover. Always halves incoming damage.", block_reduction=0.5),
    Move("Flex", "defense", "Flex so hard nothing gets through. Deflects 36 damage flat.", block_flat=36),
    Move(
        "Eat Garden",
        "heal",
        "Snack on some veggies. Restores 12-18 HP, but doesn't defend.",
        heal_range=(12, 18),
    ),
]
```

- [ ] **Step 2: Verify it imports and has the right shape**

Run:
```bash
cd squirrel-fight && python3 -c "
from moves import MOVES
assert len(MOVES) == 12
assert sum(1 for m in MOVES if m.kind == 'attack') == 7
assert sum(1 for m in MOVES if m.kind == 'defense') == 4
assert sum(1 for m in MOVES if m.kind == 'heal') == 1
print('OK')
"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/moves.py
git commit -m "Add move data for Squirrel Fight"
```

---

### Task 3: Write failing tests for the battle engine

**Files:**
- Create: `squirrel-fight/test_battle.py`

This writes tests against `Fighter`, `resolve_turn`, and `battle_outcome` before those exist in `battle.py` — they're expected to fail on import in Step 2, which confirms the tests are actually exercising real (not-yet-written) code.

- [ ] **Step 1: Write test_battle.py**

```python
import battle as battle_module
from battle import Fighter, resolve_turn, battle_outcome
from moves import Move


def make_attack(name, dmg_range, lifesteal=False):
    return Move(name=name, kind="attack", description="", dmg_range=dmg_range, lifesteal=lifesteal)


def make_dodge(name, chance):
    return Move(name=name, kind="defense", description="", dodge_chance=chance)


def make_block_pct(name, reduction):
    return Move(name=name, kind="defense", description="", block_reduction=reduction)


def make_block_flat(name, flat):
    return Move(name=name, kind="defense", description="", block_flat=flat)


def make_heal(name, heal_range):
    return Move(name=name, kind="heal", description="", heal_range=heal_range)


def test_attack_vs_attack_deals_full_damage_both_ways(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Tail Smack", (10, 13))
    move_b = make_attack("Acorn Blast", (8, 16))
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 13
    assert result.fighter_b.damage_dealt == 16
    assert b.hp == 60 - 13
    assert a.hp == 60 - 16


def test_block_percentage_halves_damage(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16))
    move_b = make_block_pct("Scurry", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 8
    assert b.hp == 60 - 8


def test_block_flat_reduces_by_fixed_amount(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Chirp Insanely", (0, 26))
    move_b = make_block_flat("Flex", 36)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 0
    assert b.hp == 60


def test_dodge_success_avoids_all_damage(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    monkeypatch.setattr(battle_module.random, "random", lambda: 0.0)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16))
    move_b = make_dodge("Dance", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 0
    assert result.fighter_b.dodged is True
    assert b.hp == 60


def test_dodge_failure_takes_full_damage(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    monkeypatch.setattr(battle_module.random, "random", lambda: 0.99)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16))
    move_b = make_dodge("Dance", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 16
    assert result.fighter_b.dodged is False
    assert b.hp == 60 - 16


def test_heal_restores_hp_and_is_capped_at_max(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=55, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_heal("Eat Garden", (12, 18))
    move_b = make_dodge("Dance", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.healed == 18
    assert a.hp == 60


def test_attack_vs_heal_healer_still_takes_full_damage(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=20, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_heal("Eat Garden", (12, 18))
    move_b = make_attack("Chirp Insanely", (0, 26))
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.healed == 18
    assert result.fighter_b.damage_dealt == 26
    assert a.hp == 12


def test_steal_heals_attacker_by_half_of_actual_damage_dealt(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=40, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Steal", (6, 14), lifesteal=True)
    move_b = make_block_pct("Scurry", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 7
    assert result.fighter_a.healed == 3
    assert a.hp == 43
    assert b.hp == 53


def test_steal_heals_nothing_when_fully_dodged(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    monkeypatch.setattr(battle_module.random, "random", lambda: 0.0)
    a = Fighter(name="A", hp=40, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Steal", (6, 14), lifesteal=True)
    move_b = make_dodge("Dance", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 0
    assert result.fighter_a.healed == 0
    assert a.hp == 40


def test_defense_vs_defense_is_a_harmless_clash():
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_dodge("Dance", 0.5)
    move_b = make_block_pct("Scurry", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert a.hp == 60
    assert b.hp == 60
    assert result.flavor_text is not None


def test_double_ko_is_a_draw(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=10, max_hp=60)
    b = Fighter(name="B", hp=10, max_hp=60)
    move_a = make_attack("Chirp Insanely", (0, 26))
    move_b = make_attack("Chirp Insanely", (0, 26))
    resolve_turn(a, move_a, b, move_b)
    assert battle_outcome(a, b) == "draw"


def test_battle_outcome_ongoing_when_both_alive():
    a = Fighter(name="A", hp=30, max_hp=60)
    b = Fighter(name="B", hp=30, max_hp=60)
    assert battle_outcome(a, b) == "ongoing"


def test_battle_outcome_a_wins_when_b_at_zero():
    a = Fighter(name="A", hp=10, max_hp=60)
    b = Fighter(name="B", hp=0, max_hp=60)
    assert battle_outcome(a, b) == "a_wins"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd squirrel-fight && pytest test_battle.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'battle'` (or `ImportError`), since `battle.py` doesn't exist yet.

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/test_battle.py
git commit -m "Add failing tests for Squirrel Fight battle engine"
```

---

### Task 4: Implement the battle engine

**Files:**
- Create: `squirrel-fight/battle.py`

- [ ] **Step 1: Write battle.py**

```python
from __future__ import annotations

import random
from dataclasses import dataclass

from moves import Move


@dataclass
class Fighter:
    name: str
    hp: int
    max_hp: int


@dataclass
class FighterTurnOutcome:
    move_name: str
    damage_dealt: int = 0
    healed: int = 0
    dodged: bool = False


@dataclass
class TurnResult:
    fighter_a: FighterTurnOutcome
    fighter_b: FighterTurnOutcome
    flavor_text: str | None = None


def _roll_damage(move: Move) -> int:
    lo, hi = move.dmg_range
    return random.randint(lo, hi)


def _roll_heal(move: Move) -> int:
    lo, hi = move.heal_range
    return random.randint(lo, hi)


def _mitigate(raw_damage: int, defending_move: Move | None) -> tuple[int, bool]:
    if defending_move is None or defending_move.kind != "defense":
        return raw_damage, False
    if defending_move.dodge_chance is not None:
        if random.random() < defending_move.dodge_chance:
            return 0, True
        return raw_damage, False
    if defending_move.block_reduction is not None:
        return int(raw_damage * (1 - defending_move.block_reduction)), False
    if defending_move.block_flat is not None:
        return max(0, raw_damage - defending_move.block_flat), False
    return raw_damage, False


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def resolve_turn(fighter_a: Fighter, move_a: Move, fighter_b: Fighter, move_b: Move) -> TurnResult:
    outcome_a = FighterTurnOutcome(move_name=move_a.name)
    outcome_b = FighterTurnOutcome(move_name=move_b.name)
    flavor_text = None

    dmg_a_to_b = 0
    dmg_b_to_a = 0

    if move_a.kind == "attack":
        raw = _roll_damage(move_a)
        defending = move_b if move_b.kind == "defense" else None
        dmg_a_to_b, b_dodged = _mitigate(raw, defending)
        if defending is not None and defending.dodge_chance is not None:
            outcome_b.dodged = b_dodged
        if move_a.lifesteal:
            outcome_a.healed += dmg_a_to_b // 2

    if move_b.kind == "attack":
        raw = _roll_damage(move_b)
        defending = move_a if move_a.kind == "defense" else None
        dmg_b_to_a, a_dodged = _mitigate(raw, defending)
        if defending is not None and defending.dodge_chance is not None:
            outcome_a.dodged = a_dodged
        if move_b.lifesteal:
            outcome_b.healed += dmg_b_to_a // 2

    if move_a.kind == "heal":
        outcome_a.healed += _roll_heal(move_a)

    if move_b.kind == "heal":
        outcome_b.healed += _roll_heal(move_b)

    if move_a.kind == "defense" and move_b.kind == "defense":
        flavor_text = "Both squirrels eye each other warily, neither committing to a move."

    outcome_a.damage_dealt = dmg_a_to_b
    outcome_b.damage_dealt = dmg_b_to_a

    fighter_a.hp = _clamp(fighter_a.hp - dmg_b_to_a + outcome_a.healed, 0, fighter_a.max_hp)
    fighter_b.hp = _clamp(fighter_b.hp - dmg_a_to_b + outcome_b.healed, 0, fighter_b.max_hp)

    return TurnResult(fighter_a=outcome_a, fighter_b=outcome_b, flavor_text=flavor_text)


def battle_outcome(fighter_a: Fighter, fighter_b: Fighter) -> str:
    a_down = fighter_a.hp <= 0
    b_down = fighter_b.hp <= 0
    if a_down and b_down:
        return "draw"
    if a_down:
        return "b_wins"
    if b_down:
        return "a_wins"
    return "ongoing"
```

Note on the HP math: damage and healing are combined into one delta (`hp - damage_taken + healed`) and clamped to `[0, max_hp]` **once**, at the end — not clamped to 0 after damage and then healed separately. That ordering matters: e.g. a fighter at 20 HP who takes 26 damage while also healing 18 (the Attack-vs-Heal case) ends at exactly 12, not at `max(0, 20-26) + 18 = 18`.

- [ ] **Step 2: Run the tests to verify they pass**

Run: `cd squirrel-fight && pytest test_battle.py -v`
Expected: all 13 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/battle.py
git commit -m "Implement Squirrel Fight battle engine"
```

---

### Task 5: Build the CLI game loop

**Files:**
- Create: `squirrel-fight/game.py`

- [ ] **Step 1: Write game.py**

```python
import random

from battle import Fighter, resolve_turn, battle_outcome
from moves import MOVES

RIVAL_NAMES = [
    "Sir Fluffington",
    "Nutsy McGee",
    "Bushy Malone",
    "Duchess Acorn",
    "Mr. Wigglebottom",
    "Chompy Von Nutsalot",
    "The Grey Menace",
    "Professor Chestnut",
]

BANNER = r"""
  #################################################
  #                                               #
  #               SQUIRREL FIGHT!                 #
  #                                               #
  #################################################
"""

HP_BAR_WIDTH = 20


def hp_bar(fighter: Fighter) -> str:
    filled = round((fighter.hp / fighter.max_hp) * HP_BAR_WIDTH)
    filled = max(0, min(HP_BAR_WIDTH, filled))
    bar = "#" * filled + "-" * (HP_BAR_WIDTH - filled)
    return f"[{bar}] {fighter.hp}/{fighter.max_hp}"


def print_status(player: Fighter, computer: Fighter) -> None:
    print(f"\n  {player.name:<20} {hp_bar(player)}")
    print(f"  {computer.name:<20} {hp_bar(computer)}\n")


def print_menu() -> None:
    print("  Attacks:")
    for i, move in enumerate(MOVES[:7], start=1):
        print(f"    {i}) {move.name} - {move.description}")
    print("  Defenses:")
    for i, move in enumerate(MOVES[7:11], start=8):
        print(f"    {i}) {move.name} - {move.description}")
    print("  Heal:")
    for i, move in enumerate(MOVES[11:], start=12):
        print(f"    {i}) {move.name} - {move.description}")


def prompt_move(fighter_name: str):
    while True:
        choice = input(f"  {fighter_name}, pick a move (1-12): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(MOVES):
            return MOVES[int(choice) - 1]
        print("  Not a valid move, try again.")


def computer_choose_move():
    return random.choice(MOVES)


def print_turn_result(player: Fighter, computer: Fighter, result) -> None:
    print(f"\n  {player.name} uses {result.fighter_a.move_name}!")
    print(f"  {computer.name} uses {result.fighter_b.move_name}!")
    if result.flavor_text:
        print(f"  {result.flavor_text}")
    if result.fighter_b.dodged:
        print(f"  {computer.name} dodges out of the way!")
    if result.fighter_a.damage_dealt:
        print(f"  {player.name} hits {computer.name} for {result.fighter_a.damage_dealt} damage!")
    if result.fighter_a.dodged:
        print(f"  {player.name} dodges out of the way!")
    if result.fighter_b.damage_dealt:
        print(f"  {computer.name} hits {player.name} for {result.fighter_b.damage_dealt} damage!")
    if result.fighter_a.healed:
        print(f"  {player.name} heals {result.fighter_a.healed} HP!")
    if result.fighter_b.healed:
        print(f"  {computer.name} heals {result.fighter_b.healed} HP!")
    print_status(player, computer)


def play_battle() -> None:
    name = input("  Name your squirrel: ").strip() or "You"
    player = Fighter(name=name, hp=60, max_hp=60)
    computer = Fighter(name=random.choice(RIVAL_NAMES), hp=60, max_hp=60)

    print(f"\n  {player.name} vs. {computer.name}! Let the fight begin!\n")

    while True:
        print_status(player, computer)
        print_menu()
        player_move = prompt_move(player.name)
        computer_move = computer_choose_move()
        result = resolve_turn(player, player_move, computer, computer_move)
        print_turn_result(player, computer, result)

        outcome = battle_outcome(player, computer)
        if outcome == "draw":
            print("  Both squirrels are down! It's a draw!\n")
            break
        if outcome == "a_wins":
            print(f"  {player.name} wins!\n")
            break
        if outcome == "b_wins":
            print(f"  {computer.name} wins!\n")
            break


def main() -> None:
    print(BANNER)
    while True:
        play_battle()
        again = input("  Play again? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            print("\n  Thanks for playing! Bye! :)\n")
            break


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it runs a full battle without crashing**

Both squirrels spamming "Tail Smack" (undefended 10-13 damage each way) will always finish within 6 rounds from 60 HP, so this scripted input reliably exercises the full loop end-to-end, including declining the replay prompt:

Run:
```bash
cd squirrel-fight && printf 'TestSquirrel\n1\n1\n1\n1\n1\n1\n1\n1\nn\n' | python3 game.py
```
Expected: the banner prints, the battle plays out over several turns with HP bars and move descriptions, a winner (or draw) is announced, and the program exits cleanly after "Thanks for playing! Bye! :)" — no traceback.

- [ ] **Step 3: Verify invalid input is rejected without crashing**

Run:
```bash
cd squirrel-fight && printf 'TestSquirrel\nabc\n99\n1\n1\n1\n1\n1\n1\n1\n1\nn\n' | python3 game.py
```
Expected: two "Not a valid move, try again." lines (for `abc` and `99`) before the battle proceeds normally to completion.

- [ ] **Step 4: Commit**

```bash
git add squirrel-fight/game.py
git commit -m "Add Squirrel Fight CLI game loop"
```

---

### Task 6: Add the project README

**Files:**
- Create: `squirrel-fight/README.md`

- [ ] **Step 1: Write squirrel-fight/README.md**

```markdown
# Squirrel Fight

A console-only 1v1 squirrel dueling game. Name your squirrel, pick from 12 silly
attack/defense/heal moves each turn, and battle a randomly-named rival squirrel
controlled by the computer.

## Run it

From the repo root:

```bash
pip install -r requirements.txt
python squirrel-fight/game.py
```

No API key needed — this game is fully offline.

## Run the tests

```bash
pip install -r requirements.txt
pytest squirrel-fight/test_battle.py
```
```

- [ ] **Step 2: Commit**

```bash
git add squirrel-fight/README.md
git commit -m "Add README for Squirrel Fight"
```

---

### Task 7: Update the root README's project list

**Files:**
- Modify: `README.md:17`

- [ ] **Step 1: Add the new project link**

Find:
```markdown
- [`word-combo-story/`](word-combo-story/) — pick a silly word combo, describe it, and get a short AI-written story about it.
```

Replace with:
```markdown
- [`word-combo-story/`](word-combo-story/) — pick a silly word combo, describe it, and get a short AI-written story about it.
- [`squirrel-fight/`](squirrel-fight/) — name your squirrel and duel a randomly-named rival with silly attack, defense, and heal moves.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "List Squirrel Fight in the root README"
```

---

### Task 8: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md:18`
- Modify: `CLAUDE.md:26`

- [ ] **Step 1: Replace the "no test suite" line with an accurate one**

Find (line 18):
```markdown
There is no build step, linter, or test suite configured in this repo.
```

Replace with:
```markdown
There is no build step or linter configured in this repo. Most projects have no tests
either, but where a project's logic is worth verifying automatically (e.g. Squirrel
Fight's battle math), it gets a `pytest` test file alongside it — run with
`pytest <project-folder>/test_*.py`. Don't assume every project has tests; check for a
`test_*.py` file in that project's folder.
```

- [ ] **Step 2: Add the second project to the architecture list**

Find (line 26, end of file):
```markdown
- `word-combo-story/game.py`: picks a random adjective + noun combo, prompts the player to describe what it is, then streams a short kid-friendly story from Claude (`claude-haiku-4-5-20251001` via the `anthropic` SDK's `messages.stream`) back to the terminal. The word lists (`ADJECTIVES`, `NOUNS`) are the main tunable content — edits there are the most common kind of change requested for this game.
```

Replace with:
```markdown
- `word-combo-story/game.py`: picks a random adjective + noun combo, prompts the player to describe what it is, then streams a short kid-friendly story from Claude (`claude-haiku-4-5-20251001` via the `anthropic` SDK's `messages.stream`) back to the terminal. The word lists (`ADJECTIVES`, `NOUNS`) are the main tunable content — edits there are the most common kind of change requested for this game.

- `squirrel-fight/`: a console 1v1 squirrel dueling game, fully offline (no Claude API use). Split across three files rather than one script: `moves.py` holds the 12 attack/defense/heal moves as data, `battle.py` is pure turn-resolution logic with no I/O (and the only tested code in this project — see `test_battle.py`), and `game.py` is the CLI loop (banner, menus, input handling) that ties them together. The move numbers/effects and full turn-resolution rules are documented in `docs/superpowers/specs/2026-08-14-squirrel-fight-design.md`.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "Document Squirrel Fight in CLAUDE.md"
```

---

## Self-review notes

- **Spec coverage:** premise/structure/AI (Task 5), all 12 moves with exact numbers (Task 2), full turn-resolution rules including the HP-clamping order (Task 4), HP bar display (Task 5), error handling for move input (Task 5, Step 3), testing (Tasks 1, 3, 4), architecture/file layout (Tasks 2/4/5/6), out-of-scope items (no graphics, no API, no cooldowns, no difficulty levels) are simply absent from the implementation, as intended.
- **Type consistency:** `Fighter`, `Move`, `TurnResult`, `FighterTurnOutcome`, `resolve_turn`, and `battle_outcome` are named and shaped identically everywhere they're used across Tasks 2-5 (verified by actually running this exact code against this exact test suite before writing it into this plan — all 13 tests passed).
- **No placeholders:** every step above has complete, runnable code — nothing deferred to "later."
