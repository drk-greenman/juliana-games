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


def test_a_jumping_squirrel_still_fits_on_the_stage():
    """The ceiling constrains the jump APEX, not the climb height.

    Guarded because this broke once: MAX_CLIMB was set so a *climbing* squirrel
    fitted, then jumping arrived and rose another 76px, clipping heads off the
    top of the stage. Fails if art gets taller or the jump gets stronger.
    """
    import visual_game

    tallest_sprite = 184          # Big Bumboy, the tallest drawing in assets/
    apex = arena.MAX_CLIMB + arena.JUMP_SPEED ** 2 / (2 * arena.GRAVITY)
    feet = visual_game.GROUND_Y + 10 - apex
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
    # The middle of a clearing — now the furthest from a trunk you can stand.
    nowhere = arena.TREES[1] + arena.CLEARING // 2
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


def copse_gaps():
    """Every gap between neighbouring trunks, in order."""
    return [arena.TREES[i + 1] - arena.TREES[i] for i in range(len(arena.TREES) - 1)]


def test_trunks_in_a_copse_are_spaced_for_jumping():
    """Inside a copse the spacing is unchanged, so treetop chaining still works."""
    assert arena.TREE_SPACING in copse_gaps()
    assert set(copse_gaps()) == {arena.TREE_SPACING, arena.CLEARING}


def test_a_clearing_is_wider_than_any_jump(monkeypatch):
    """Not a round number: it has to beat the furthest a jump can possibly go.

    That is the ballistic reach from MAX_CLIMB plus CATCH_REACH, because a catch
    radius adds itself to every jump's effective reach — the thing that broke the
    tree-to-tree rule the first time these numbers were picked. With no trunks to
    catch, the arc runs its full length.

    Launched from WALK_LEFT rather than 0: `clamp_walk` pins x to the walkable
    band, so a jump measured from outside it reads far longer than it is.
    """
    monkeypatch.setattr(arena, "TREES", ())
    start = float(arena.WALK_LEFT)
    x, y, flight = start, float(arena.MAX_CLIMB), arena.launch()
    while flight.airborne:
        x, y, flight = arena.step_flight(flight, x, y, 1, 16, start, 99999.0)
    assert arena.CLEARING > (x - start) + arena.CATCH_REACH


def test_both_fighters_start_at_a_trunk():
    """The spacing divides the 460px opening gap, so neither side starts favoured.

    At a spacing that doesn't divide it, one fighter begins able to climb and the
    other doesn't — a small unfairness baked into every battle.
    """
    assert arena.tree_near(arena.PLAYER_START) is not None
    assert arena.tree_near(arena.RIVAL_START) is not None


def trunk_on_a_copse_edge():
    """A trunk whose right-hand neighbour is a clearing away, not a jump away.

    The last trunk in the world is excluded: it has nothing to its right because
    the world ends, which is not the same thing as a copse edge.
    """
    for trunk in arena.TREES[:-1]:
        if trunk + arena.TREE_SPACING not in arena.TREES:
            return trunk
    raise AssertionError("no copse edges — the trees are a uniform grid")


def test_you_cannot_leap_out_of_a_copse():
    """The point of the whole layout, stated as what happens.

    Leaping from trunk to trunk works inside a copse and runs out at its edge:
    crossing a clearing means coming down and walking. Asserted as "lands in the
    dirt" rather than as a distance, for the same reason as the ground-jump test.
    """
    _, y, flight, _ = fly_until_settled(
        float(trunk_on_a_copse_edge()), float(arena.MAX_CLIMB), 1)
    assert y == 0.0, "a jump across a clearing should land in the dirt"
    assert not flight.airborne


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


def trunk_with_a_neighbour_to_the_right():
    """A trunk that has another trunk exactly TREE_SPACING to its right.

    The jump-reach tests need "a trunk and the next one along". An index into
    TREES only supplies that by accident: with trunks in copses, TREES[4] is a
    copse edge, and the nearest trunk to its right is a whole clearing away.
    Asking for the condition directly keeps these tests about jumping rather
    than about where the trees happen to be this week.
    """
    for trunk in arena.TREES:
        if trunk + arena.TREE_SPACING in arena.TREES:
            return trunk
    raise AssertionError("no two trunks are a jump apart — check TREE_SPACING")


def test_launching_leaves_the_ground():
    flight = arena.launch()
    assert flight.airborne is True
    assert flight.vy > 0


def test_a_jump_comes_back_down_and_lands_flat():
    # Straight up from between two trunks, so nothing is caught on the way down.
    between = trunk_with_a_neighbour_to_the_right() + arena.TREE_SPACING // 2
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
    start = trunk_with_a_neighbour_to_the_right()
    x, y, flight, _ = fly_until_settled(float(start), 0.0, 1)
    assert y == 0.0, "should have landed on the ground, not caught a trunk"
    assert not flight.airborne
    assert x < start + arena.TREE_SPACING


