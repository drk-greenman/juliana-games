from __future__ import annotations

import random
from dataclasses import dataclass

from moves import Move


@dataclass
class Fighter:
    name: str
    hp: int
    max_hp: int


@dataclass
class FighterTurnOutcome:
    move_name: str
    damage_dealt: int = 0
    healed: int = 0
    dodged: bool = False
    # None when the move landed; otherwise "too_far" or "too_close", so the
    # caption can explain itself without choreography learning any geometry.
    whiff_reason: str | None = None


@dataclass
class TurnResult:
    fighter_a: FighterTurnOutcome
    fighter_b: FighterTurnOutcome
    flavor_text: str | None = None


def _roll_damage(move: Move) -> int:
    lo, hi = move.dmg_range
    return random.randint(lo, hi)


def _roll_heal(move: Move) -> int:
    lo, hi = move.heal_range
    return random.randint(lo, hi)


def _mitigate(raw_damage: int, defending_move: Move | None) -> tuple[int, bool]:
    if defending_move is None or defending_move.kind != "defense":
        return raw_damage, False
    if defending_move.dodge_chance is not None:
        if random.random() < defending_move.dodge_chance:
            return 0, True
        return raw_damage, False
    if defending_move.block_reduction is not None:
        return max(0, int(raw_damage * (1 - defending_move.block_reduction))), False
    if defending_move.block_flat is not None:
        return max(0, raw_damage - defending_move.block_flat), False
    return raw_damage, False


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _capped_heal(raw_heal: int, hp_before: int, damage_taken: int, max_hp: int) -> int:
    room = max_hp - (hp_before - damage_taken)
    return max(0, min(raw_heal, room))


def _reaches(move: Move, band: str | None) -> bool:
    """Can this move connect from this range band?

    `band` is "close", "mid" or "far", or None when distance isn't part of the
    game at all — which is how the terminal version in `game.py` keeps playing
    exactly as it always has.

    The band names are literals rather than imports from `arena`: the rules here
    stay free of stage geometry, and pulling in `arena` for two strings would
    drag pixel constants along with them.
    """
    if band is None or move.reach == "any":
        return True
    if move.reach == "melee":
        return band == "close"
    return band == "mid"


def _whiff_reason(move: Move, band: str | None) -> str:
    """Why a move that didn't reach didn't reach."""
    if move.reach == "ranged" and band == "close":
        return "too_close"
    return "too_far"


def resolve_turn(
    fighter_a: Fighter,
    move_a: Move,
    fighter_b: Fighter,
    move_b: Move,
    band: str | None = None,
) -> TurnResult:
    outcome_a = FighterTurnOutcome(move_name=move_a.name)
    outcome_b = FighterTurnOutcome(move_name=move_b.name)
    flavor_text = None

    dmg_a_to_b = 0
    dmg_b_to_a = 0

    if move_a.kind == "attack":
        if not _reaches(move_a, band):
            outcome_a.whiff_reason = _whiff_reason(move_a, band)
        else:
            raw = _roll_damage(move_a)
            defending = move_b if move_b.kind == "defense" else None
            dmg_a_to_b, b_dodged = _mitigate(raw, defending)
            if defending is not None and defending.dodge_chance is not None:
                outcome_b.dodged = b_dodged

    if move_b.kind == "attack":
        if not _reaches(move_b, band):
            outcome_b.whiff_reason = _whiff_reason(move_b, band)
        else:
            raw = _roll_damage(move_b)
            defending = move_a if move_a.kind == "defense" else None
            dmg_b_to_a, a_dodged = _mitigate(raw, defending)
            if defending is not None and defending.dodge_chance is not None:
                outcome_a.dodged = a_dodged

    if move_a.kind == "attack" and move_a.lifesteal:
        outcome_a.healed += _capped_heal(dmg_a_to_b // 2, fighter_a.hp, dmg_b_to_a, fighter_a.max_hp)

    if move_b.kind == "attack" and move_b.lifesteal:
        outcome_b.healed += _capped_heal(dmg_b_to_a // 2, fighter_b.hp, dmg_a_to_b, fighter_b.max_hp)

    if move_a.kind == "heal":
        outcome_a.healed += _capped_heal(_roll_heal(move_a), fighter_a.hp, dmg_b_to_a, fighter_a.max_hp)

    if move_b.kind == "heal":
        outcome_b.healed += _capped_heal(_roll_heal(move_b), fighter_b.hp, dmg_a_to_b, fighter_b.max_hp)

    if move_a.kind == "defense" and move_b.kind == "defense":
        flavor_text = "Both squirrels eye each other warily, neither committing to a move."

    outcome_a.damage_dealt = dmg_a_to_b
    outcome_b.damage_dealt = dmg_b_to_a

    fighter_a.hp = _clamp(fighter_a.hp - dmg_b_to_a + outcome_a.healed, 0, fighter_a.max_hp)
    fighter_b.hp = _clamp(fighter_b.hp - dmg_a_to_b + outcome_b.healed, 0, fighter_b.max_hp)

    return TurnResult(fighter_a=outcome_a, fighter_b=outcome_b, flavor_text=flavor_text)


def battle_outcome(fighter_a: Fighter, fighter_b: Fighter) -> str:
    a_down = fighter_a.hp <= 0
    b_down = fighter_b.hp <= 0
    if a_down and b_down:
        return "draw"
    if a_down:
        return "b_wins"
    if b_down:
        return "a_wins"
    return "ongoing"
