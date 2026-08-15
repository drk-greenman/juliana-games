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
        return int(raw_damage * (1 - defending_move.block_reduction)), False
    if defending_move.block_flat is not None:
        return max(0, raw_damage - defending_move.block_flat), False
    return raw_damage, False


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def resolve_turn(fighter_a: Fighter, move_a: Move, fighter_b: Fighter, move_b: Move) -> TurnResult:
    outcome_a = FighterTurnOutcome(move_name=move_a.name)
    outcome_b = FighterTurnOutcome(move_name=move_b.name)
    flavor_text = None

    dmg_a_to_b = 0
    dmg_b_to_a = 0

    if move_a.kind == "attack":
        raw = _roll_damage(move_a)
        defending = move_b if move_b.kind == "defense" else None
        dmg_a_to_b, b_dodged = _mitigate(raw, defending)
        if defending is not None and defending.dodge_chance is not None:
            outcome_b.dodged = b_dodged
        if move_a.lifesteal:
            outcome_a.healed += dmg_a_to_b // 2

    if move_b.kind == "attack":
        raw = _roll_damage(move_b)
        defending = move_a if move_a.kind == "defense" else None
        dmg_b_to_a, a_dodged = _mitigate(raw, defending)
        if defending is not None and defending.dodge_chance is not None:
            outcome_a.dodged = a_dodged
        if move_b.lifesteal:
            outcome_b.healed += dmg_b_to_a // 2

    if move_a.kind == "heal":
        outcome_a.healed += _roll_heal(move_a)

    if move_b.kind == "heal":
        outcome_b.healed += _roll_heal(move_b)

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
