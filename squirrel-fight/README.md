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

The window version draws simple placeholder squirrels until you give it real
art. Drop PNG files into `squirrel-fight/assets/` and they show up next run —
no code changes needed.

Start with these two:

- `assets/player_idle.png`
- `assets/rival_idle.png`

Make them PNGs with a see-through background, roughly 200×200, with the
squirrel **facing right**. The rival gets flipped automatically, so both
drawings face the same way.

Once those work, these are all optional and each one replaces a placeholder:

| File | When it shows |
| --- | --- |
| `player_hurt.png`, `rival_hurt.png` | While getting hit |
| `player_attack.png`, `rival_attack.png` | While lunging |
| `background.png` | Instead of the plain sky and grass |

Any file you haven't drawn yet just falls back to the one you have, so you can
add them one at a time.

## Run the tests

```bash
python3 -m pytest squirrel-fight/
```

`test_battle.py` covers the fight maths and `test_choreography.py` covers the
animation timeline. The pygame drawing code has no tests — like `game.py`, it's
checked by playing it.

## How the code is split

| File | What it does |
| --- | --- |
| `moves.py` | The 12 moves, as data |
| `battle.py` | Turn resolution. Pure logic, no input or output |
| `game.py` | The terminal version |
| `visual_game.py` | The window version |
| `choreography.py` | Turns a resolved turn into animation. Pure, no pygame |
| `sprites.py` | Loads drawings, falls back to code-drawn squirrels |
