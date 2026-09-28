"""Smoke tests: does the window version actually run?

Every other test here is pure — `battle.py` and `choreography.py` import no
pygame, and `test_sprites.py` sticks to `slug()`. That left `visual_game.py`
with no coverage at all, and it cost us: partway through widening the world the
game was completely broken at launch (it called an `arena.is_close` that had
been removed) while all 105 tests passed.

So these aren't detailed tests of the drawing. They drive a real `Game` through
its states with a dummy video driver and assert only that it gets there. The
job is to fail loudly when a rename or a signature change breaks the game, which
is exactly the failure the pure tests cannot see.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

import arena
import visual_game
from moves import MOVES

WINDOW = visual_game.WINDOW_SIZE


@pytest.fixture(scope="module")
def screen():
    pygame.init()
    surface = pygame.display.set_mode(WINDOW)
    yield surface
    pygame.quit()


@pytest.fixture
def game(screen):
    fresh = visual_game.Game(screen)
    fresh.typed_name = "Juliana"
    fresh.start_battle()
    return fresh


def run_out_the_animation(game, limit=2000):
    """Tick until the turn's animation finishes, or give up rather than hang."""
    for _ in range(limit):
        if game.state != "animating":
            return
        game.update(16)
    raise AssertionError("animation never finished")


def test_a_game_can_be_built_and_a_battle_started(game):
    assert game.state == "battle"
    assert game.player.hp == visual_game.START_HP
    assert game.rival.hp == visual_game.START_HP


def test_the_title_screen_draws(screen):
    fresh = visual_game.Game(screen)
    assert fresh.state == "title"
    fresh.draw()


def test_every_state_draws_without_crashing(game):
    game.draw()                        # battle
    game.take_turn(MOVES[0])
    assert game.state == "animating"
    game.draw()                        # animating
    run_out_the_animation(game)
    game.draw()                        # battle again, or result


def test_taking_a_turn_animates_and_comes_back_to_the_menu(game):
    game.take_turn(MOVES[0])
    assert game.state == "animating"
    run_out_the_animation(game)
    assert game.state in ("battle", "result")
    assert game.message


def test_walking_moves_the_player_and_the_rival_wanders(game):
    before_player = game.player_x
    before_rival = (game.rival_x, game.rival_y)
    game.update(16)                    # no keys held: only the rival should move
    assert game.player_x == before_player
    # Checked as a pair, not just x: the rival starts at a trunk now, so its
    # first move may be up the tree rather than along the ground.
    assert (game.rival_x, game.rival_y) != before_rival


def test_squirrels_stay_inside_the_world_over_a_long_idle(game):
    for _ in range(3000):
        game.update(16)
        assert arena.WALK_LEFT <= game.player_x <= arena.WALK_RIGHT
        assert arena.WALK_LEFT <= game.rival_x <= arena.WALK_RIGHT
        assert arena.gap(game.player_x, 0, game.rival_x, 0) <= arena.LEASH + 1


def test_a_whole_battle_can_be_fought_to_a_finish(game):
    for _ in range(200):
        if game.state == "result":
            break
        if game.state == "battle":
            game.take_turn(MOVES[0])
        run_out_the_animation(game)
    assert game.state == "result"
    assert game.outcome in ("a_wins", "b_wins", "draw")
    assert game._outcome_text()


def test_every_move_can_be_used_at_any_range(game):
    """A move should never crash, whatever it is or wherever the squirrels are."""
    for move in MOVES:
        for player_x, rival_x in ((400, 400 + arena.MIN_GAP), (400, 900), (400, 1100)):
            fresh = visual_game.Game(game.screen)
            fresh.typed_name = "Juliana"
            fresh.start_battle()
            fresh.player_x, fresh.rival_x = player_x, rival_x
            fresh.take_turn(move)
            run_out_the_animation(fresh)
            fresh.draw()


def test_a_squirrel_can_climb_and_come_back_down(game):
    game.player_x = arena.TREES[2]
    game.player_y = 0.0
    for _ in range(120):
        game.player_y = arena.climb(game.player_y, 1, 16)
    assert game.player_y == arena.MAX_CLIMB
    game.draw()
    for _ in range(300):
        game.player_y = arena.climb(game.player_y, -1, 16)
    assert game.player_y == 0.0


def test_height_changes_which_moves_reach(game):
    game.player_x = game.rival_x = arena.TREES[2]
    game.player_y, game.rival_y = 0.0, 0.0
    on_the_ground = arena.band(game.player_x, 0, game.rival_x, 0)
    game.player_y = arena.MAX_CLIMB
    up_a_tree = arena.band(game.player_x, game.player_y, game.rival_x, game.rival_y)
    assert on_the_ground == arena.CLOSE
    assert up_a_tree == arena.CLOSE     # 240 is still inside CLOSE_RANGE
    assert arena.gap(game.player_x, game.player_y, game.rival_x, game.rival_y) == \
        arena.MAX_CLIMB


def test_squirrels_never_end_up_inside_each_other(game):
    for _ in range(3000):
        game.update(16)
        same_height = abs(game.player_y - game.rival_y) < arena.CLIMB_CLEARANCE
        if same_height:
            assert abs(game.player_x - game.rival_x) >= arena.MIN_GAP - 1
        assert 0 <= game.player_y <= arena.MAX_CLIMB
        assert 0 <= game.rival_y <= arena.MAX_CLIMB
