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


def test_player_stops_at_the_left_edge():
    assert arena.clamp_player(-500, arena.RIVAL_START) == arena.WALK_LEFT


def test_player_stops_short_of_the_rival():
    assert arena.clamp_player(900, 700) == 700 - arena.MIN_GAP


def test_rival_stops_at_the_right_edge():
    assert arena.clamp_rival(9999, arena.PLAYER_START) == arena.WALK_RIGHT


def test_rival_stops_short_of_the_player():
    assert arena.clamp_rival(100, 400) == 400 + arena.MIN_GAP


def test_squirrels_never_swap_sides():
    player = arena.clamp_player(9999, arena.RIVAL_START)
    rival = arena.clamp_rival(-9999, player)
    assert player < rival


def test_walking_right_moves_at_the_given_speed():
    moved = arena.walk_player(300, 1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == 300 + 220.0


def test_walking_left_moves_the_other_way():
    moved = arena.walk_player(500, -1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == 500 - 220.0


def test_walking_is_clamped_like_everything_else():
    moved = arena.walk_player(arena.WALK_LEFT + 10, -1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == arena.WALK_LEFT
