"""Tests for the pure name-to-filename matching in sprites.py.

The drawing-loading itself is pygame I/O and has no tests, the same way
`game.py` has none. `slug()` is the exception: it is pure, and it is the join
between a rival's name in `game.py` and a file on disk. When it is wrong,
nothing raises — the squirrel just quietly falls back to a placeholder.
"""

import pytest

from sprites import slug


@pytest.mark.parametrize("name, expected", [
    ("JOHN CENA", "john-cena"),
    ("sherlock gnomes", "sherlock-gnomes"),
    ("BIG BUMBOY", "big-bumboy"),
    ("Bushy Malone godski", "bushy-malone-godski"),
])
def test_rival_names_become_their_file_stems(name, expected):
    assert slug(name) == expected


def test_case_does_not_matter():
    assert slug("Sherlock Gnomes") == slug("sherlock gnomes")


def test_punctuation_and_spacing_collapse():
    assert slug("Mr. tickle bum") == "mr-tickle-bum"
    assert slug("lord o  Grey   Menace") == "lord-o-grey-menace"


def test_slugging_a_slug_changes_nothing():
    # pick_player_art() hands an already-slugged stem back to load_pose(), so
    # this has to be a no-op or the player's borrowed drawing goes missing.
    assert slug("john-cena") == "john-cena"


def test_leading_and_trailing_junk_is_stripped():
    assert slug("  SIR NUTS ALOT!  ") == "sir-nuts-alot"


def test_a_tree_is_always_available_even_with_no_drawing():
    """Like the squirrels, trees work with no art and get better with it."""
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    import sprites

    pygame.init()
    pygame.display.set_mode((1, 1))
    sprites.clear_cache()
    tree = sprites.load_tree()
    assert tree.get_width() > 0
    assert tree.get_height() > 0


def test_only_squirrels_are_offered_as_fighters(tmp_path, monkeypatch):
    """Non-squirrel art must never be dealt as a fighter.

    `tree.png` really was offered before this test existed — a drawn tree would
    have turned up in a duel as the player's borrowed squirrel. When a new kind
    of asset is added, reserve it here and this test will say so.
    """
    import sprites

    for name in ("john-cena.png", "big-bumboy.png", "background.png",
                 "background-forest.png", "tree.png",
                 "player_idle.png", "john-cena_hurt.png"):
        (tmp_path / name).touch()
    monkeypatch.setattr(sprites, "ASSETS_DIR", tmp_path)

    assert sprites.available_squirrels() == {"john-cena", "big-bumboy"}


def test_available_backgrounds_finds_every_scene(tmp_path, monkeypatch):
    import sprites

    for name in ("background.png", "background-forest.png", "background-snow.png",
                 "john-cena.png", "tree.png"):
        (tmp_path / name).touch()
    monkeypatch.setattr(sprites, "ASSETS_DIR", tmp_path)

    assert sprites.available_backgrounds() == [
        "background", "background-forest", "background-snow"]


def test_available_backgrounds_copes_with_no_art(tmp_path, monkeypatch):
    import sprites

    monkeypatch.setattr(sprites, "ASSETS_DIR", tmp_path)
    assert sprites.available_backgrounds() == []


def test_a_missing_scene_loads_as_nothing(tmp_path, monkeypatch):
    import sprites

    monkeypatch.setattr(sprites, "ASSETS_DIR", tmp_path)
    sprites.clear_cache()
    assert sprites.load_background("background-nowhere") is None
