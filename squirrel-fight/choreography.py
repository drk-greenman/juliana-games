"""Turns a resolved turn into a timeline of timed animation cues.

This is to animation what `game.py`'s `format_turn_result_lines()` is to text:
both take the `TurnResult` that `battle.resolve_turn()` returns and turn it into
presentation. Nothing here imports pygame, so it is pure and testable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

PLAYER = "player"
RIVAL = "rival"
ACTORS = (PLAYER, RIVAL)

# +1 faces right, -1 faces left. Used to mirror every effect for the rival.
FACING = {PLAYER: 1, RIVAL: -1}

# All timings in milliseconds.
ACTION_MS = 700      # how long one fighter's action window lasts
GAP_MS = 120         # pause between the two fighters' windows
IMPACT_MS = 260      # when a lunge connects, measured from its window start
DODGE_MS = 180       # when a dodger starts moving, measured from the window start
STAGGER_MS = 340
FLASH_MS = 220
HOP_MS = 320
BRACE_MS = 400
GLOW_MS = 420
HP_MS = 340          # how long an HP bar takes to slide to its new value
FAINT_MS = 500       # how long the topple takes (the cue itself lasts longer)
TAIL_MS = 400        # dead air after the last cue so the last line can be read


@dataclass(frozen=True)
class ActorState:
    """Where one squirrel is and what it looks like at a single instant."""

    offset_x: float = 0.0
    offset_y: float = 0.0
    rotation: float = 0.0
    scale: float = 1.0
    tint: float = 0.0    # red "just got hit" flash, 0..1
    glow: float = 0.0    # green "healing" glow, 0..1
    alpha: float = 1.0


@dataclass(frozen=True)
class Cue:
    start_ms: int
    duration_ms: int
    actor: str
    effect: str          # lunge | stagger | flash | hop | brace | glow | faint


@dataclass(frozen=True)
class HpTween:
    actor: str
    start_ms: int
    duration_ms: int
    hp_from: int
    hp_to: int


@dataclass(frozen=True)
class Timeline:
    cues: list[Cue] = field(default_factory=list)
    captions: list[tuple[int, str]] = field(default_factory=list)   # sorted by start_ms
    hp_tweens: list[HpTween] = field(default_factory=list)
    hp_start: dict[str, int] = field(default_factory=dict)
    total_ms: int = 0


@dataclass(frozen=True)
class FrameState:
    """Everything the renderer needs for one frame, from one `sample()` call."""

    actors: dict[str, ActorState]
    hp: dict[str, int]
    caption: str


def sample(timeline: Timeline, t_ms: int) -> FrameState:
    actors = {actor: ActorState() for actor in ACTORS}
    for cue in timeline.cues:
        end_ms = cue.start_ms + cue.duration_ms
        if not (cue.start_ms <= t_ms <= end_ms):
            continue
        elapsed_ms = t_ms - cue.start_ms
        if cue.duration_ms <= 0:
            progress = 1.0
        else:
            progress = min(1.0, max(0.0, elapsed_ms / cue.duration_ms))
        actors[cue.actor] = _compose(
            actors[cue.actor],
            _effect_state(cue.effect, progress, elapsed_ms, FACING[cue.actor]),
        )

    hp = dict(timeline.hp_start)
    for tween in timeline.hp_tweens:
        if t_ms >= tween.start_ms + tween.duration_ms:
            hp[tween.actor] = tween.hp_to
        elif t_ms > tween.start_ms:
            progress = (t_ms - tween.start_ms) / tween.duration_ms
            hp[tween.actor] = round(tween.hp_from + (tween.hp_to - tween.hp_from) * progress)

    # Relies on captions being sorted by start_ms: the last one that has started wins.
    caption = ""
    for start_ms, text in timeline.captions:
        if t_ms >= start_ms:
            caption = text

    return FrameState(actors=actors, hp=hp, caption=caption)


def _compose(base: ActorState, extra: ActorState) -> ActorState:
    """Two cues on the same squirrel at the same moment stack."""
    return ActorState(
        offset_x=base.offset_x + extra.offset_x,
        offset_y=base.offset_y + extra.offset_y,
        rotation=base.rotation + extra.rotation,
        scale=base.scale * extra.scale,
        tint=max(base.tint, extra.tint),
        glow=max(base.glow, extra.glow),
        alpha=min(base.alpha, extra.alpha),
    )


def _arc(progress: float) -> float:
    """0 -> 1 -> 0, smoothly. Zero at both ends, so cues start and finish home."""
    return math.sin(math.pi * progress)


def _shudder(progress: float) -> float:
    """A quick wobble that dies away. Zero at progress 0."""
    return math.sin(progress * math.pi * 3.0) * (1.0 - progress)


def _effect_state(effect: str, progress: float, elapsed_ms: int, facing: int) -> ActorState:
    if effect == "lunge":
        swing = _arc(progress)
        return ActorState(offset_x=facing * 70.0 * swing, rotation=-facing * 12.0 * swing)
    if effect == "stagger":
        knock = _shudder(progress)
        return ActorState(offset_x=-facing * 26.0 * knock, rotation=facing * 9.0 * knock)
    if effect == "flash":
        # Instant on impact, then fades. This is the one effect that is loudest
        # at progress 0 rather than silent.
        return ActorState(tint=1.0 - progress)
    if effect == "hop":
        # The lift is capped by the headroom between a standing squirrel's ears
        # and the top of the stage. Raise it and the dodger jumps up over the HP
        # bars; `visual_game` clips the stage, so it would be sliced flat instead.
        swing = _arc(progress)
        return ActorState(offset_x=-facing * 34.0 * swing, offset_y=-30.0 * swing)
    if effect == "brace":
        crouch = _arc(progress)
        return ActorState(offset_x=-facing * 12.0 * crouch, scale=1.0 - 0.09 * crouch)
    if effect == "glow":
        lift = _arc(progress)
        return ActorState(glow=lift, offset_y=-10.0 * lift)
    if effect == "faint":
        # Driven by absolute elapsed time, not progress: the cue is stretched to
        # the end of the timeline so the squirrel stays down, but the topple
        # itself always takes FAINT_MS.
        fallen = min(1.0, elapsed_ms / FAINT_MS)
        return ActorState(
            rotation=facing * 90.0 * fallen,
            # Just enough of a slump to read as hitting the dirt. Any more and
            # the fallen squirrel's head sinks through the grass into the
            # message strip, since it is already standing on the stage floor.
            offset_y=6.0 * fallen,
            alpha=1.0 - 0.45 * fallen,
        )
    return ActorState()


def build_timeline(
    player_name,
    rival_name,
    player_move,
    rival_move,
    result,
    hp_before,
    hp_after,
    max_hp,
) -> Timeline:
    """Lay out one resolved turn as cues, captions and HP slides.

    `hp_before` and `hp_after` are `{PLAYER: int, RIVAL: int}`. The caller must
    capture `hp_before` *before* calling `battle.resolve_turn()`, which mutates
    `Fighter.hp` in place. Nothing here re-simulates the fight; it only shows a
    result that has already been computed. Both fighters share one `max_hp`.
    """
    names = {PLAYER: player_name, RIVAL: rival_name}
    moves = {PLAYER: player_move, RIVAL: rival_move}
    cues = []
    captions = []
    hp_events = {PLAYER: [], RIVAL: []}

    rival_start_ms = ACTION_MS + GAP_MS
    sides = (
        (PLAYER, RIVAL, result.fighter_a, result.fighter_b, 0),
        (RIVAL, PLAYER, result.fighter_b, result.fighter_a, rival_start_ms),
    )

    for actor, other, own, other_outcome, start_ms in sides:
        move = moves[actor]
        captions.append((start_ms, "{} uses {}!".format(names[actor], move.name)))

        if move.kind == "attack":
            cues.append(Cue(start_ms, ACTION_MS, actor, "lunge"))
            hit_ms = start_ms + IMPACT_MS
            if other_outcome.dodged:
                cues.append(Cue(start_ms + DODGE_MS, HOP_MS, other, "hop"))
                captions.append((hit_ms, "{} dodges out of the way!".format(names[other])))
            elif own.damage_dealt > 0:
                cues.append(Cue(hit_ms, STAGGER_MS, other, "stagger"))
                cues.append(Cue(hit_ms, FLASH_MS, other, "flash"))
                captions.append((hit_ms, "{} hits {} for {} damage!".format(
                    names[actor], names[other], own.damage_dealt)))
                hp_events[other].append((hit_ms, HP_MS, -own.damage_dealt))
            else:
                cues.append(Cue(hit_ms, BRACE_MS, other, "brace"))
                captions.append((hit_ms, "{} shrugs it off!".format(names[other])))
            if move.lifesteal and own.healed > 0:
                cues.append(Cue(hit_ms, GLOW_MS, actor, "glow"))
                captions.append((hit_ms + 120, "{} steals {} HP!".format(
                    names[actor], own.healed)))
                hp_events[actor].append((hit_ms + 120, HP_MS, own.healed))

        elif move.kind == "defense":
            # If the other squirrel is attacking, this one already gets a hop or
            # brace as a reaction inside that attack's window. Only add a stance
            # of its own when there is no attack to react to.
            if moves[other].kind != "attack":
                cues.append(Cue(start_ms, BRACE_MS, actor, "brace"))

        elif move.kind == "heal":
            cues.append(Cue(start_ms, GLOW_MS, actor, "glow"))
            if own.healed > 0:
                captions.append((start_ms + 200, "{} heals {} HP!".format(
                    names[actor], own.healed)))
                hp_events[actor].append((start_ms + 200, HP_MS, own.healed))

    if result.flavor_text:
        captions.append((rival_start_ms + 350, result.flavor_text))

    hp_tweens = _build_hp_tweens(hp_events, hp_before, hp_after, max_hp)

    end_of_action_ms = rival_start_ms + ACTION_MS
    knocked_out = [actor for actor in ACTORS if hp_after[actor] <= 0]

    candidates = (
        [end_of_action_ms]
        + [cue.start_ms + cue.duration_ms for cue in cues]
        + [start for start, _ in captions]
        + [tween.start_ms + tween.duration_ms for tween in hp_tweens]
    )
    if knocked_out:
        # The timeline has to outlast the topple, or the faint cue gets cut off
        # part-way and the squirrel freezes at a half-fallen angle.
        candidates.append(end_of_action_ms + FAINT_MS)
    total_ms = max(candidates) + TAIL_MS

    for actor in knocked_out:
        # Stretched to the end of the timeline so the squirrel stays down.
        cues.append(Cue(end_of_action_ms, total_ms - end_of_action_ms, actor, "faint"))

    if len(knocked_out) == len(ACTORS):
        # Both toppled at once. Two captions on the same millisecond would hide
        # one of them, and the terminal version says it as a single line too.
        captions.append((end_of_action_ms + 120, "Both squirrels are down! It's a draw!"))
    else:
        for actor in knocked_out:
            captions.append((end_of_action_ms + 120, "{} is down!".format(names[actor])))

    captions.sort(key=lambda caption: caption[0])
    return Timeline(
        cues=cues,
        captions=captions,
        hp_tweens=hp_tweens,
        hp_start=dict(hp_before),
        total_ms=total_ms,
    )


def _build_hp_tweens(hp_events, hp_before, hp_after, max_hp):
    """Chain each squirrel's HP changes so the last one lands exactly on `hp_after`.

    A squirrel can both heal and take damage in one turn (Eat Garden against an
    attack), so it can need two slides. `battle.py` clamps the *net* change, so
    intermediate values are clamped for display only and the final slide is
    pinned to the real post-turn HP rather than recomputed.
    """
    tweens = []
    for actor in ACTORS:
        events = sorted(hp_events[actor])
        current = hp_before[actor]
        for index, (start_ms, duration_ms, delta) in enumerate(events):
            is_last = index == len(events) - 1
            if is_last:
                target = hp_after[actor]
            else:
                target = max(0, min(max_hp, current + delta))
            if target != current:
                tweens.append(HpTween(actor, start_ms, duration_ms, current, target))
            current = target
    tweens.sort(key=lambda tween: tween.start_ms)
    return tweens
