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


class FakeRandom:
    """A stand-in for `random` that hands back whatever the test wants."""

    def __init__(self, choices, ints):
        self.choices = list(choices)
        self.ints = list(ints)

    def choice(self, options):
        return self.choices.pop(0)

    def randint(self, low, high):
        return self.ints.pop(0)


def test_wander_picks_a_direction_when_its_stretch_runs_out():
    rng = FakeRandom(choices=[1], ints=[800])
    x, wander = arena.step_wander(arena.Wander(direction=-1, remaining_ms=0),
                                  500, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 800
    assert x > 500


def test_wander_keeps_going_while_its_stretch_lasts():
    rng = FakeRandom(choices=[], ints=[])
    x, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  500, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 400
    assert x > 500


def test_wander_turns_around_at_the_right_wall():
    rng = FakeRandom(choices=[], ints=[])
    _, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  arena.WALK_RIGHT, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == -1


def test_wander_stays_inside_the_band_over_many_steps():
    import random as real_random
    real_random.seed(1)
    wander = arena.Wander()
    x = arena.RIVAL_START
    for _ in range(2000):
        x, wander = arena.step_wander(wander, x, arena.PLAYER_START, 16)
        assert arena.WALK_LEFT <= x <= arena.WALK_RIGHT
        assert x >= arena.PLAYER_START + arena.MIN_GAP
