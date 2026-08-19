# Squirrel Fight

A 1v1 squirrel duel. Name your squirrel, pick from 12 silly attack/defense/heal
moves each turn, and battle a randomly-named rival squirrel controlled by the
computer.

There are two ways to play the same fight.

## Play in the terminal

No extra installs, works anywhere:

```bash
python3 squirrel-fight/game.py
```

## Play in a window

Squirrels that lunge, stagger and flash, with clickable moves:

```bash
python3 -m pip install -r squirrel-fight/requirements.txt
python3 squirrel-fight/visual_game.py
```

Click a move, or use the number row — `1`–`9` for the first nine moves, then
`0`, `-` and `=` for moves 10, 11 and 12. Esc quits.

Neither version needs an API key. Both are fully offline.

## Drawing your own squirrels

Drop PNG files into `squirrel-fight/assets/` and they show up next run — no code
changes needed. Any squirrel you haven't drawn yet uses a simple code-drawn
placeholder, so the game always works and just gets better one drawing at a time.

**Give each rival its own drawing** by naming the file after them, in lowercase
with dashes instead of spaces. The name has to match one in `RIVAL_NAMES` in
`game.py`, or that squirrel will never turn up to fight:

| Rival in `game.py` | Draw this file |
| --- | --- |
| `JOHN CENA` | `assets/john-cena.png` |
| `BIG BUMBOY` | `assets/big-bumboy.png` |
| `sherlock gnomes` | `assets/sherlock-gnomes.png` |

Draw them **facing left**, on a see-through background. Both styles work, and
each is handled the way it wants to be:

- **Small pixel art** (32×32 and up to 48 tall) is blown up 8×, keeping every
  pixel sharp and square.
- **Bigger freehand drawings** are resized to stand about as tall as everyone
  else, keeping their soft edges.

So a pixel squirrel and a hand-drawn one end up roughly the same size on the
stage and can fight each other quite happily.

The player's squirrel borrows one of the rivals' drawings each battle, picking
one that isn't in the fight, so you never face your own twin.

These are all optional, and each one replaces a placeholder:

| File | When it shows |
| --- | --- |
| `john-cena_hurt.png` | While that squirrel is getting hit |
| `john-cena_attack.png` | While that squirrel is lunging |
| `player_idle.png`, `rival_idle.png` | Any squirrel with no drawing of its own |
| `background.png` | The arena, behind the fight |

The background is drawn as a frame over the sky and grass, so anything you leave
**pure white** in it becomes see-through and the sky shows through the gap.

## Run the tests

```bash
python3 -m pytest squirrel-fight/
```

`test_battle.py` covers the fight maths, `test_choreography.py` covers the
animation timeline, and `test_sprites.py` covers turning a rival's name into a
filename. The pygame drawing code has no tests — like `game.py`, it's checked by
playing it.

## How the code is split

| File | What it does |
| --- | --- |
| `moves.py` | The 12 moves, as data |
| `battle.py` | Turn resolution. Pure logic, no input or output |
| `game.py` | The terminal version |
| `visual_game.py` | The window version |
| `choreography.py` | Turns a resolved turn into animation. Pure, no pygame |
| `sprites.py` | Loads drawings, falls back to code-drawn squirrels |
