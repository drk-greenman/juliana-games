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
