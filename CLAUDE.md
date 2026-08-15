# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A place for Juliana to create things with code — funny games, stories, and creative coding experiments. It also doubles as a learning experiment in coding with Claude, so expect a casual, playful tone in both the code and the outputs it generates.

## Setup and running

```bash
pip install -r requirements.txt
python <project-folder>/game.py     # e.g. python word-combo-story/game.py
```

Requires an `ANTHROPIC_API_KEY` in a `.env` file in the repo root (loaded via `python-dotenv`, gitignored). It's shared across all projects — `load_dotenv()` walks up from a script's own folder to find it, so this works regardless of which project folder you run from. If the key is missing, a game should print setup instructions and exit rather than crashing (see `word-combo-story/game.py`'s `get_client()` for the pattern).

There is no build step, linter, or test suite configured in this repo.

## Architecture

This is a multi-project repo: each game/story lives in its own top-level folder (e.g. `word-combo-story/`) with its own entry script and a short project-level `README.md` describing what it is and how to run it. Dependencies (`requirements.txt`) and the API key (`.env`) are shared at the repo root rather than per-project — split a project out with its own requirements only if it needs something the others don't (e.g. pygame, pillow). The root `README.md` keeps a linked list of projects; add new games there too.

Within a project folder, expect a standalone script style (no shared framework/engine across games) unless the user asks to factor out common code.

- `word-combo-story/game.py`: picks a random adjective + noun combo, prompts the player to describe what it is, then streams a short kid-friendly story from Claude (`claude-haiku-4-5-20251001` via the `anthropic` SDK's `messages.stream`) back to the terminal. The word lists (`ADJECTIVES`, `NOUNS`) are the main tunable content — edits there are the most common kind of change requested for this game.
