import arena
from moves import Move


def test_gap_is_the_distance_between_them():
    assert arena.gap(250, 0, 710, 0) == 460
    assert arena.gap(710, 0, 250, 0) == 460


def test_the_three_bands_split_at_their_thresholds():
    assert arena.band(200, 0, 200 + arena.CLOSE_RANGE, 0) == arena.CLOSE
    assert arena.band(200, 0, 200 + arena.CLOSE_RANGE + 1, 0) == arena.MID
    assert arena.band(200, 0, 200 + arena.LONG_RANGE, 0) == arena.MID
    assert arena.band(200, 0, 200 + arena.LONG_RANGE + 1, 0) == arena.FAR


def test_fighters_start_in_the_ranged_band():
    assert arena.band(arena.PLAYER_START, 0, arena.RIVAL_START, 0) == arena.MID


def test_melee_reaches_only_when_close():
    move = Move("Tail Smack", "attack", "", dmg_range=(1, 1), reach="melee")
    assert arena.reaches(move, 400, 0, 500, 0) is True
    assert arena.reaches(move, 140, 0, 820, 0) is False


def test_ranged_reaches_only_in_the_middle_band():
    move = Move("Acorn Blast", "attack", "", dmg_range=(1, 1), reach="ranged")
    assert arena.reaches(move, 400, 0, 400 + arena.LONG_RANGE, 0) is True
    assert arena.reaches(move, 400, 0, 500, 0) is False              # too close
    assert arena.reaches(move, 400, 0, 400 + arena.LONG_RANGE + 1, 0) is False   # drops short


def test_any_reach_works_everywhere():
    move = Move("Scurry", "defense", "", block_reduction=0.5)
    assert arena.reaches(move, 400, 0, 500, 0) is True
    assert arena.reaches(move, 140, 0, 820, 0) is True


def test_player_stops_at_the_world_edge():
    # Rival close enough to the left edge that the leash isn't the binding limit.
    assert arena.clamp_walk(-500, 0, 600, 0) == arena.WALK_LEFT


def test_player_is_held_back_by_the_leash():
    assert arena.clamp_walk(-500, 0, 1670, 0) == 1670 - arena.LEASH


def test_walking_squirrels_keep_min_gap_apart():
    # Side-agnostic now: it only insists on separation, not on who is left.
    assert arena.clamp_walk(750, 0, 700, 0) == 700 + arena.MIN_GAP
    assert arena.clamp_walk(650, 0, 700, 0) == 700 - arena.MIN_GAP


def test_rival_stops_at_the_world_edge():
    assert arena.clamp_walk(9999, 0, arena.WALK_RIGHT - arena.MIN_GAP, 0) == arena.WALK_RIGHT


def test_rival_is_held_back_by_the_leash():
    assert arena.clamp_walk(9999, 0, 1210, 0) == 1210 + arena.LEASH


def test_a_squirrel_already_clear_is_left_where_it_is():
    # 260 apart is more than MIN_GAP, so nothing pushes it.
    assert arena.clamp_walk(660, 0, 400, 0) == 660


def test_squirrels_cannot_walk_through_each_other_on_the_ground():
    """They pass when one is up a tree, but never while both are walking.

    Checked by stepping rather than teleporting, because walking is what the
    game actually does — a single huge jump would clear the gap in one go.
    """
    x = arena.RIVAL_START - 400
    for _ in range(600):
        x = arena.walk(x, 0, 1, 16, arena.RIVAL_START, 0)
    assert x < arena.RIVAL_START
    assert arena.RIVAL_START - x >= arena.MIN_GAP


def test_walking_right_moves_at_the_given_speed():
    # Player at 1200 with the rival at RIVAL_START has room either way inside the leash.
    moved = arena.walk(1200, 0, 1, 1000, arena.RIVAL_START, 0, speed=220.0)
    assert moved == 1200 + 220.0


def test_walking_left_moves_the_other_way():
    moved = arena.walk(1200, 0, -1, 1000, arena.RIVAL_START, 0, speed=220.0)
    assert moved == 1200 - 220.0


