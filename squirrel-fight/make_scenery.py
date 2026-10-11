"""Builds the background scenes and the tree out of borrowed art.

`source-art/` holds art other people made (see its CREDITS.md). This flattens it
into the shape `sprites.load_background()` wants and writes it into `assets/`,
the same way `make_sprites.py` turns one borrowed squirrel into a roster.

    python3 squirrel-fight/make_scenes.py

Two things about background art that catch people out, both handled here:

- The loader reads scenes **without an alpha channel** and treats pure white as
  see-through. Art containing white — clouds, snow, highlights — would come out
  full of holes, so any pure white is nudged to near-white on the way through.
- The stage is 960x440, so scenes want to be about 2.2:1. Art of another shape
  is cropped rather than squashed, keeping the bottom, because that is where the
  ground is and the squirrels have to stand on it.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

HERE = Path(__file__).parent
SOURCE = HERE / "source-art"
ASSETS_DIR = HERE / "assets"

# What the stage wants. Matches sprites.STAGE_SIZE without importing pygame-heavy
# code at module scope.
STAGE_ASPECT = 960 / 440

WHITE = (255, 255, 255)
NEARLY_WHITE = (254, 254, 254)

# Luis Zuno's forest ships as separate parallax layers, back to front.
FOREST_LAYERS = (
    "parallax-forest-back-trees.png",
    "parallax-forest-lights.png",
    "parallax-forest-middle-trees.png",
    "parallax-forest-front-trees.png",
)
# The layers are transparent where the sky shows through; this is the colour
# behind them.
FOREST_SKY = (30, 40, 50)


def flatten(layers_dir: Path, names, sky) -> pygame.Surface:
    """Stack transparent parallax layers onto one opaque picture."""
    first = pygame.image.load(str(layers_dir / names[0]))
    canvas = pygame.Surface(first.get_size())
    canvas.fill(sky)
    for name in names:
        canvas.blit(pygame.image.load(str(layers_dir / name)).convert_alpha(), (0, 0))
    return canvas


def crop_to_stage(image: pygame.Surface) -> pygame.Surface:
    """Trim to the stage's shape, keeping the bottom.

    Cropping rather than scaling, because squashing a forest to a different
    aspect is very visible. The bottom is kept because that is where the ground
    is drawn, and the squirrels stand on it.
    """
    width, height = image.get_size()
    wanted = round(width / STAGE_ASPECT)
    if wanted >= height:
        return image
    return image.subsurface((0, height - wanted, width, wanted)).copy()


def unwhiten(image: pygame.Surface) -> pygame.Surface:
    """Nudge pure white off true white so it isn't keyed out as see-through."""
    out = image.copy()
    for y in range(out.get_height()):
        for x in range(out.get_width()):
            if out.get_at((x, y))[:3] == WHITE:
                out.set_at((x, y), NEARLY_WHITE)
    return out


# The trunk to lift out of the front-trees layer, and how tall to draw it.
# x155-195 is the right-hand trunk's core plus a little bark either side; the
# crop stops at the ground strip so the game's own ground shows beneath it.
TRUNK_CROP = (155, 0, 40, 133)

# Added to the trunk so it stands out from the scenery it was cut from.
TRUNK_LIFT = (46, 34, 24)


def build_tree(layers_dir: Path) -> pygame.Surface:
    """Lift one trunk out of the foreground layer.

    Using ansimuz's own trunk rather than a separate tree sprite, so the thing
    you climb is drawn in the same hand as the forest behind it. A detailed
    realistic pine was tried first and looked wrong against 8x pixel squirrels.
    """
    front = pygame.image.load(str(layers_dir / "parallax-forest-front-trees.png"))
    trunk = front.convert_alpha().subsurface(TRUNK_CROP).copy()
    # Lifted out of the gloom on purpose. Left at the layer's own colour the
    # climbable trunks were indistinguishable from the trees painted into the
    # scene behind them, and there is no way to tell by looking which ones you
    # can actually climb. Brightening reads as "this one is in front".
    trunk.fill(TRUNK_LIFT, special_flags=pygame.BLEND_RGB_ADD)
    return trunk


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))

    layers = SOURCE / "parallax_forest_pack" / "layers"
    if not layers.is_dir():
        raise SystemExit(
            "Missing {}.\nSee source-art/CREDITS.md for where it came from.".format(layers)
        )

    scene = unwhiten(crop_to_stage(flatten(layers, FOREST_LAYERS, FOREST_SKY)))
    out = ASSETS_DIR / "background-forest.png"
    pygame.image.save(scene, str(out))
    print("Wrote {} at {}x{}".format(out.name, *scene.get_size()))

    tree = build_tree(layers)
    out = ASSETS_DIR / "tree.png"
    pygame.image.save(tree, str(out))
    print("Wrote {} at {}x{}".format(out.name, *tree.get_size()))


if __name__ == "__main__":
    main()
