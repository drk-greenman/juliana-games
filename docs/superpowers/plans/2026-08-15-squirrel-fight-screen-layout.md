# Squirrel Fight Screen Layout Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework `squirrel-fight/game.py`'s per-turn screen output so the result of the
last move is never buried under a reprinted move menu, following
`docs/superpowers/specs/2026-08-15-squirrel-fight-screen-layout-design.md`.

**Architecture:** Single-file change to `squirrel-fight/game.py`. Add a `clear_screen()`
helper and a two-beat turn draw (Beat 1: HP + recap of the last turn, paused on Enter;
Beat 2: HP + a compact, color-coded move menu). Split the existing move menu into a
colored compact form (numbers + names only) and a colored detailed form (with
descriptions, shown on demand via typing `?`). `battle.py` and `moves.py` are untouched.

**Tech Stack:** Python 3, standard library only (`os` for `os.system` screen clear,
raw ANSI escape codes for color — no new dependency).

---

## Before you start

All commands below assume you're in the repo root `/Users/kgreenman/git/juliana-games`
unless a step says `cd squirrel-fight` first. The current `squirrel-fight/game.py` (127
lines) is the starting point for every "Modify" reference below — none of these tasks
have been applied yet.

Note: Tasks 1–6 verify each new/renamed function in isolation via `python3 -c`. Between
Task 3 and Task 7, `play_battle()` still calls the *old* function names (`print_menu()`,
`print_turn_result()`) internally, so running the full game with `python3 game.py`
during that window will crash — that's expected and fine, since nothing in Tasks 1–6
runs `play_battle()`. Task 7 rewrites `play_battle()` to call the new functions, and is
the first point the full game is playable end-to-end again.

---

### Task 1: Add color constants and `clear_screen()` helper

**Files:**
- Modify: `squirrel-fight/game.py:1` (import), `squirrel-fight/game.py:25` (after
  `HP_BAR_WIDTH`)

- [ ] **Step 1: Add the `os` import**

Replace:
```python
import random

from battle import Fighter, resolve_turn, battle_outcome
from moves import MOVES
```

With:
```python
import os
import random

from battle import Fighter, resolve_turn, battle_outcome
from moves import MOVES
```

- [ ] **Step 2: Add color constants and `clear_screen()` right after `HP_BAR_WIDTH`**

Replace:
```python
HP_BAR_WIDTH = 20


def hp_bar(fighter: Fighter) -> str:
```

With:
```python
HP_BAR_WIDTH = 20

COLOR_RESET = "\033[0m"
MOVE_KIND_COLOR = {
    "attack": "\033[91m",
    "defense": "\033[96m",
    "heal": "\033[92m",
}


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def hp_bar(fighter: Fighter) -> str:
```

- [ ] **Step 3: Verify**

Run:
```bash
cd squirrel-fight && python3 -c "import game; print(game.MOVE_KIND_COLOR); game.clear_screen()"
```
Expected: prints `{'attack': '\x1b[91m', 'defense': '\x1b[96m', 'heal': '\x1b[92m'}`, the
screen clears (or the clear is a no-op in a non-interactive shell), no traceback.

- [ ] **Step 4: Commit**

```bash
git add squirrel-fight/game.py
git commit -m "Add color constants and clear_screen() helper to squirrel-fight/game.py"
```

---

### Task 2: Add `print_header()`

**Files:**
- Modify: `squirrel-fight/game.py` (insert after `print_status`, currently lines 35-37)

- [ ] **Step 1: Insert `print_header()` after `print_status()`**

Replace:
```python
def print_status(player: Fighter, computer: Fighter) -> None:
    print(f"\n  {player.name:<20} {hp_bar(player)}")
    print(f"  {computer.name:<20} {hp_bar(computer)}\n")


def print_menu() -> None:
```

With:
```python
def print_status(player: Fighter, computer: Fighter) -> None:
    print(f"\n  {player.name:<20} {hp_bar(player)}")
    print(f"  {computer.name:<20} {hp_bar(computer)}\n")


def print_header(player: Fighter, computer: Fighter) -> None:
    print(f"  🐿️  SQUIRREL FIGHT — {player.name} vs. {computer.name}")


def print_menu() -> None:
```

- [ ] **Step 2: Verify**

