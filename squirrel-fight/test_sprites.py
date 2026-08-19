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
