from moves import MOVES


def move_named(name):
    for move in MOVES:
        if move.name == name:
            return move
    raise AssertionError("no move called {}".format(name))


def test_melee_moves_are_marked_melee():
    for name in ("Tail Smack", "Cheek Barrel", "Scratch", "Steal"):
        assert move_named(name).reach == "melee"


def test_ranged_moves_are_marked_ranged():
    for name in ("Acorn Blast", "Chirp", "Chirp Insanely"):
        assert move_named(name).reach == "ranged"


def test_defenses_and_heals_work_at_any_distance():
    for move in MOVES:
        if move.kind != "attack":
            assert move.reach == "any"


def test_every_attack_picks_a_side():
    for move in MOVES:
        if move.kind == "attack":
            assert move.reach in ("melee", "ranged")
