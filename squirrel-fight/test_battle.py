import battle as battle_module
from battle import Fighter, resolve_turn, battle_outcome
from moves import Move


def make_attack(name, dmg_range, lifesteal=False):
    return Move(name=name, kind="attack", description="", dmg_range=dmg_range, lifesteal=lifesteal)


def make_dodge(name, chance):
    return Move(name=name, kind="defense", description="", dodge_chance=chance)


def make_block_pct(name, reduction):
    return Move(name=name, kind="defense", description="", block_reduction=reduction)


def make_block_flat(name, flat):
    return Move(name=name, kind="defense", description="", block_flat=flat)


def make_heal(name, heal_range):
    return Move(name=name, kind="heal", description="", heal_range=heal_range)


def test_attack_vs_attack_deals_full_damage_both_ways(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Tail Smack", (10, 13))
    move_b = make_attack("Acorn Blast", (8, 16))
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 13
    assert result.fighter_b.damage_dealt == 16
    assert b.hp == 60 - 13
    assert a.hp == 60 - 16


def test_block_percentage_halves_damage(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16))
    move_b = make_block_pct("Scurry", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 8
    assert b.hp == 60 - 8


def test_block_percentage_floors_odd_damage(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: 15)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Scratch", (7, 17))
    move_b = make_block_pct("Scurry", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 7  # int(15 * 0.5) == 7, not round(7.5) == 8
    assert b.hp == 60 - 7


def test_block_flat_reduces_by_fixed_amount(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Chirp Insanely", (0, 26))
    move_b = make_block_flat("Flex", 36)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 0
    assert b.hp == 60


def test_dodge_success_avoids_all_damage(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    monkeypatch.setattr(battle_module.random, "random", lambda: 0.0)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16))
    move_b = make_dodge("Dance", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 0
    assert result.fighter_b.dodged is True
    assert b.hp == 60


def test_dodge_failure_takes_full_damage(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    monkeypatch.setattr(battle_module.random, "random", lambda: 0.99)
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Acorn Blast", (8, 16))
    move_b = make_dodge("Dance", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 16
    assert result.fighter_b.dodged is False
    assert b.hp == 60 - 16


def test_heal_restores_hp_and_is_capped_at_max(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=55, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_heal("Eat Garden", (12, 18))
    move_b = make_dodge("Dance", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.healed == 5
    assert a.hp == 60
    assert b.hp == 60
    assert result.fighter_b.dodged is False


def test_attack_vs_heal_healer_still_takes_full_damage(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=20, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_heal("Eat Garden", (12, 18))
    move_b = make_attack("Chirp Insanely", (0, 26))
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.healed == 18
    assert result.fighter_b.damage_dealt == 26
    assert a.hp == 12


def test_heal_vs_heal_both_restore_hp(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=40, max_hp=60)
    b = Fighter(name="B", hp=40, max_hp=60)
    move_a = make_heal("Eat Garden", (12, 18))
    move_b = make_heal("Eat Garden", (12, 18))
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.healed == 18
    assert result.fighter_b.healed == 18
    assert a.hp == 58
    assert b.hp == 58


def test_steal_heals_attacker_by_half_of_actual_damage_dealt(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=40, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Steal", (6, 14), lifesteal=True)
    move_b = make_block_pct("Scurry", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 7
    assert result.fighter_a.healed == 3
    assert a.hp == 43
    assert b.hp == 53


def test_steal_heals_nothing_when_fully_dodged(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    monkeypatch.setattr(battle_module.random, "random", lambda: 0.0)
    a = Fighter(name="A", hp=40, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_attack("Steal", (6, 14), lifesteal=True)
    move_b = make_dodge("Dance", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert result.fighter_a.damage_dealt == 0
    assert result.fighter_a.healed == 0
    assert a.hp == 40


def test_defense_vs_defense_is_a_harmless_clash():
    a = Fighter(name="A", hp=60, max_hp=60)
    b = Fighter(name="B", hp=60, max_hp=60)
    move_a = make_dodge("Dance", 0.5)
    move_b = make_block_pct("Scurry", 0.5)
    result = resolve_turn(a, move_a, b, move_b)
    assert a.hp == 60
    assert b.hp == 60
    assert result.flavor_text is not None


def test_double_ko_is_a_draw(monkeypatch):
    monkeypatch.setattr(battle_module.random, "randint", lambda lo, hi: hi)
    a = Fighter(name="A", hp=10, max_hp=60)
    b = Fighter(name="B", hp=10, max_hp=60)
    move_a = make_attack("Chirp Insanely", (0, 26))
    move_b = make_attack("Chirp Insanely", (0, 26))
    resolve_turn(a, move_a, b, move_b)
    assert battle_outcome(a, b) == "draw"


def test_battle_outcome_ongoing_when_both_alive():
    a = Fighter(name="A", hp=30, max_hp=60)
    b = Fighter(name="B", hp=30, max_hp=60)
    assert battle_outcome(a, b) == "ongoing"


def test_battle_outcome_a_wins_when_b_at_zero():
    a = Fighter(name="A", hp=10, max_hp=60)
    b = Fighter(name="B", hp=0, max_hp=60)
    assert battle_outcome(a, b) == "a_wins"
