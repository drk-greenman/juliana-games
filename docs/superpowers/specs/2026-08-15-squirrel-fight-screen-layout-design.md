# Squirrel Fight — Screen Layout Redesign

Reworks how `squirrel-fight/game.py` draws each turn to fix readability during play.
Today, the full 12-move menu (with descriptions) reprints every turn directly after
the turn's outcome, so the interesting part — what just happened — gets buried under
menu text almost immediately, and the whole thing scrolls into one long wall of text
over a multi-turn battle. This is a `game.py`-only change: `battle.py`'s turn
resolution logic and `moves.py`'s move data are untouched.

## Two-beat turn flow

Each turn clears the screen (`os.system("cls" if os.name == "nt" else "clear")`) and
redraws in two beats, so the result of the last move and the menu for the next one are
never on screen fighting for attention at the same time.

**Beat 1 — Recap.** Clear, then show:
1. A slim one-line header: `🐿️  SQUIRREL FIGHT — {player.name} vs. {computer.name}`
2. Both fighters' HP bars (existing `hp_bar()` format, unchanged)
3. A recap of what just happened last turn (moves used, damage, dodges, blocks,
   heals — the existing content of `print_turn_result()`, minus the HP-bar printing
   it currently does at the end, since HP bars are now always printed as part of
   this beat directly)
4. `Press Enter to continue...` and wait for input (value discarded)

On turn 1, there is no prior turn yet — the recap section instead shows
`{player.name} vs. {computer.name}! Let the fight begin!`, matching today's intro
line.

**Beat 2 — Menu.** Clear again, then show:
1. The same header and HP bars as Beat 1 (recap is dropped — it already had its
   moment in Beat 1)
2. A divider line (`-` × 45)
3. The compact move menu (see below)
4. The move prompt: `{fighter_name}, pick a move (1-12, or ? for move details):`

If the battle ends this turn (`battle_outcome()` returns anything other than
"ongoing"), Beat 2 is skipped entirely: Beat 1's recap is followed directly by the
win/lose/draw line, and the loop exits straight into the existing
`Play again? (y/n)` prompt in `main()` — no extra pause, since that input prompt
already holds the final screen in place until the player responds.

## Compact menu vs. on-demand details

The Beat 2 menu drops the per-move descriptions and lays out several moves per line
instead of one, grouped under the existing category headers:

```
Attacks:
  1) Tail Smack   2) Cheek Barrel   3) Acorn Blast
  4) Scratch      5) Chirp          6) Chirp Insanely
  7) Steal
Defenses:
  8) Dance   9) Moonwalk   10) Scurry   11) Flex
Heal:
  12) Eat Garden
```

Typing `?` at the move prompt prints today's full descriptive menu (one move per
line, `name - description`) directly below the compact menu — no screen clear — then
re-prompts. Typing a move number directly still works at any time, with or without
ever pressing `?` first. `?` is a third accepted input alongside numbers and invalid
input, not a replacement for either.

## Color-coded move categories

Each category gets a consistent ANSI color, applied to that category's header and
every move line under it, in both the compact menu and the `?` detailed list:

- **Attacks** — red (`\033[91m`)
- **Defenses** — cyan (`\033[96m`)
- **Heal** — green (`\033[92m`)

Colors are plain ANSI escape codes wrapped around each category's output — no new
dependency. Nothing else (header, HP bars, recap text, prompts) is colored. No
terminal-capability detection: this repo's games are run from Terminal.app/iTerm on
macOS per `CLAUDE.md`, both of which support ANSI color, so this stays unconditional
rather than adding fallback logic for a case that doesn't occur in practice.

## Code structure

All changes are within `squirrel-fight/game.py`; no changes to `battle.py`,
`moves.py`, or their tests.

- `clear_screen()` — new helper, wraps the `os.system` call
- `format_turn_result_lines(player, computer, player_move, computer_move, result) -> list[str]`
  — replaces `print_turn_result()`; same content, returns lines instead of printing
  them, and no longer calls `print_status()` itself (the two-beat loop calls
  `print_status()` directly in both beats)
- `print_menu_compact()` — new, colored, description-free menu (replaces the old
  `print_menu()` call site in the turn loop)
- `print_move_details()` — the existing `print_menu()` body (full descriptions),
  renamed and now also colored by category; invoked when `prompt_move()` sees `?`
- `prompt_move()` — extended to treat `?` as a request to call `print_move_details()`
  and re-prompt, rather than falling through to "Not a valid move, try again"
- `play_battle()` — restructured around the two-beat loop described above, tracking
  the current recap lines and an optional outcome message between iterations

## Error handling

Unchanged from today: the only input surface is the move prompt, and it already
handles invalid input by re-prompting without ending the turn. `?` is added as a
recognized non-error input at that same prompt. No new failure modes are introduced;
`os.system("clear")` failing is not handled specially (it isn't expected to fail on
the supported platform, and worst case leaves old output on screen rather than
crashing).

## Testing

No new automated tests. `battle.py` remains the only tested code in this project —
this change is entirely presentational (`game.py`'s I/O loop), which the existing
project convention already excludes from the test suite. Verified by playing the
game manually.

## Explicitly out of scope

- Terminal-capability detection / graceful color fallback
- Coloring anything other than move categories (HP bars, recap text, player-vs-rival
  distinction) — considered and deferred, not forgotten
- Scrollback/history of past turns (Beat 1's screen clear means only the immediately
  prior turn is visible; this is an intentional trade-off, not a gap)
- Changing `battle.py` or `moves.py` in any way
