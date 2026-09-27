# Where the borrowed art came from

## sqrl_5frames.png

- **What it is:** a 5-frame squirrel run cycle, 52×52 per frame, stacked vertically.
- **Artist:** alizard
- **Found at:** https://opengameart.org/content/pixel-squirrel
- **Licence:** CC0 (public domain) — no attribution required, free to change and
  reuse. Credited here anyway, because that's the polite thing to do.

The squirrel already faces left and has a white background. `make_sprites.py`
turns the white see-through, picks one frame per pose, and recolours the fur so
each rival gets its own squirrel. Nothing in the game reads this folder —
`assets/` is the only place `sprites.py` looks.
