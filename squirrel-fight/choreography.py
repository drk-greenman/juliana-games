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
        swing = _arc(progress)
        return ActorState(offset_x=-facing * 34.0 * swing, offset_y=-52.0 * swing)
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
            offset_y=26.0 * fallen,
            alpha=1.0 - 0.45 * fallen,
        )
    return ActorState()
