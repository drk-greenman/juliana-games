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

## parallax_forest_pack/

- **What it is:** a layered parallax forest — back trees, light shafts, middle
  trees, foreground trunks — 272×160 per layer.
- **Artist:** Luis Zuno (@ansimuz), ansimuz.com
- **Found at:** https://opengameart.org/content/forest-background
- **Licence:** CC0 (public domain), as stated in the pack's own `license.txt`,
  which is kept alongside it.
- The pack also ships a 172KB `.psd`. Not kept — the PNG layers are what gets
  used, and the original is a click away at the link above.

`make_scenery.py` flattens the layers into `assets/background-forest.png`, and
lifts a single trunk out of the foreground layer for `assets/tree.png` — so the
tree you climb is drawn in the same hand as the forest behind it.

## iso_pines.png

- **Artist:** pistachio — https://opengameart.org/content/pixel-pine-tree-assets-10-pack
- **Licence:** CC0 (public domain).
- **Evaluated and rejected**, so the file isn't here. They are finely detailed
  realistic pines and looked wrong beside squirrels made of 8× pixels, and the
  pack's "2 trunks" turn out to be little stumps. Noted so nobody spends an
  evening rediscovering it.
