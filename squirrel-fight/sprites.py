from __future__ import annotations

from pathlib import Path

import pygame

ASSETS_DIR = Path(__file__).parent / "assets"
SPRITE_SIZE = (200, 200)
# Matches visual_game's stage band, the strip between the HP panel and the
# message strip. A drawn backdrop is stretched to exactly fill it.
STAGE_SIZE = (960, 240)

# Body colours for the code-drawn stand-in squirrels, so the two fighters are
# still tellable apart before any real art exists.
PLACEHOLDER_COLORS = {
    "player": (168, 106, 58),
    "rival": (116, 116, 132),
}

_cache: dict = {}
_background_cache: dict = {}


def load_pose(actor: str, pose: str) -> pygame.Surface:
    """Return the drawing for `actor` in `pose`, facing right.

    Falls back to the actor's `idle` drawing, and then to a code-drawn
    placeholder, so a missing or unreadable file is never fatal. Results are
    cached, so the placeholder is drawn once rather than every frame.
    """
    key = (actor, pose)
    if key not in _cache:
        surface = _load_file(actor, pose)
        if surface is None and pose != "idle":
            surface = _load_file(actor, "idle")
        if surface is None:
            surface = _draw_placeholder(actor)
        _cache[key] = surface
    return _cache[key]


def clear_cache() -> None:
    """Forget every loaded drawing. Only needed if assets change while running."""
    _cache.clear()
    _background_cache.clear()


def _load_file(actor: str, pose: str) -> pygame.Surface | None:
    path = ASSETS_DIR / "{}_{}.png".format(actor, pose)
    if not path.is_file():
        return None
    try:
        image = pygame.image.load(str(path)).convert_alpha()
    except (pygame.error, OSError):
        # Corrupt, unreadable, or vanished between the check and the load.
        # Treat it exactly like a missing file.
        return None
    return pygame.transform.smoothscale(image, SPRITE_SIZE)


def load_background() -> pygame.Surface | None:
    """Return `assets/background.png` scaled to the stage, or None if there isn't one.

    None means "no backdrop drawn yet", which the caller answers with its plain
    sky and grass — so this is the one loader with no placeholder of its own.
    """
    if "background" not in _background_cache:
        path = ASSETS_DIR / "background.png"
        surface = None
        if path.is_file():
            try:
                # convert(), not convert_alpha(): a backdrop fills the whole
                # stage, so it needs no transparency and blits faster opaque.
                surface = pygame.transform.smoothscale(
                    pygame.image.load(str(path)).convert(), STAGE_SIZE
                )
            except (pygame.error, OSError):
                surface = None
        _background_cache["background"] = surface
    return _background_cache["background"]


def _draw_placeholder(actor: str) -> pygame.Surface:
    """A simple squirrel built from ellipses and circles, facing right."""
    surface = pygame.Surface(SPRITE_SIZE, pygame.SRCALPHA)
    body = PLACEHOLDER_COLORS.get(actor, (150, 150, 150))
    dark = tuple(max(0, channel - 38) for channel in body)

    pygame.draw.ellipse(surface, dark, (6, 28, 84, 146))          # bushy tail
    pygame.draw.ellipse(surface, body, (66, 78, 96, 104))         # body
    pygame.draw.polygon(surface, dark, [(124, 46), (134, 10), (152, 44)])   # near ear
    pygame.draw.polygon(surface, dark, [(158, 44), (174, 12), (182, 48)])   # far ear
    pygame.draw.circle(surface, body, (152, 74), 40)              # head
    pygame.draw.circle(surface, (24, 24, 24), (166, 66), 6)       # eye
    pygame.draw.circle(surface, (24, 24, 24), (188, 74), 5)       # nose
    return surface
