"""Turns one borrowed squirrel into a whole roster of them.

`source-art/sqrl_5frames.png` is a CC0 run cycle by alizard (see that folder's
CREDITS.md) — one squirrel, five frames, white background. Drawing seven more
rivals by hand is a lot of drawing, so instead this picks three frames out of the
run cycle to stand in for the three poses the game asks for, and repaints the fur
once per rival. Same squirrel underneath, but a purple one reads as a different
fighter from a pink one, which is all the stage needs.

Re-run it any time the colours want changing — it only ever writes the files it
generates, so hand-drawn squirrels in `assets/` are safe:

    python3 squirrel-fight/make_sprites.py

The fur colours below are the fun part to edit.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

HERE = Path(__file__).parent
SOURCE = HERE / "source-art" / "sqrl_5frames.png"
ASSETS_DIR = HERE / "assets"

# The source has no alpha channel, so its background arrived as solid white.
# Every pixel this colour becomes see-through; everything else is squirrel.
BACKGROUND = (255, 255, 255)

# The three colours the original squirrel's fur is painted in. Swapping these is
# what makes one rival look different from the next, so they're looked up by
# exact value rather than nudged by hue — a squirrel is only ~700 pixels and the
# palette is this short, so there's nothing subtler to preserve.
SOURCE_MAIN = (175, 94, 45)
SOURCE_DARK = (140, 67, 23)
SOURCE_LIGHT = (214, 175, 151)
SOURCE_LIGHT_ALT = (209, 164, 136)

# Which frame of the run cycle stands in for each pose. `visual_game` asks for
# "idle", "attack" and "hurt"; an empty pose name means the plain `<name>.png`,
# which is both the idle drawing and the file that makes `available_squirrels()`
# offer this squirrel as a fighter at all.
#   frame 0 — feet together and planted, so it reads as standing about
#   frame 3 — stretched out flat and low, which looks near enough to a lunge
#   frame 2 — tail dropped and legs trailing behind, i.e. reeling backwards
POSE_FRAMES = {"": 0, "attack": 3, "hurt": 2}

# (main fur, shading, belly) per rival. The keys have to match `slug(name)` for a
# name in `RIVAL_NAMES` in game.py, or the squirrel never turns up to fight.
SQUIRREL_COLORS = {
    # Bright chestnut — closest to the squirrel as drawn.
    "nutsy-mcgee": ((198, 108, 48), (152, 74, 26), (232, 190, 160)),
    # Unapologetically pink.
    "mr-tickle-bum": ((226, 122, 168), (176, 78, 124), (250, 205, 226)),
    # Chocolate, for a squirrel whose whole name is about chomping.
    "chompy-von-nutsalot": ((110, 70, 44), (74, 44, 26), (188, 152, 122)),
    # The classic grey squirrel, menacingly.
    "lord-o-grey-menace": ((136, 140, 150), (92, 96, 106), (206, 210, 218)),
    # Golden, and slightly too pleased about it.
    "sir-nuts-alot": ((214, 168, 66), (166, 122, 36), (244, 222, 162)),
    # Purple, because lords get purple.
    "lord-acornut": ((142, 104, 186), (100, 68, 140), (206, 182, 234)),
    # Electric teal — deliberately nothing like the Grey Menace above, who was
    # wearing almost this exact silver until the two of them turned out to be
    # indistinguishable on the stage.
    "elon-must": ((78, 176, 196), (40, 118, 140), (190, 232, 240)),
}


def recolor(frame: pygame.Surface, palette: tuple) -> pygame.Surface:
    """Copy `frame` onto a see-through canvas, repainting the fur as it goes."""
    main, dark, light = palette
    swaps = {
        SOURCE_MAIN: main,
        SOURCE_DARK: dark,
        SOURCE_LIGHT: light,
        SOURCE_LIGHT_ALT: light,
    }
    out = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
    for y in range(frame.get_height()):
        for x in range(frame.get_width()):
            color = frame.get_at((x, y))[:3]
            if color == BACKGROUND:
                continue  # leave it transparent
            # Anything not in the fur palette is an eye or an outline, and stays
            # dark so every squirrel keeps a face.
            out.set_at((x, y), (*swaps.get(color, color), 255))
    return out


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))  # image.load/save want a video mode set up

    sheet = pygame.image.load(str(SOURCE)).convert()
    # The frames are square and stacked in one column, so each is as tall as the
    # sheet is wide.
    frame_height = sheet.get_width()
    frames = {
        index: sheet.subsurface((0, index * frame_height, sheet.get_width(), frame_height))
        for index in set(POSE_FRAMES.values())
    }

    ASSETS_DIR.mkdir(exist_ok=True)
    written = 0
    for stem, palette in SQUIRREL_COLORS.items():
        for pose, index in POSE_FRAMES.items():
            name = "{}_{}.png".format(stem, pose) if pose else "{}.png".format(stem)
            pygame.image.save(recolor(frames[index], palette), str(ASSETS_DIR / name))
            written += 1
    print("Wrote {} drawings for {} squirrels into {}".format(
        written, len(SQUIRREL_COLORS), ASSETS_DIR
    ))


if __name__ == "__main__":
    main()
