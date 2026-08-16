# Handoff — Squirrel Fight visual version

**Written:** 2026-08-15, at the end of the brainstorm-and-plan session.
**Status:** Design and plan are finished and committed. **No implementation code exists yet.** The next action is Task 1 of the plan.

---

## Paste this into the fresh session

> Read `docs/superpowers/plans/2026-08-15-squirrel-fight-visuals-handoff.md`, then implement `docs/superpowers/plans/2026-08-15-squirrel-fight-visuals.md` task by task.

**One question is still open and needs answering before work starts:** execution mode.

- **Subagent-driven** (was the recommendation) — a fresh subagent per task, review between tasks. Uses the `superpowers:subagent-driven-development` skill.
- **Inline** — execute in the session with checkpoints. Uses the `superpowers:executing-plans` skill.

Task 2 and Task 7–11 need a human to actually look at a game window and confirm the squirrels look right, so those verification steps can't be fully delegated either way.

---

## What is being built

A second way to play Squirrel Fight: a pygame window where two hand-drawn squirrels lunge, stagger, flash red and glow green as each turn resolves, with clickable move buttons and sliding HP bars. The existing terminal game keeps working, untouched. Both versions import the same `battle.py` and `moves.py`, so the fight rules live in exactly one place.

Juliana is drawing the squirrels herself, and hasn't started. **The game must be fully playable before any drawing exists** — every missing image falls back to a code-drawn placeholder squirrel. This is a hard requirement, not a nicety; it's what lets art arrive one file at a time.

## The two documents

| Document | What it's for |
| --- | --- |
| `docs/superpowers/specs/2026-08-15-squirrel-fight-visuals-design.md` | Why and what. Read this if a plan task seems wrong or underspecified. |
| `docs/superpowers/plans/2026-08-15-squirrel-fight-visuals.md` | How. 12 tasks with complete code and exact commands. |

The plan is self-contained — it does not assume you've read the spec.

## Decisions already made — don't reopen these

Each was chosen deliberately, with the alternatives considered and rejected.

| Decision | Why |
| --- | --- |
| pygame window, not terminal art or a web page | Real image files and real motion were the point of the request. |
| One drawing per squirrel, moved by code — not frame-by-frame animation | Looks the most alive for the fewest drawings. Frame animation needs dozens of PNGs; this needs two. |
| `visual_game.py` beside `game.py` in the same folder | Shares `battle.py` and `moves.py` with no `sys.path` hacks and no duplicated fight rules. A separate folder was rejected for exactly that reason. |
| Engine first, art drops in later | Nothing blocks on a drawing being finished, and no step gets rewritten by a later one. |
| `choreography.py` imports no pygame | It's the only new logic worth testing. Keeping it pure is what makes that possible. |
| `pygame-ce`, in a project-level `requirements.txt` | `CLAUDE.md` names pygame as the case for splitting dependencies, so `word-combo-story` doesn't inherit a graphics library. `pygame-ce` imports as `pygame` — no code differences. |
| Art comes only from Juliana's own drawings | Not AI-generated, not free sprite packs. This was an explicit choice. |

## Environment constraints that will cause confusing failures

1. **Python is 3.9.6** (`/usr/bin/python3`, the macOS system python). `X | None` union syntax is a runtime syntax error unless the module starts with `from __future__ import annotations` — which is exactly why `battle.py` and `moves.py` already have that line. Every new module in the plan has it. No `match` statements.
2. **Use `python3`, never `python`.** There is no `python` on the PATH.
3. **pygame is not installed.** Task 1 installs it. Packages land in `~/Library/Python/3.9/lib/python/site-packages/`, alongside the existing pytest 8.4.2.
4. **`squirrel-fight/` has a hyphen**, so it can never be a Python package. There is no `__init__.py` and none should be added. Tests import modules as bare top-level names (`import battle`), relying on pytest putting the test file's own directory on `sys.path` — this is how `test_battle.py` already works.
5. **A real display is required** to verify anything visual. `pygame.display.set_mode()` raises `pygame.error` over plain SSH.

## Files that must not change

`battle.py`, `moves.py`, `game.py`, `test_battle.py`.

Task 12 verifies this, but check it any time you're unsure:

```bash
git diff --stat main -- squirrel-fight/game.py squirrel-fight/battle.py squirrel-fight/moves.py squirrel-fight/test_battle.py
```

Expected: no output whatsoever. `visual_game.py` imports `RIVAL_NAMES` from `game.py` — that's a read, not a modification, and importing `game` has no side effects because its `main()` is guarded by `if __name__ == "__main__"`.

## Traps already found, and where they're handled

These were caught while writing the plan. The plan's code is already correct — this list exists so nobody "fixes" them back.

- **`resolve_turn()` mutates `Fighter.hp` in place.** `visual_game.take_turn()` must snapshot HP *before* calling it. Losing this makes every HP bar animate from its final value to itself.
- **A fighter can heal and take damage in the same turn** (`Eat Garden` into an attack), needing two chained HP slides. `battle.py` clamps the *net* change, not each part, so recomputing an intermediate value can disagree with reality. `_build_hp_tweens` pins the last slide directly to `hp_after` instead of recomputing.
- **The faint cue must be stretched to the end of the timeline**, and `total_ms` must account for the topple before the faint cues are appended. An earlier draft computed the length first and the loser froze at 72° instead of falling all the way over.
- **Never colour the surface `sprites.load_pose()` returns** — it's cached and shared. `_draw_squirrel` copies before tinting.
- **Every animation effect returns a neutral state at progress 0**, except `flash`, which is loudest on impact and fades. A parametrised test enforces this.

## Open items

- **Keyboard shortcuts differ slightly from what was originally described.** A single keystroke can't express "12", so shortcuts run along the number row: `1`–`9` for moves 1–9, then `0`, `-`, `=` for 10–12. Buttons stay labelled 1–12 to match the terminal game. This was flagged to the user, who hasn't responded — if they'd rather have letter keys for the four defenses, it's a small change to `SHORTCUT_KEYS` in `visual_game.py` and the hint text on the title screen.
- **A flying acorn for `Acorn Blast`** is written up at the bottom of the plan as an optional follow-up. It's out of scope because it changes the `ActorState` shape.
- **Animation timing may need tuning by feel.** A full turn is 1920 ms. Task 9 Step 2 covers adjusting `ACTION_MS` and `TAIL_MS` if it drags.

## Verifying at any point

```bash
python3 -m pytest squirrel-fight/ -v      # battle tests + choreography tests
python3 squirrel-fight/game.py            # terminal version must still work
python3 squirrel-fight/visual_game.py     # the window version (exists from Task 7 on)
```

## Git state at handoff

Branch `main`, working tree clean.

```
1ada429 Add implementation plan for Squirrel Fight's visual version
419f1f1 Add design spec for Squirrel Fight's visual (pygame) version
5e0ca6b Add more silly rival squirrel names        <- last commit before this work
```

Nothing has been pushed; there's no branch for the implementation yet. Creating one before Task 1 is reasonable, since `main` is the default branch.

The `.superpowers/` directory holds throwaway mockups from the design session and is gitignored — ignore it.
