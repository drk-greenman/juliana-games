from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Move:
    name: str
    kind: Literal["attack", "defense", "heal"]
    description: str
    dmg_range: tuple[int, int] | None = None
    lifesteal: bool = False
    dodge_chance: float | None = None
    block_reduction: float | None = None
    block_flat: int | None = None
    heal_range: tuple[int, int] | None = None
    # How close you have to be for this to connect. Defaults to "any" so a new
    # move without a reach still works everywhere rather than silently whiffing.
    reach: Literal["melee", "ranged", "any"] = "any"


MOVES: list[Move] = [
    Move("Tail Smack", "attack", "A reliable melee whack.", dmg_range=(10, 13), reach="melee"),
    Move("Cheek Barrel", "attack", "A barreling tackle, cheeks first.", dmg_range=(9, 15), reach="melee"),
    Move("Acorn Blast", "attack", "A balanced ranged acorn throw.", dmg_range=(8, 16), reach="ranged"),
    Move("Scratch", "attack", "Quick claws, decent spread.", dmg_range=(7, 17), reach="melee"),
    Move("Chirp", "attack", "A risky, piercing shriek.", dmg_range=(4, 20), reach="ranged"),
    Move("Chirp Insanely", "attack", "Totally unhinged. Could whiff, could devastate.", dmg_range=(0, 26), reach="ranged"),
    Move(
        "Steal",
        "attack",
        "Swipes the rival's acorns; heals you for half the damage dealt.",
        dmg_range=(6, 14),
        lifesteal=True,
        reach="melee",
    ),
    Move("Dance", "defense", "A flashy juke. 50% chance to fully dodge.", dodge_chance=0.5),
    Move("Moonwalk", "defense", "A cooler, riskier juke. 35% chance to fully dodge.", dodge_chance=0.35),
    Move("Scurry", "defense", "Duck and cover. Always halves incoming damage.", block_reduction=0.5),
    Move("Flex", "defense", "Flex so hard nothing gets through. Deflects 36 damage flat.", block_flat=36),
    Move(
        "Eat Garden",
        "heal",
        "Snack on some veggies. Restores 12-18 HP, but doesn't defend.",
        heal_range=(12, 18),
    ),
]
