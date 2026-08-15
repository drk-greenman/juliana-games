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


MOVES: list[Move] = [
    Move("Tail Smack", "attack", "A reliable melee whack.", dmg_range=(10, 13)),
    Move("Cheek Barrel", "attack", "A barreling tackle, cheeks first.", dmg_range=(9, 15)),
    Move("Acorn Blast", "attack", "A balanced ranged acorn throw.", dmg_range=(8, 16)),
    Move("Scratch", "attack", "Quick claws, decent spread.", dmg_range=(7, 17)),
    Move("Chirp", "attack", "A risky, piercing shriek.", dmg_range=(4, 20)),
    Move("Chirp Insanely", "attack", "Totally unhinged. Could whiff, could devastate.", dmg_range=(0, 26)),
    Move(
        "Steal",
        "attack",
        "Swipes the rival's acorns; heals you for half the damage dealt.",
        dmg_range=(6, 14),
        lifesteal=True,
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