def test_a_jump_from_up_a_tree_catches_the_next_one():
    start = trunk_with_a_neighbour_to_the_right()
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


def test_the_rival_does_not_live_up_a_tree():
    """The vertical whim has to pull toward the ground, not merely wobble.

    A whim drawn from a zero-mean set makes the rival's height an aimless walk
    between two walls, and such a walk sits at every height equally — so the
    rival ends up clinging to a trunk most of the fight instead of wandering.
    It cannot walk while it is off the ground, so this stops the whole fight
    moving. Measured at 71% of the fight off the ground, with single stints of
    half a minute, before the whim was weighted downwards.

    Stranding itself up a tree is meant to be the joke, not the default state.

    What is measured here is the *stint* and how far it travels, not the share
    of time spent off the ground. Once jumping existed, that share stopped being
    a proxy for stuck: a rival climbing, perching, leaping and coming down is
    off the ground half the time while never standing still. Guarding the share
    instead is what pushed the rival to the opposite failure — see
    `test_the_rival_really_climbs_when_it_climbs`.
    """
    import random as real_random

    total = 0
    travelled = 0.0
    longest_stint_ms = 0
    for seed in range(4):
        real_random.seed(seed)
        wander, flight = arena.Wander(), arena.Flight()
        x, y = float(arena.RIVAL_START), 0.0
        stint_ms = 0
        for _ in range(60 * 60):            # a minute of play at 60fps
            previous_x = x
            x, y, wander, flight = arena.step_rival(
                wander, flight, x, y, arena.PLAYER_START, 0.0, 16)
            travelled += abs(x - previous_x)
            total += 1
            if y > 0:
                stint_ms += 16
                longest_stint_ms = max(longest_stint_ms, stint_ms)
            else:
                stint_ms = 0

    assert longest_stint_ms < 12000, (
        "rival spent {:.1f}s up a tree in one go".format(longest_stint_ms / 1000))
    assert travelled / (total / 3600) > 2500, (
        "rival covered only {:.0f}px a minute".format(travelled / (total / 3600)))


def test_chained_jumps_cannot_ratchet_a_squirrel_off_the_top():
    """Catching a trunk must never leave you gripping above `MAX_CLIMB`.

    Reported from play: "I climbed a tree and jumped at the top and flew off
    the map." A catch returned whatever height it happened at, so each jump in
    a chain launched about 73px higher than the last and the squirrel ratcheted
    out of the world — peaking at 3531px against a stage budget of 240.

    `MAX_CLIMB` is what makes the whole ceiling sum work: a launch from there
    apexes at exactly the stage ceiling, so a launch from any higher cannot fit.
    """
    ceiling = arena.MAX_CLIMB + arena.JUMP_SPEED ** 2 / (2 * arena.GRAVITY)
    x, y = float(arena.TREES[3]), float(arena.MAX_CLIMB)
    flight = arena.launch()
    peak = y
    for _ in range(2000):
        x, y, flight = arena.step_flight(
            flight, x, y, 1, 16, float(arena.TREES[0]), 0.0)
        peak = max(peak, y)
        if not flight.airborne and y > 0:
            assert y <= arena.MAX_CLIMB, (
                "caught a trunk at {:.0f}px, above MAX_CLIMB of {}".format(
                    y, arena.MAX_CLIMB))
            flight = arena.launch()          # as holding Space does

    assert peak <= ceiling + 1, (
        "reached {:.0f}px against a ceiling of {:.0f}".format(peak, ceiling))


def test_the_rival_really_climbs_when_it_climbs():
    """Going up a trunk has to be a commitment, not a twitch.

    Weighting the whim downwards stopped the rival living up a tree, but a
    walk pulled down hard never gets anywhere either — it bobs at the foot of
    a trunk, spending 2% of the fight above 120px, and the jump it could only
    launch from up there almost never fires. Reported from play as "the rival
    didn't jump very much or really climb at all".

    This test and `test_the_rival_does_not_live_up_a_tree` pull in opposite
    directions on purpose: together they rule out both failure modes, and a
    plain random walk cannot satisfy both.
    """
    import random as real_random

    high = total = jumps = 0
    peak = 0.0
    for seed in range(4):
        real_random.seed(seed)
        wander, flight = arena.Wander(), arena.Flight()
        x, y = float(arena.RIVAL_START), 0.0
        was_airborne = False
        for _ in range(60 * 120):           # two minutes of play
            x, y, wander, flight = arena.step_rival(
                wander, flight, x, y, arena.PLAYER_START, 0.0, 16)
            total += 1
            peak = max(peak, y)
            if y > 120:
                high += 1
            if flight.airborne and not was_airborne:
                jumps += 1
            was_airborne = flight.airborne

    assert peak > arena.MAX_CLIMB * 0.8, "never got near the top of a trunk"
    assert high / total > 0.05, (
        "spent only {:.1%} of the fight high up a trunk".format(high / total))
    assert jumps / (total / 3600) > 8, (
        "only jumped {:.1f} times a minute".format(jumps / (total / 3600)))
