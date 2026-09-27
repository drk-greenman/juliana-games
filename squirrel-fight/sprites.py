"""Loads the drawings, and copes with however many of them exist yet.

Every lookup falls back until it finds something, ending at a code-drawn
squirrel, so the game is playable with no art at all and gets better one PNG at
a time. Drawings are cached, so the fallback work happens once, not every frame.
"""

from __future__ import annotations

import re
from pathlib import Path

import pygame

ASSETS_DIR = Path(__file__).parent / "assets"

# Drawings arrive in two styles and `_fit` tells them apart by height. Anything
# this short was drawn pixel by pixel, and gets blown up by a whole number with
# nearest-neighbour sampling. One shared factor keeps a pixel the same size on
# screen for every squirrel, so a smaller drawing reads as a smaller squirrel
# rather than as the same squirrel at a different resolution.
PIXEL_SCALE = 8
PIXEL_ART_MAX_HEIGHT = 48
# Anything taller was drawn freehand, and is fitted to this height instead — so
# a 1000px drawing doesn't turn up eight times taller than the window, and the
# two styles end up roughly the same size as each other on the stage.
TARGET_HEIGHT = 180

# The stage band in visual_game, between the HP panel and the message strip.
STAGE_SIZE = (960, 440)

# The arena drawing is a frame with an empty middle, but it was exported with no
# alpha channel, so that middle arrived as solid white. Treating pure white as
# "not drawn" turns it back into a frame and lets the sky and grass show
# through. Set this to None to blit the background exactly as drawn instead.
BACKGROUND_KEY_COLOR = (255, 255, 255)

# Which way the drawings face. Juliana's all face left; the game works in
# facing-right art, so files are flipped once on load and everything downstream
# — including visual_game's "flip the rival" — stays as it was.
ART_FACES_RIGHT = False

# Reserved stems in assets/ that name something other than an individual
# squirrel, so `available_squirrels()` doesn't offer them as fighters.
RESERVED_STEMS = {"background"}
GENERIC_PREFIXES = ("player_", "rival_")

# Body colours for the code-drawn stand-in squirrels, so the two fighters are
# still tellable apart before any real art exists.
PLACEHOLDER_COLORS = {
    "player": (168, 106, 58),
    "rival": (116, 116, 132),
}

_cache: dict = {}
_background_cache: dict = {}


def slug(name: str) -> str:
    """Turn a squirrel's name into its file stem.

    `"JOHN CENA"` and `"john cena"` both become `"john-cena"`, so the drawings
    are named the way a person would name them and still match `RIVAL_NAMES`.
    Already-slugged text passes through unchanged.
    """
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_pose(side: str, pose: str, name: str | None = None) -> pygame.Surface:
    """Return one squirrel's drawing for `pose`, facing right.

    `side` is "player" or "rival"; it picks the generic art and the placeholder
    colour. `name` is the individual squirrel, so a rival with a drawing of its
    own gets it. The search runs widest-last:

        1. `<name>_<pose>.png`   this squirrel, doing this thing
        2. `<name>.png`          this squirrel, however it was drawn
        3. `<side>_<pose>.png`   any squirrel on this side, doing this thing
        4. `<side>_idle.png`     any squirrel on this side
        5. a code-drawn placeholder
    """
    key = (side, pose, name)
    if key not in _cache:
        stem = slug(name) if name else None
        candidates = []
        if stem:
            candidates.append("{}_{}".format(stem, pose))
            candidates.append(stem)
        candidates.append("{}_{}".format(side, pose))
        candidates.append("{}_idle".format(side))

        surface = None
        for candidate in candidates:
            surface = _load_file(candidate)
            if surface is not None:
                break
        if surface is None:
            surface = _draw_placeholder(side)
        _cache[key] = surface
    return _cache[key]


def available_squirrels() -> set:
    """The stems of every individual squirrel drawing in `assets/`.

    Skips the background and the generic `player_*`/`rival_*` art, and skips
    pose files like `john-cena_hurt.png` — a squirrel is offered here only if it
    has a plain `<name>.png` to stand around in.
    """
    found = set()
    if not ASSETS_DIR.is_dir():
        return found
    for path in ASSETS_DIR.glob("*.png"):
        stem = path.stem
        if stem in RESERVED_STEMS or stem.startswith(GENERIC_PREFIXES) or "_" in stem:
            continue
        found.add(stem)
    return found


def load_background() -> pygame.Surface | None:
    """Return `assets/background.png` scaled to the stage, or None if absent.

    None means "nothing drawn yet", which the caller answers with its own sky
    and grass — so this is the one loader with no placeholder of its own.
    """
    if "background" not in _background_cache:
        path = ASSETS_DIR / "background.png"
        surface = None
        if path.is_file():
            try:
                surface = pygame.transform.scale(
                    pygame.image.load(str(path)).convert(), STAGE_SIZE
                )
                if BACKGROUND_KEY_COLOR is not None:
                    # Safe to key after scaling because scale() is
                    # nearest-neighbour: it copies colours rather than blending
                    # them, so no almost-white pixels appear along the edges.
                    surface.set_colorkey(BACKGROUND_KEY_COLOR)
            except (pygame.error, OSError):
                surface = None
        _background_cache["background"] = surface
    return _background_cache["background"]


