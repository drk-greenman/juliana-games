import pytest

from battle import FighterTurnOutcome, TurnResult
from choreography import (
    ACTION_MS, GAP_MS, PLAYER, RIVAL, ActorState, Cue, Timeline,
    _effect_state, build_timeline, sample,
)
from moves import Move


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


FULL_HP = {PLAYER: 60, RIVAL: 60}


def attack_move(name="Tail Smack", lifesteal=False):
    return Move(name=name, kind="attack", description="", dmg_range=(10, 13), lifesteal=lifesteal)


def dodge_move(name="Dance"):
    return Move(name=name, kind="defense", description="", dodge_chance=0.5)


def block_move(name="Flex"):
    return Move(name=name, kind="defense", description="", block_flat=36)


def heal_move(name="Eat Garden"):
    return Move(name=name, kind="heal", description="", heal_range=(12, 18))


def build(player_move, rival_move, result, hp_before=None, hp_after=None):
    hp_before = FULL_HP if hp_before is None else hp_before
    hp_after = hp_before if hp_after is None else hp_after
    return build_timeline(
        "Juliana", "JOHN CENA", player_move, rival_move, result, hp_before, hp_after, 60
    )


def effects_for(timeline, actor):
    return {cue.effect for cue in timeline.cues if cue.actor == actor}


def test_landed_attack_lunges_and_staggers_the_defender():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 60, RIVAL: 48})
    assert "lunge" in effects_for(timeline, PLAYER)
    assert "stagger" in effects_for(timeline, RIVAL)
    assert "flash" in effects_for(timeline, RIVAL)


def test_dodged_attack_hops_instead_of_flashing():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=0),
        fighter_b=FighterTurnOutcome(move_name="Dance", dodged=True),
    )
    timeline = build(attack_move(), dodge_move(), result)
    assert "hop" in effects_for(timeline, RIVAL)
    assert "flash" not in effects_for(timeline, RIVAL)


def test_fully_blocked_attack_braces_instead_of_flashing():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=0),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result)
    assert "brace" in effects_for(timeline, RIVAL)
    assert "flash" not in effects_for(timeline, RIVAL)
    assert "stagger" not in effects_for(timeline, RIVAL)


def test_heal_move_glows():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Eat Garden", healed=15),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(heal_move(), block_move(), result,
                     hp_before={PLAYER: 40, RIVAL: 60}, hp_after={PLAYER: 55, RIVAL: 60})
    assert "glow" in effects_for(timeline, PLAYER)


def test_lifesteal_both_hurts_the_rival_and_glows_the_thief():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Steal", damage_dealt=10, healed=5),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move("Steal", lifesteal=True), block_move(), result,
                     hp_before={PLAYER: 40, RIVAL: 60}, hp_after={PLAYER: 45, RIVAL: 50})
    assert "glow" in effects_for(timeline, PLAYER)
    assert "flash" in effects_for(timeline, RIVAL)


def test_the_rival_acts_after_the_player():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=9),
    )
    timeline = build(attack_move(), attack_move("Scratch"), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 51, RIVAL: 48})
    player_lunge = next(c for c in timeline.cues if c.actor == PLAYER and c.effect == "lunge")
    rival_lunge = next(c for c in timeline.cues if c.actor == RIVAL and c.effect == "lunge")
    assert player_lunge.start_ms == 0
    assert rival_lunge.start_ms == ACTION_MS + GAP_MS


def test_a_defender_facing_no_attack_still_braces_once():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Dance"),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
        flavor_text="Both squirrels eye each other warily, neither committing to a move.",
    )
    timeline = build(dodge_move(), block_move(), result)
    assert "brace" in effects_for(timeline, PLAYER)
    assert "brace" in effects_for(timeline, RIVAL)


def test_a_double_knockout_announces_the_draw_once():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=9),
    )
    timeline = build(attack_move(), attack_move("Scratch"), result,
                     hp_before={PLAYER: 8, RIVAL: 5}, hp_after={PLAYER: 0, RIVAL: 0})
    assert "faint" in effects_for(timeline, PLAYER)
    assert "faint" in effects_for(timeline, RIVAL)
    knockouts = [text for _, text in timeline.captions if "down" in text]
    assert knockouts == ["Both squirrels are down! It's a draw!"]
    assert sample(timeline, timeline.total_ms).caption == knockouts[0]


def test_hp_slide_ends_on_the_real_post_turn_value():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 60, RIVAL: 48})
    assert sample(timeline, timeline.total_ms).hp == {PLAYER: 60, RIVAL: 48}


def test_hp_starts_at_the_pre_turn_value():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 60, RIVAL: 48})
    assert sample(timeline, 0).hp == {PLAYER: 60, RIVAL: 60}


def test_healing_and_taking_damage_in_one_turn_still_lands_exactly():
    # Eat Garden while the rival attacks: two slides for the player, and the
    # last one must land on the real post-turn HP.
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Eat Garden", healed=15),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=10),
    )
    timeline = build(heal_move(), attack_move("Scratch"), result,
                     hp_before={PLAYER: 55, RIVAL: 60}, hp_after={PLAYER: 60, RIVAL: 60})
    player_tweens = [tween for tween in timeline.hp_tweens if tween.actor == PLAYER]
    assert len(player_tweens) >= 1
    assert sample(timeline, timeline.total_ms).hp[PLAYER] == 60