Run:
```bash
cd squirrel-fight && python3 -c "
from battle import Fighter
import game
game.print_header(Fighter('Juliana', 60, 60), Fighter('Mr. Wigglebottom', 60, 60))
"
```
Expected:
```
  🐿️  SQUIRREL FIGHT — Juliana vs. Mr. Wigglebottom
```

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/game.py
git commit -m "Add print_header() to squirrel-fight/game.py"
```

---

### Task 3: Rename `print_menu()` to `print_move_details()` and color it by category

**Files:**
- Modify: `squirrel-fight/game.py` (the `print_menu` function, currently lines 40-49)

- [ ] **Step 1: Replace `print_menu()` with a colored `print_move_details()`**

Replace:
```python
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
```

With:
```python
def print_move_details() -> None:
    color = MOVE_KIND_COLOR["attack"]
    print(f"  {color}Attacks:{COLOR_RESET}")
    for i, move in enumerate(MOVES[:7], start=1):
        print(f"  {color}  {i}) {move.name} - {move.description}{COLOR_RESET}")
    color = MOVE_KIND_COLOR["defense"]
    print(f"  {color}Defenses:{COLOR_RESET}")
    for i, move in enumerate(MOVES[7:11], start=8):
        print(f"  {color}  {i}) {move.name} - {move.description}{COLOR_RESET}")
    color = MOVE_KIND_COLOR["heal"]
    print(f"  {color}Heal:{COLOR_RESET}")
    for i, move in enumerate(MOVES[11:], start=12):
        print(f"  {color}  {i}) {move.name} - {move.description}{COLOR_RESET}")
