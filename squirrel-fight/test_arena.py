import arena
from moves import Move


def test_gap_is_the_distance_between_them():
    assert arena.gap(250, 710) == 460
    assert arena.gap(710, 250) == 460


def test_close_and_far_split_at_the_threshold():
    assert arena.is_close(200, 200 + arena.CLOSE_RANGE) is True
    assert arena.is_close(200, 200 + arena.CLOSE_RANGE + 1) is False


def test_fighters_start_far_apart():
    assert arena.is_close(arena.PLAYER_START, arena.RIVAL_START) is False


def test_melee_reaches_only_when_close():
    move = Move("Tail Smack", "attack", "", dmg_range=(1, 1), reach="melee")
    assert arena.reaches(move, 400, 500) is True
    assert arena.reaches(move, 140, 820) is False


def test_ranged_reaches_only_when_far():
    move = Move("Acorn Blast", "attack", "", dmg_range=(1, 1), reach="ranged")
    assert arena.reaches(move, 140, 820) is True
    assert arena.reaches(move, 400, 500) is False


def test_any_reach_works_everywhere():
    move = Move("Scurry", "defense", "", block_reduction=0.5)
    assert arena.reaches(move, 400, 500) is True
    assert arena.reaches(move, 140, 820) is True