def test_captions_are_ordered_and_sample_returns_the_most_recent():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=9),
    )
    timeline = build(attack_move(), attack_move("Scratch"), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 51, RIVAL: 48})
    starts = [start for start, _ in timeline.captions]
    assert starts == sorted(starts)
    assert sample(timeline, 0).caption == "Juliana uses Tail Smack!"
    assert "JOHN CENA" in sample(timeline, timeline.total_ms).caption


def test_total_ms_covers_every_cue():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=9),
    )
    timeline = build(attack_move(), attack_move("Scratch"), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 51, RIVAL: 48})
    assert timeline.total_ms >= max(c.start_ms + c.duration_ms for c in timeline.cues)


def test_a_knocked_out_squirrel_faints_and_stays_down():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before={PLAYER: 60, RIVAL: 12}, hp_after={PLAYER: 60, RIVAL: 0})
    assert "faint" in effects_for(timeline, RIVAL)
    assert abs(sample(timeline, timeline.total_ms).actors[RIVAL].rotation) == 90.0


def test_nobody_faints_while_both_are_standing():
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Tail Smack", damage_dealt=12),
        fighter_b=FighterTurnOutcome(move_name="Flex"),
    )
    timeline = build(attack_move(), block_move(), result,
                     hp_before=FULL_HP, hp_after={PLAYER: 60, RIVAL: 48})
    assert "faint" not in effects_for(timeline, PLAYER)
    assert "faint" not in effects_for(timeline, RIVAL)


def test_a_heal_that_overflows_is_clamped_before_the_damage_lands():
    # Eat Garden heals past full while the rival lands a big hit. The bar has to
    # slide up to exactly max HP -- never past it -- and only then slide back
    # down, finishing on the real post-turn value. This is the two-slide chain
    # that `test_healing_and_taking_damage_in_one_turn_still_lands_exactly`
    # describes but whose fixture collapses to a single slide.
    result = TurnResult(
        fighter_a=FighterTurnOutcome(move_name="Eat Garden", healed=15),
        fighter_b=FighterTurnOutcome(move_name="Scratch", damage_dealt=25),
    )
    timeline = build(heal_move(), attack_move("Scratch"), result,
                     hp_before={PLAYER: 55, RIVAL: 60}, hp_after={PLAYER: 45, RIVAL: 60})
    player_tweens = [tween for tween in timeline.hp_tweens if tween.actor == PLAYER]
    assert len(player_tweens) == 2
    assert player_tweens[0].hp_from == 55
    assert player_tweens[0].hp_to == 60     # clamped down from 70, not overshooting
    assert player_tweens[1].hp_to == 45     # pinned to the real post-turn HP
    assert sample(timeline, timeline.total_ms).hp[PLAYER] == 45


def captions_of(timeline):
    return [text for _, text in timeline.captions]


def build_one_sided(player_move, player_outcome):
    """A turn where only the player acts and the rival stands there."""
    rival_move = Move("Scurry", "defense", "", block_reduction=0.5)
    result = TurnResult(
        fighter_a=player_outcome,
        fighter_b=FighterTurnOutcome(move_name=rival_move.name),
    )
    return build_timeline(
        "Nutsy", "Chompy", player_move, rival_move, result,
        {PLAYER: 60, RIVAL: 60}, {PLAYER: 60, RIVAL: 60}, 60,
    )


def test_melee_whiff_says_the_rival_is_too_far():
    move = Move("Tail Smack", "attack", "", dmg_range=(10, 13), reach="melee")
    outcome = FighterTurnOutcome(move_name="Tail Smack", whiff_reason="too_far")
    captions = " ".join(captions_of(build_one_sided(move, outcome)))
    assert "too far away" in captions
    assert "shrugs it off" not in captions


def test_ranged_whiff_up_close_says_too_close():
    move = Move("Acorn Blast", "attack", "", dmg_range=(8, 16), reach="ranged")
    outcome = FighterTurnOutcome(move_name="Acorn Blast", whiff_reason="too_close")
    captions = " ".join(captions_of(build_one_sided(move, outcome)))
    assert "too close" in captions
    assert "shrugs it off" not in captions


def test_ranged_whiff_from_the_far_band_drops_short():
    move = Move("Acorn Blast", "attack", "", dmg_range=(8, 16), reach="ranged")
    outcome = FighterTurnOutcome(move_name="Acorn Blast", whiff_reason="too_far")
    captions = " ".join(captions_of(build_one_sided(move, outcome)))
    assert "drops well short" in captions
    assert "too close" not in captions


def test_a_whiff_does_not_stagger_the_other_squirrel():
    move = Move("Tail Smack", "attack", "", dmg_range=(10, 13), reach="melee")
    outcome = FighterTurnOutcome(move_name="Tail Smack", whiff_reason="too_far")
    timeline = build_one_sided(move, outcome)
    effects = {cue.effect for cue in timeline.cues if cue.actor == RIVAL}
    assert "stagger" not in effects
    assert "flash" not in effects
    # The previous version of this test passed whether or not the whiff branch
    # existed, because the old zero-damage path also skipped stagger and flash.
    # No brace cue is what actually tells a whiff apart from a shrug.
    assert "brace" not in effects
