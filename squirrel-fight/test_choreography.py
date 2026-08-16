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
