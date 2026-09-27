import arena
from moves import Move


def test_gap_is_the_distance_between_them():
    assert arena.gap(250, 710) == 460
    assert arena.gap(710, 250) == 460


def test_the_three_bands_split_at_their_thresholds():
    assert arena.band(200, 200 + arena.CLOSE_RANGE) == arena.CLOSE
    assert arena.band(200, 200 + arena.CLOSE_RANGE + 1) == arena.MID
    assert arena.band(200, 200 + arena.LONG_RANGE) == arena.MID
    assert arena.band(200, 200 + arena.LONG_RANGE + 1) == arena.FAR


def test_fighters_start_in_the_ranged_band():
    assert arena.band(arena.PLAYER_START, arena.RIVAL_START) == arena.MID


def test_melee_reaches_only_when_close():
    move = Move("Tail Smack", "attack", "", dmg_range=(1, 1), reach="melee")
    assert arena.reaches(move, 400, 500) is True
    assert arena.reaches(move, 140, 820) is False


def test_ranged_reaches_only_in_the_middle_band():
    move = Move("Acorn Blast", "attack", "", dmg_range=(1, 1), reach="ranged")
    assert arena.reaches(move, 400, 400 + arena.LONG_RANGE) is True
    assert arena.reaches(move, 400, 500) is False              # too close
    assert arena.reaches(move, 400, 400 + arena.LONG_RANGE + 1) is False   # drops short


def test_any_reach_works_everywhere():
    move = Move("Scurry", "defense", "", block_reduction=0.5)
    assert arena.reaches(move, 400, 500) is True
    assert arena.reaches(move, 140, 820) is True


def test_player_stops_at_the_world_edge():
    # Rival close enough to the left edge that the leash isn't the binding limit.
    assert arena.clamp_player(-500, 600) == arena.WALK_LEFT


def test_player_is_held_back_by_the_leash():
    assert arena.clamp_player(-500, 1670) == 1670 - arena.LEASH


def test_player_stops_short_of_the_rival():
    assert arena.clamp_player(900, 700) == 700 - arena.MIN_GAP


def test_rival_stops_at_the_world_edge():
    assert arena.clamp_rival(9999, arena.WALK_RIGHT - arena.MIN_GAP) == arena.WALK_RIGHT


def test_rival_is_held_back_by_the_leash():
    assert arena.clamp_rival(9999, 1210) == 1210 + arena.LEASH


def test_rival_stops_short_of_the_player():
    assert arena.clamp_rival(100, 400) == 400 + arena.MIN_GAP


def test_squirrels_never_swap_sides():
    player = arena.clamp_player(9999, arena.RIVAL_START)
    rival = arena.clamp_rival(-9999, player)
    assert player < rival


def test_walking_right_moves_at_the_given_speed():
    # Player at 1200 with the rival at RIVAL_START has room either way inside the leash.
    moved = arena.walk_player(1200, 1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == 1200 + 220.0


def test_walking_left_moves_the_other_way():
    moved = arena.walk_player(1200, -1, 1000, arena.RIVAL_START, speed=220.0)
    assert moved == 1200 - 220.0


def test_walking_is_clamped_like_everything_else():
    # Hard left with the rival near the left edge: the world edge stops us.
    moved = arena.walk_player(arena.WALK_LEFT + 10, -1, 1000, 600, speed=220.0)
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
                                  arena.RIVAL_START, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 800
    assert x > arena.RIVAL_START


def test_wander_keeps_going_while_its_stretch_lasts():
    rng = FakeRandom(choices=[], ints=[])
    x, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  arena.RIVAL_START, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 400
    assert x > arena.RIVAL_START


def test_wander_turns_around_at_the_world_edge():
    rng = FakeRandom(choices=[], ints=[])
    # The player has to be pressed against the right edge for the rival to reach it.
    _, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  arena.WALK_RIGHT, arena.WALK_RIGHT - arena.MIN_GAP,
                                  100, rng=rng)
    assert wander.direction == -1


def test_wander_turns_around_at_the_leash():
    rng = FakeRandom(choices=[], ints=[])
    at_leash = arena.PLAYER_START + arena.LEASH
    _, wander = arena.step_wander(arena.Wander(direction=1, remaining_ms=500),
                                  at_leash, arena.PLAYER_START, 100, rng=rng)
    assert wander.direction == -1


def test_wander_stays_inside_the_band_and_the_leash_over_many_steps():
    import random as real_random
    real_random.seed(1)
    wander = arena.Wander()
    x = arena.RIVAL_START
    for _ in range(2000):
        x, wander = arena.step_wander(wander, x, arena.PLAYER_START, 16)
        assert arena.WALK_LEFT <= x <= arena.WALK_RIGHT
        assert arena.PLAYER_START + arena.MIN_GAP <= x <= arena.PLAYER_START + arena.LEASH


def test_the_player_cannot_outrun_the_leash():
    """Walking hard away from a stationary rival stops at the leash, not the edge."""
    player_x = arena.PLAYER_START
    for _ in range(600):
        player_x = arena.walk_player(player_x, -1, 16, arena.RIVAL_START)
    assert arena.gap(player_x, arena.RIVAL_START) == arena.LEASH


def test_neither_squirrel_can_be_pushed_out_of_the_world():
    assert arena.clamp_player(9999, arena.WALK_RIGHT) <= arena.WALK_RIGHT - arena.MIN_GAP
    assert arena.clamp_rival(-9999, arena.WALK_LEFT) >= arena.WALK_LEFT + arena.MIN_GAP


def test_camera_centres_between_the_two_squirrels():
    # Well inside the world, so no clamping interferes.
    assert arena.camera_x(1200, 1600) == 1400 - arena.WINDOW_WIDTH / 2


def test_camera_stops_at_the_left_of_the_world():
    assert arena.camera_x(arena.WALK_LEFT, arena.WALK_LEFT + arena.MIN_GAP) == 0


def test_camera_stops_at_the_right_of_the_world():
    assert arena.camera_x(arena.WALK_RIGHT - arena.MIN_GAP, arena.WALK_RIGHT) == (
        arena.WORLD_WIDTH - arena.WINDOW_WIDTH
    )


def test_opening_positions_look_exactly_like_the_old_one_screen_stage():
    """The game should open on the marks the squirrels always stood on."""
    camera = arena.camera_x(arena.PLAYER_START, arena.RIVAL_START)
    assert arena.PLAYER_START - camera == 250
    assert arena.RIVAL_START - camera == 710
