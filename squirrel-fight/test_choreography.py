import pytest

from choreography import PLAYER, RIVAL, ActorState, Cue, Timeline, _effect_state, sample


def test_empty_timeline_samples_neutral():
    timeline = Timeline(hp_start={PLAYER: 60, RIVAL: 60}, total_ms=0)
    frame = sample(timeline, 0)
    assert frame.actors[PLAYER] == ActorState()
    assert frame.actors[RIVAL] == ActorState()
    assert frame.hp == {PLAYER: 60, RIVAL: 60}
    assert frame.caption == ""


@pytest.mark.parametrize("effect", ["lunge", "stagger", "hop", "brace", "glow", "faint"])
def test_effects_start_neutral(effect):
    assert _effect_state(effect, 0.0, 0, 1) == ActorState()


def test_lunge_moves_player_right_and_rival_left():
    forward = _effect_state("lunge", 0.5, 350, 1)
    backward = _effect_state("lunge", 0.5, 350, -1)
    assert forward.offset_x > 0
    assert backward.offset_x == -forward.offset_x


def test_lunge_returns_home_at_the_end():
    assert _effect_state("lunge", 1.0, 700, 1).offset_x == pytest.approx(0.0, abs=1e-9)


def test_flash_is_brightest_immediately_and_fades_out():
    assert _effect_state("flash", 0.0, 0, 1).tint == 1.0
    assert _effect_state("flash", 1.0, 220, 1).tint == 0.0


def test_hop_lifts_the_dodger_off_the_ground():
    assert _effect_state("hop", 0.5, 160, 1).offset_y < 0


def test_brace_crouches_without_leaving_the_ground():
    braced = _effect_state("brace", 0.5, 200, 1)
    assert braced.scale < 1.0
    assert braced.offset_y == 0.0


def test_faint_topples_and_fades():
    down = _effect_state("faint", 1.0, 500, 1)
    assert abs(down.rotation) == 90.0
    assert down.alpha < 1.0


def test_faint_holds_its_final_pose_long_after_the_cue_started():
    # The faint cue is stretched to the end of the timeline so the squirrel stays
    # down, but the topple itself must still finish quickly.
    late = _effect_state("faint", 0.2, 4000, 1)
    assert abs(late.rotation) == 90.0


def test_two_cues_on_one_squirrel_stack():
    timeline = Timeline(
        cues=[Cue(0, 200, RIVAL, "stagger"), Cue(0, 200, RIVAL, "flash")],
        hp_start={PLAYER: 60, RIVAL: 60},
        total_ms=200,
    )
    frame = sample(timeline, 100)
    assert frame.actors[RIVAL].tint > 0
    assert frame.actors[RIVAL].offset_x != 0


def test_glow_brightens_and_lifts_the_healer():
    lit = _effect_state("glow", 0.5, 210, 1)
    assert lit.glow > 0
    assert lit.offset_y < 0


@pytest.mark.parametrize("effect", ["lunge", "stagger", "hop", "brace", "faint"])
def test_effects_mirror_for_the_rival(effect):
    player = _effect_state(effect, 0.5, 250, 1)
    rival = _effect_state(effect, 0.5, 250, -1)
    # Guard against the assertions below passing vacuously on an all-zero state.
    assert (player.offset_x, player.rotation) != (0.0, 0.0)
    assert rival.offset_x == -player.offset_x
    assert rival.rotation == -player.rotation


# Which way each effect should carry the player squirrel, which faces right (+1).
# Screen coordinates: negative offset_y is up. Sampled at a progress where the
# movement is unambiguous -- stagger wobbles, so it is checked early in its
# window while the knock-back still dominates.
DIRECTIONS = [
    # effect,   progress, elapsed_ms, attribute,   expected sign
    ("lunge",   0.5, 350, "offset_x", +1),   # drives forward at the rival
    ("stagger", 0.1,  34, "offset_x", -1),   # reels backwards from the hit
    ("hop",     0.5, 160, "offset_x", -1),   # skips back out of the way
    ("hop",     0.5, 160, "offset_y", -1),   # ...and up off the ground
    ("brace",   0.5, 200, "offset_x", -1),   # digs in and gives ground
    ("faint",   0.5, 250, "rotation", +1),   # topples over forwards
    ("faint",   0.5, 250, "offset_y", +1),   # and sinks toward the floor
    ("glow",    0.5, 210, "offset_y", -1),   # floats up while healing
]


@pytest.mark.parametrize("effect,progress,elapsed_ms,attribute,sign", DIRECTIONS)
def test_effects_move_the_player_the_right_way(effect, progress, elapsed_ms, attribute, sign):
    value = getattr(_effect_state(effect, progress, elapsed_ms, 1), attribute)
    assert value * sign > 0