# How big a trunk is drawn on the stage: wide enough to read as a tree, tall
# enough to reach above the highest a squirrel can climb.
TREE_SIZE = (60, 300)

# Bark colours for the code-drawn stand-in trunk.
TREE_COLORS = ((104, 72, 44), (78, 52, 30))


def load_tree() -> pygame.Surface:
    """Return `assets/tree.png` at trunk size, or a code-drawn one.

    Same bargain as the squirrels: the game works with no art at all, and gets
    better the moment somebody draws a tree.
    """
    if "tree" not in _cache:
        surface = None
        path = ASSETS_DIR / "tree.png"
        if path.is_file():
            try:
                surface = pygame.transform.scale(
                    pygame.image.load(str(path)).convert_alpha(), TREE_SIZE
                )
            except (pygame.error, OSError):
                surface = None
        _cache["tree"] = surface if surface is not None else _draw_tree()
    return _cache["tree"]


def _draw_tree() -> pygame.Surface:
    """A plain trunk with a bit of bark texture, so trees read as climbable."""
    width, height = TREE_SIZE
    surface = pygame.Surface(TREE_SIZE, pygame.SRCALPHA)
    bark, dark = TREE_COLORS
    surface.fill(bark)
    # A few vertical grooves. Regular rather than random so it doesn't shimmer
    # between frames.
    for x in range(6, width, 17):
        pygame.draw.rect(surface, dark, (x, 0, 4, height))
    return surface


def clear_cache() -> None:
    """Forget every loaded drawing. Only needed if assets change while running."""
    _cache.clear()
    _background_cache.clear()


def _load_file(stem: str):
    path = ASSETS_DIR / "{}.png".format(stem)
    if not path.is_file():
        return None
    try:
        image = pygame.image.load(str(path)).convert_alpha()
    except (pygame.error, OSError):
        # Corrupt, unreadable, or vanished between the check and the load.
        # Treat it exactly like a missing file.
        return None
    if not ART_FACES_RIGHT:
        image = pygame.transform.flip(image, True, False)
    return _fit(_trim(image))


def _trim(image: pygame.Surface) -> pygame.Surface:
    """Crop away fully transparent edges.

    Without this, a squirrel drawn high in its canvas hovers above the ground,
    because the drawing is planted on the stage by the bottom of its *file*
    rather than the bottom of its feet.
    """
    bounds = image.get_bounding_rect()
    if bounds.width == 0 or bounds.height == 0:
        return image
    return image.subsurface(bounds).copy()


def _fit(image: pygame.Surface) -> pygame.Surface:
    """Blow the drawing up to fighting size, in whichever way suits how it was drawn.

    The two styles need opposite treatment, and the source height tells them
    apart: a tiny drawing was drawn pixel by pixel, a big one was drawn freehand.
    Using the wrong one is very visible — smoothscale turns pixel art to mush,
    and nearest-neighbour turns a soft-edged drawing to jaggies.
    """
    height = image.get_height()
    if height == 0:
        return image
    if height <= PIXEL_ART_MAX_HEIGHT:
        # Pixel art: a whole-number blow-up with nearest-neighbour sampling, so
        # every pixel stays square, sharp, and the same size as its neighbours'.
        size = (max(1, image.get_width() * PIXEL_SCALE), max(1, height * PIXEL_SCALE))
        return pygame.transform.scale(image, size)
    # A freehand drawing: fit it to a fighter's height and keep its soft edges.
    factor = TARGET_HEIGHT / height
    size = (max(1, round(image.get_width() * factor)), max(1, round(height * factor)))
    return pygame.transform.smoothscale(image, size)


def _draw_placeholder(side: str) -> pygame.Surface:
    """A simple squirrel built from ellipses and circles, facing right."""
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    body = PLACEHOLDER_COLORS.get(side, (150, 150, 150))
    dark = tuple(max(0, channel - 38) for channel in body)

    pygame.draw.ellipse(surface, dark, (6, 28, 84, 146))          # bushy tail
    pygame.draw.ellipse(surface, body, (66, 78, 96, 104))         # body
    pygame.draw.polygon(surface, dark, [(124, 46), (134, 10), (152, 44)])   # near ear
    pygame.draw.polygon(surface, dark, [(158, 44), (174, 12), (182, 48)])   # far ear
    pygame.draw.circle(surface, body, (152, 74), 40)              # head
    pygame.draw.circle(surface, (24, 24, 24), (166, 66), 6)       # eye
    pygame.draw.circle(surface, (24, 24, 24), (188, 74), 5)       # nose
    return surface
