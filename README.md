# juliana-games

A place for Juliana to create things with code! This is where funny games, stories, and all kinds of creative projects come to life.

This repo is also an experiment in learning how coding with Claude works — so expect lots of cool ideas, weird experiments, and maybe a few silly stories along the way.

## What you'll find here

- 🎮 Funny games
- 📖 Stories
- 🛠️ Whatever Juliana decides to build next

## Projects

Each game/story lives in its own folder with its own `README.md`.

- [`word-combo-story/`](word-combo-story/) — pick a silly word combo, describe it, and get a short AI-written story about it.
- [`squirrel-fight/`](squirrel-fight/) — name your squirrel and duel a randomly-named rival with silly attack, defense, and heal moves.

## Setup

```bash
pip install -r requirements.txt
```

Some projects use Claude and need an Anthropic API key — check a project's own `README.md` to see if it does. Add the key to a `.env` file in the repo root (shared by all projects that need one):

```bash
echo 'ANTHROPIC_API_KEY=your-key-here' > .env
```