```

- [ ] **Step 2: Verify**

Run:
```bash
cd squirrel-fight && python3 -c "import game; game.print_move_details()" | cat -v | head -3
```
Expected: lines wrapped in escape codes, e.g. a first line starting `  ^[[91mAttacks:^[[0m`
and a second line starting `  ^[[91m  1) Tail Smack - A reliable melee whack.^[[0m` —
confirming both the header and each move line are wrapped in the attack color.

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/game.py
git commit -m "Rename print_menu() to print_move_details() and color by move category"
```

---

### Task 4: Add `print_menu_compact()`

**Files:**
- Modify: `squirrel-fight/game.py` (insert after `print_move_details()`)

- [ ] **Step 1: Insert a row-grouping helper and `print_menu_compact()`**

Replace:
```python
def prompt_move(fighter_name: str):
```

With:
```python
def _print_move_row_group(entries: list[str], color: str, row_size: int) -> None:
    for i in range(0, len(entries), row_size):
        row = entries[i:i + row_size]
        print(f"  {color}  " + "   ".join(row) + COLOR_RESET)


def print_menu_compact() -> None:
    color = MOVE_KIND_COLOR["attack"]
    print(f"  {color}Attacks:{COLOR_RESET}")
    entries = [f"{i}) {move.name}" for i, move in enumerate(MOVES[:7], start=1)]
    _print_move_row_group(entries, color, row_size=3)

    color = MOVE_KIND_COLOR["defense"]
    print(f"  {color}Defenses:{COLOR_RESET}")
    entries = [f"{i}) {move.name}" for i, move in enumerate(MOVES[7:11], start=8)]
    _print_move_row_group(entries, color, row_size=4)

    color = MOVE_KIND_COLOR["heal"]
    print(f"  {color}Heal:{COLOR_RESET}")
    entries = [f"{i}) {move.name}" for i, move in enumerate(MOVES[11:], start=12)]
    _print_move_row_group(entries, color, row_size=4)


def prompt_move(fighter_name: str):
```

- [ ] **Step 2: Verify**

Run:
```bash
cd squirrel-fight && python3 -c "import game; game.print_menu_compact()" | cat -v
```
Expected (escape codes shown as `^[[...`, omitted below for readability — confirm they
wrap each line):
```
  Attacks:
    1) Tail Smack   2) Cheek Barrel   3) Acorn Blast
    4) Scratch   5) Chirp   6) Chirp Insanely
    7) Steal
  Defenses:
    8) Dance   9) Moonwalk   10) Scurry   11) Flex
  Heal:
    12) Eat Garden
```

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/game.py
git commit -m "Add print_menu_compact() to squirrel-fight/game.py"
```

---

### Task 5: Replace `print_turn_result()` with `format_turn_result_lines()`

**Files:**
- Modify: `squirrel-fight/game.py` (the `print_turn_result` function, currently lines
  64-85)

- [ ] **Step 1: Replace the printing function with a line-returning function**

Replace:
```python
def print_turn_result(player: Fighter, computer: Fighter, player_move, computer_move, result) -> None:
    print(f"\n  {player.name} uses {result.fighter_a.move_name}!")
    print(f"  {computer.name} uses {result.fighter_b.move_name}!")
    if result.flavor_text:
        print(f"  {result.flavor_text}")
    if result.fighter_b.dodged:
        print(f"  {computer.name} dodges out of the way!")
    if result.fighter_a.damage_dealt:
        print(f"  {player.name} hits {computer.name} for {result.fighter_a.damage_dealt} damage!")
    elif player_move.kind == "attack" and (computer_move.block_reduction is not None or computer_move.block_flat is not None):
        print(f"  {computer.name} fully blocks the attack!")
    if result.fighter_a.dodged:
        print(f"  {player.name} dodges out of the way!")
    if result.fighter_b.damage_dealt:
        print(f"  {computer.name} hits {player.name} for {result.fighter_b.damage_dealt} damage!")
    elif computer_move.kind == "attack" and (player_move.block_reduction is not None or player_move.block_flat is not None):
        print(f"  {player.name} fully blocks the attack!")
    if result.fighter_a.healed:
        print(f"  {player.name} heals {result.fighter_a.healed} HP!")
    if result.fighter_b.healed:
        print(f"  {computer.name} heals {result.fighter_b.healed} HP!")
    print_status(player, computer)
```

With:
```python
def format_turn_result_lines(player: Fighter, computer: Fighter, player_move, computer_move, result) -> list[str]:
    lines = [
        f"  {player.name} uses {result.fighter_a.move_name}!",
        f"  {computer.name} uses {result.fighter_b.move_name}!",
    ]
    if result.flavor_text:
        lines.append(f"  {result.flavor_text}")
    if result.fighter_b.dodged:
        lines.append(f"  {computer.name} dodges out of the way!")
    if result.fighter_a.damage_dealt:
        lines.append(f"  {player.name} hits {computer.name} for {result.fighter_a.damage_dealt} damage!")
    elif player_move.kind == "attack" and (computer_move.block_reduction is not None or computer_move.block_flat is not None):
        lines.append(f"  {computer.name} fully blocks the attack!")
    if result.fighter_a.dodged:
        lines.append(f"  {player.name} dodges out of the way!")
    if result.fighter_b.damage_dealt:
        lines.append(f"  {computer.name} hits {player.name} for {result.fighter_b.damage_dealt} damage!")
    elif computer_move.kind == "attack" and (player_move.block_reduction is not None or player_move.block_flat is not None):
        lines.append(f"  {player.name} fully blocks the attack!")
    if result.fighter_a.healed:
        lines.append(f"  {player.name} heals {result.fighter_a.healed} HP!")
    if result.fighter_b.healed:
        lines.append(f"  {computer.name} heals {result.fighter_b.healed} HP!")
    return lines
```

Note this drops the leading `\n` (screen clearing handles spacing now) and the trailing
`print_status(player, computer)` call (the two-beat loop in Task 7 calls `print_status`
directly instead, since it's now needed in both beats, not just after the recap).

- [ ] **Step 2: Verify**

Run:
```bash
cd squirrel-fight && python3 -c "
import random
random.seed(1)
from battle import Fighter, resolve_turn
from moves import MOVES
import game
player = Fighter('Juliana', 60, 60)
computer = Fighter('Rival', 60, 60)
result = resolve_turn(player, MOVES[0], computer, MOVES[1])
lines = game.format_turn_result_lines(player, computer, MOVES[0], MOVES[1], result)
print(type(lines), len(lines))
for line in lines:
    print(line)
"
```
Expected: `<class 'list'> N` (N is at least 4: the two "uses" lines plus at least one hit
line each way), followed by lines like `  Juliana uses Tail Smack!`, `  Rival uses Cheek
Barrel!`, and two "hits ... for ... damage!" lines. No traceback.

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/game.py
git commit -m "Replace print_turn_result() with format_turn_result_lines()"
```

---

### Task 6: Add `?` (move details) handling to `prompt_move()`

**Files:**
- Modify: `squirrel-fight/game.py` (the `prompt_move` function, currently lines 52-57)

- [ ] **Step 1: Update `prompt_move()`**

Replace:
```python
def prompt_move(fighter_name: str):
    while True:
        choice = input(f"  {fighter_name}, pick a move (1-12): ").strip()
        if choice.isascii() and choice.isdigit() and 1 <= int(choice) <= len(MOVES):
            return MOVES[int(choice) - 1]
        print("  Not a valid move, try again.")
```

With:
```python
def prompt_move(fighter_name: str):
    while True:
        choice = input(f"  {fighter_name}, pick a move (1-12, or ? for move details): ").strip()
        if choice == "?":
            print()
            print_move_details()
            print()
            continue
        if choice.isascii() and choice.isdigit() and 1 <= int(choice) <= len(MOVES):
            return MOVES[int(choice) - 1]
        print("  Not a valid move, try again.")
```

- [ ] **Step 2: Verify**

Run:
```bash
cd squirrel-fight && printf "?\n1\n" | python3 -c "
import game
move = game.prompt_move('Juliana')
print('CHOSE:', move.name)
"
```
Expected: the colored detailed move list prints first (12 move lines with
descriptions), followed by `CHOSE: Tail Smack`, confirming `?` reprints details and
still lets a follow-up number choice go through. No traceback.

- [ ] **Step 3: Commit**

```bash
git add squirrel-fight/game.py
git commit -m "Add ? (move details) handling to prompt_move()"
```

---

### Task 7: Restructure `play_battle()` into the two-beat turn loop

**Files:**
- Modify: `squirrel-fight/game.py` (the `play_battle` function, currently lines 88-112)

- [ ] **Step 1: Replace `play_battle()`**

Replace:
```python
def play_battle() -> None:
    name = input("  Name your squirrel: ").strip() or "You"
    player = Fighter(name=name, hp=60, max_hp=60)
    computer = Fighter(name=random.choice(RIVAL_NAMES), hp=60, max_hp=60)

    print(f"\n  {player.name} vs. {computer.name}! Let the fight begin!\n")
    print_status(player, computer)

    while True:
        print_menu()
        player_move = prompt_move(player.name)
        computer_move = computer_choose_move()
        result = resolve_turn(player, player_move, computer, computer_move)
        print_turn_result(player, computer, player_move, computer_move, result)

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
```

With:
```python
def play_battle() -> None:
    name = input("  Name your squirrel: ").strip() or "You"
    player = Fighter(name=name, hp=60, max_hp=60)
    computer = Fighter(name=random.choice(RIVAL_NAMES), hp=60, max_hp=60)

    recap_lines = [f"  {player.name} vs. {computer.name}! Let the fight begin!"]

    while True:
        # Beat 1: recap of the last turn (or the intro line, on turn 1)
        clear_screen()
        print_header(player, computer)
        print_status(player, computer)
        for line in recap_lines:
            print(line)
        print()

        outcome = battle_outcome(player, computer)
        if outcome != "ongoing":
            if outcome == "draw":
                print("  Both squirrels are down! It's a draw!\n")
            elif outcome == "a_wins":
                print(f"  {player.name} wins!\n")
            elif outcome == "b_wins":
                print(f"  {computer.name} wins!\n")
            break

        input("  Press Enter to continue...")

        # Beat 2: the move menu
        clear_screen()
        print_header(player, computer)
        print_status(player, computer)
        print("  " + "-" * 45)
        print_menu_compact()
        print()

        player_move = prompt_move(player.name)
        computer_move = computer_choose_move()
        result = resolve_turn(player, player_move, computer, computer_move)
        recap_lines = format_turn_result_lines(player, computer, player_move, computer_move, result)
```

- [ ] **Step 2: Verify with a full scripted playthrough**

Run:
```bash
cd squirrel-fight
{
  echo "Juliana"
  for i in $(seq 1 30); do echo ""; echo "1"; done
} | python3 game.py
```
Expected: the output shows the two-beat structure repeating — a header/HP/recap block,
then `Press Enter to continue...`, then a header/HP/divider/menu block, then a move
prompt — across multiple turns, ending in a line containing `wins!` or `draw!`, with no
Python traceback. (The player always picks move 1/Tail Smack, guaranteeing at least
10 damage per player turn against a 60 HP rival, so 30 scripted turns is comfortably
enough for the battle to conclude. If it somehow doesn't, you'll see an `EOFError` —
just bump the `seq 1 30` count and rerun; it isn't a sign of a bug.)

- [ ] **Step 3: Play it for real**

Run `python3 game.py` (no piped input) in an actual terminal and play a couple of
turns, including typing `?` at least once at a move prompt. Confirm: the screen
visibly clears between beats, the HP/recap appear before you're asked to continue,
the compact menu is colored by category (red attacks, cyan defenses, green heal),
and `?` shows the full descriptions in the same colors.

- [ ] **Step 4: Commit**

```bash
git add squirrel-fight/game.py
git commit -m "Restructure play_battle() into a two-beat clear-screen turn flow"
```

---

## Explicitly out of scope (matches the design spec)

- Terminal-capability detection / graceful color fallback
- Coloring anything other than move categories (HP bars, recap text, player-vs-rival
  distinction)
- Preserving scrollback of past turns
- Any change to `battle.py` or `moves.py`
