from __future__ import annotations

from pathlib import Path

import pygame

ASSETS_DIR = Path(__file__).parent / "assets"
SPRITE_SIZE = (200, 200)

# Body colours for the code-drawn stand-in squirrels, so the two fighters are
# still tellable apart before any real art exists.
PLACEHOLDER_COLORS = {
    "player": (168, 106, 58),
    "rival": (116, 116, 132),
}

_cache: dict = {}


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


def _load_file(actor: str, pose: str):
    path = ASSETS_DIR / "{}_{}.png".format(actor, pose)
    if not path.is_file():
        return None
    try:
        image = pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        # Corrupt or unreadable file. Treat it exactly like a missing one.
        return None
    return pygame.transform.smoothscale(image, SPRITE_SIZE)


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