def test_walking_is_clamped_like_everything_else():
    # Hard left with the rival near the left edge: the world edge stops us.
    moved = arena.walk(arena.WALK_LEFT + 10, 0, -1, 1000, 600, 0, speed=220.0)
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
    # Two draws now, not one: the vertical whim expires at the same moment.
    rng = FakeRandom(choices=[1, 0], ints=[800, 500])
    x, _, wander = arena.step_wander(
        arena.Wander(direction=-1, remaining_ms=0, climb_remaining_ms=0),
        arena.RIVAL_START, 0.0, arena.PLAYER_START, 0.0, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 800
    assert x > arena.RIVAL_START


def test_wander_keeps_going_while_its_stretch_lasts():
    rng = FakeRandom(choices=[], ints=[])
    x, _, wander = arena.step_wander(
        arena.Wander(direction=1, remaining_ms=500, climb_remaining_ms=500),
        arena.RIVAL_START, 0.0, arena.PLAYER_START, 0.0, 100, rng=rng)
    assert wander.direction == 1
    assert wander.remaining_ms == 400
    assert x > arena.RIVAL_START


def test_wander_turns_around_at_the_world_edge():
    rng = FakeRandom(choices=[], ints=[])
    # The player has to be pressed against the right edge for the rival to reach it.
    _, _, wander = arena.step_wander(
        arena.Wander(direction=1, remaining_ms=500, climb_remaining_ms=500),
        arena.WALK_RIGHT, 0.0, arena.WALK_RIGHT - arena.MIN_GAP, 0.0, 100, rng=rng)
    assert wander.direction == -1


def test_wander_turns_around_at_the_leash():
    rng = FakeRandom(choices=[], ints=[])
    at_leash = arena.PLAYER_START + arena.LEASH
    _, _, wander = arena.step_wander(
        arena.Wander(direction=1, remaining_ms=500, climb_remaining_ms=500),
        at_leash, 0.0, arena.PLAYER_START, 0.0, 100, rng=rng)
    assert wander.direction == -1


def test_wander_stays_inside_the_band_and_the_leash_over_many_steps():
    import random as real_random
    real_random.seed(1)
    wander = arena.Wander()
    x, y = arena.RIVAL_START, 0.0
    for _ in range(2000):
        x, y, wander = arena.step_wander(wander, x, y, arena.PLAYER_START, 0.0, 16)
        assert arena.WALK_LEFT <= x <= arena.WALK_RIGHT
        assert arena.PLAYER_START + arena.MIN_GAP <= x <= arena.PLAYER_START + arena.LEASH


def test_the_player_cannot_outrun_the_leash():
    """Walking hard away from a stationary rival stops at the leash, not the edge."""
    player_x = arena.PLAYER_START
    for _ in range(600):
        player_x = arena.walk(player_x, 0, -1, 16, arena.RIVAL_START, 0)
    assert arena.gap(player_x, 0, arena.RIVAL_START, 0) == arena.LEASH


def test_neither_squirrel_can_be_pushed_out_of_the_world():
    assert arena.clamp_walk(9999, 0, arena.WALK_RIGHT, 0) <= arena.WALK_RIGHT - arena.MIN_GAP
    assert arena.clamp_walk(-9999, 0, arena.WALK_LEFT, 0) >= arena.WALK_LEFT + arena.MIN_GAP


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


def test_gap_is_straight_line_distance():
    assert arena.gap(0, 0, 300, 400) == 500.0          # 3-4-5
    assert arena.gap(300, 400, 0, 0) == 500.0


def test_pure_height_counts_as_distance():
    assert arena.gap(1000, 0, 1000, 240) == 240.0


def test_height_can_push_you_out_of_melee_range():
    # Directly above, far enough up, is still close — but add a little walking
    # and it tips into the ranged band.
    assert arena.band(1000, 0, 1000, arena.CLOSE_RANGE) == arena.CLOSE
    assert arena.band(1000, 0, 1000 + 200, 240) == arena.MID


def test_trees_stand_inside_the_walkable_world():
    for trunk in arena.TREES:
        assert arena.WALK_LEFT <= trunk <= arena.WALK_RIGHT


def test_a_tree_is_on_screen_from_the_first_turn():
    assert any(arena.PLAYER_START <= trunk <= arena.RIVAL_START for trunk in arena.TREES)


def test_tree_near_finds_a_trunk_within_reach():
    trunk = arena.TREES[0]
    assert arena.tree_near(trunk) == trunk
    assert arena.tree_near(trunk + arena.CLIMB_REACH) == trunk
    assert arena.tree_near(trunk + arena.CLIMB_REACH + 1) is None


def test_climbing_up_and_down():
    assert arena.climb(0, 1, 1000, speed=160.0) == 160.0
    assert arena.climb(200, -1, 1000, speed=160.0) == 40.0


def test_climbing_stops_at_the_ground_and_the_ceiling():
    assert arena.climb(10, -1, 1000, speed=160.0) == 0.0
    assert arena.climb(arena.MAX_CLIMB - 10, 1, 1000, speed=160.0) == arena.MAX_CLIMB


def test_a_fully_climbed_squirrel_still_fits_on_the_stage():
    """MAX_CLIMB is forced by the stage ceiling, not chosen. Guard it.

    If squirrel art ever gets taller this fails, which is the point — otherwise
    the tallest squirrel's ears quietly leave the top of the stage.
    """
    import visual_game

    tallest_sprite = 184          # Big Bumboy, the tallest drawing in assets/
    feet = visual_game.GROUND_Y + 10 - arena.MAX_CLIMB
    assert feet - tallest_sprite >= visual_game.STAGE_TOP


def test_squirrels_bump_when_at_the_same_height():
    # Trying to stand exactly on someone stops MIN_GAP short, on the side you
    # came from — ties go left, since the push uses `x <= other_x`.
    assert arena.clamp_walk(1000, 0, 1000, 0) == 1000 - arena.MIN_GAP
    assert arena.clamp_walk(1100, 0, 1000, 0) == 1000 + arena.MIN_GAP


def test_squirrels_pass_freely_when_one_is_up_a_tree():
    # Same x, but 240 apart vertically: no horizontal constraint at all.
    assert arena.clamp_walk(1000, 0, 1000, arena.MAX_CLIMB) == 1000


def test_you_can_walk_out_the_far_side_of_an_occupied_tree():
    trunk = arena.TREES[2]
    x = trunk - 200
    for _ in range(400):
        x = arena.walk(x, 0, 1, 16, trunk, arena.MAX_CLIMB)
    assert x > trunk, "should have passed under the tree and out the other side"


def test_clamp_walk_still_honours_the_world_and_the_leash():
    assert arena.clamp_walk(-9999, 0, 600, arena.MAX_CLIMB) == arena.WALK_LEFT
    assert arena.clamp_walk(9999, 0, 1000, arena.MAX_CLIMB) == 1000 + arena.LEASH


def test_a_shove_lands_exactly_min_gap_away():
    assert arena.shove(1000, 1050) == 1050 - arena.MIN_GAP
    assert arena.shove(1100, 1050) == 1050 + arena.MIN_GAP


def test_a_shove_against_the_world_edge_goes_the_other_way():
    # Nowhere to go on the left, so the shoved squirrel goes right instead.
    shoved = arena.shove(arena.WALK_LEFT, arena.WALK_LEFT + 10)
    assert arena.WALK_LEFT <= shoved <= arena.WALK_RIGHT
    assert shoved == arena.WALK_LEFT + 10 + arena.MIN_GAP


def test_landing_on_a_grounded_squirrel_shoves_it():
    # Rival descends onto the player, who is standing on the ground below.
    px, py, rx, ry = arena.resolve_overlap(1000, 0, 1000, 10)
    assert py == 0 and ry == 10           # heights untouched
    assert abs(px - rx) == arena.MIN_GAP  # the player got moved aside


def test_landing_on_a_climbing_squirrel_is_blocked_instead():
    # Both up the same trunk: nobody gets shoved off it, the higher one stops.
    px, py, rx, ry = arena.resolve_overlap(1000, 100, 1000, 110)
    assert px == 1000 and rx == 1000      # nobody moved sideways
    assert ry == 100 + arena.CLIMB_CLEARANCE


def test_no_overlap_means_nothing_changes():
    before = (1000, 0, 1400, 0)
    assert arena.resolve_overlap(*before) == before


def test_the_rival_climbs_when_it_is_at_a_tree():
    rng = FakeRandom(choices=[1, 1], ints=[800, 800])
    trunk = arena.TREES[2]
    _, y, _ = arena.step_wander(arena.Wander(remaining_ms=0, climb_remaining_ms=0),
                                trunk, 0.0, trunk - 400, 0.0, 100, rng=rng)
    assert y > 0


def test_the_rival_cannot_climb_in_open_ground():
    rng = FakeRandom(choices=[1, 1], ints=[800, 800])
    # Exactly half a spacing past a trunk is the furthest you can be from one.
    nowhere = arena.TREES[2] + arena.TREE_SPACING // 2
    _, y, _ = arena.step_wander(arena.Wander(remaining_ms=0, climb_remaining_ms=0),
                                nowhere, 0.0, nowhere - 400, 0.0, 100, rng=rng)
    assert y == 0


def test_the_rival_stays_put_horizontally_while_off_the_ground():
    rng = FakeRandom(choices=[], ints=[])
    trunk = arena.TREES[2]
    x, y, _ = arena.step_wander(
        arena.Wander(direction=1, remaining_ms=500,
                     climb_direction=0, climb_remaining_ms=500),
        trunk, 100.0, trunk - 400, 0.0, 100, rng=rng)
    assert x == trunk, "a squirrel up a trunk should not drift sideways"
    assert y == 100.0


def test_the_rival_wander_stays_inside_every_limit():
    import random as real_random
    real_random.seed(3)
    wander = arena.Wander()
    x, y = arena.RIVAL_START, 0.0
    for _ in range(4000):
        x, y, wander = arena.step_wander(wander, x, y, arena.PLAYER_START, 0.0, 16)
        assert arena.WALK_LEFT <= x <= arena.WALK_RIGHT
        assert 0 <= y <= arena.MAX_CLIMB
        assert abs(x - arena.PLAYER_START) <= arena.LEASH


def test_trees_are_spaced_for_jumping():
    gaps = {arena.TREES[i + 1] - arena.TREES[i] for i in range(len(arena.TREES) - 1)}
    assert gaps == {arena.TREE_SPACING}


def test_both_fighters_start_at_a_trunk():
    """The spacing divides the 460px opening gap, so neither side starts favoured.

    At a spacing that doesn't divide it, one fighter begins able to climb and the
    other doesn't — a small unfairness baked into every battle.
    """
    assert arena.tree_near(arena.PLAYER_START) is not None
    assert arena.tree_near(arena.RIVAL_START) is not None


def out_of_the_way(x):
    """Somewhere the other squirrel can sit without affecting this one.

    NOT a huge x: `clamp_walk` applies the leash, so a far-off "other" would drag
    the jumper across the world to stay within 700px of it. Same x and a height
    nothing can reach is what actually means "ignore the other squirrel".
    """
    return x, 99999.0


def fly_until_settled(x, y, direction, limit=400):
    """Run a jump to its end. Returns (x, y, flight, steps)."""
    other_x, other_y = out_of_the_way(x)
    flight = arena.launch()
    steps = 0
    while flight.airborne and steps < limit:
        x, y, flight = arena.step_flight(flight, x, y, direction, 16, other_x, other_y)
        steps += 1
    assert steps < limit, "a jump should always end"
    return x, y, flight, steps


def test_launching_leaves_the_ground():
    flight = arena.launch()
    assert flight.airborne is True
    assert flight.vy > 0


def test_a_jump_comes_back_down_and_lands_flat():
    # Straight up from between two trunks, so nothing is caught on the way down.
    between = arena.TREES[4] + arena.TREE_SPACING // 2
    _, y, flight, _ = fly_until_settled(float(between), 0.0, 0)
    assert y == 0.0
    assert flight.airborne is False
    assert flight.vy == 0.0


def test_a_ground_jump_does_not_reach_the_next_tree():
    """The design rule, guarded, in terms of what actually happens.

    Asserted as "lands in the dirt" rather than a raw distance, because the catch
    radius adds itself to a jump's effective reach — measuring distance alone
    once hid a ground jump that was grabbing the next trunk anyway.
    """
    start = arena.TREES[4]
    x, y, flight, _ = fly_until_settled(float(start), 0.0, 1)
    assert y == 0.0, "should have landed on the ground, not caught a trunk"
    assert not flight.airborne
    assert x < start + arena.TREE_SPACING


def test_a_jump_from_up_a_tree_catches_the_next_one():
    start = arena.TREES[4]
    x, y, flight, _ = fly_until_settled(float(start), float(arena.MAX_CLIMB), 1)
    assert y > 0, "should have caught the next trunk, not landed"
    assert not flight.airborne
    assert arena.tree_near(x, arena.CATCH_REACH) == start + arena.TREE_SPACING


def test_a_descending_squirrel_catches_a_trunk():
    trunk = arena.TREES[4]
    flight = arena.Flight(airborne=True, vy=-100.0)      # falling
    _, y, after = arena.step_flight(flight, trunk, 120.0, 0, 16, *out_of_the_way(trunk))
    assert after.airborne is False, "should have grabbed the trunk"
    assert y > 0, "and stayed up it"


def test_an_ascending_squirrel_does_not_catch_the_trunk_it_left():
    trunk = arena.TREES[4]
    flight = arena.Flight(airborne=True, vy=300.0)       # still rising
    _, _, after = arena.step_flight(flight, trunk, 120.0, 0, 16, *out_of_the_way(trunk))
    assert after.airborne is True, "would never be able to leave a tree otherwise"


def test_steering_in_the_air_still_respects_the_world():
    flight = arena.Flight(airborne=True, vy=0.0)
    x, _, _ = arena.step_flight(
        flight, arena.WALK_LEFT, 100.0, -1, 16, *out_of_the_way(arena.WALK_LEFT))
    assert x >= arena.WALK_LEFT


def test_the_rival_always_ends_up_somewhere_solid():
    """Over a long wander it may jump, but it must never be left airborne forever."""
    import random as real_random
    real_random.seed(7)
    wander = arena.Wander()
    flight = arena.Flight()
    x, y = arena.RIVAL_START, 0.0
    airborne_run = 0
    for _ in range(6000):
        x, y, wander, flight = arena.step_rival(
            wander, flight, x, y, arena.PLAYER_START, 0.0, 16)
        assert arena.WALK_LEFT <= x <= arena.WALK_RIGHT
        assert 0 <= y <= arena.MAX_CLIMB + 200      # a jump arcs above MAX_CLIMB
        airborne_run = airborne_run + 1 if flight.airborne else 0
        assert airborne_run < 200, "never came back down"


def test_the_rival_only_jumps_from_somewhere_it_could():
    rng = FakeRandom(choices=[1, 0, 1], ints=[800, 500, 500])
    # Mid-air already: it must not start another jump.
    _, _, _, flight = arena.step_rival(
        arena.Wander(remaining_ms=0, climb_remaining_ms=0, jump_remaining_ms=0),
        arena.Flight(airborne=True, vy=100.0),
        arena.TREES[4], 100.0, arena.PLAYER_START, 0.0, 16, rng=rng)
    assert flight.vy < 100.0, "should have kept falling, not relaunched"
