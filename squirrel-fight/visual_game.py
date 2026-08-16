"""The pygame window version of Squirrel Fight.

The text version in `game.py` still works and is unaffected. Both import the
same `battle.py` and `moves.py`, so the fight rules live in exactly one place.
"""

from __future__ import annotations

import random
import sys

try:
    import pygame
except ImportError:
    sys.exit(
        "\n  Squirrel Fight's window version needs pygame.\n\n"
        "  Install it with:\n"
        "    python3 -m pip install -r squirrel-fight/requirements.txt\n\n"
        "  Or play the text version instead:\n"
        "    python3 squirrel-fight/game.py\n"
    )

from battle import Fighter, battle_outcome, resolve_turn
from choreography import PLAYER, RIVAL, ActorState, build_timeline, sample
from game import RIVAL_NAMES
from moves import MOVES
from sprites import load_pose

WINDOW_SIZE = (960, 640)
FPS = 60
START_HP = 60

COLOR_BG = (32, 36, 46)
COLOR_PANEL = (22, 26, 34)
COLOR_TEXT = (201, 209, 217)
COLOR_DIM = (125, 133, 144)
COLOR_SKY = (168, 220, 240)
COLOR_GRASS = (124, 186, 96)
COLOR_TRACK = (12, 14, 18)
COLOR_HP_GOOD = (46, 160, 67)
COLOR_HP_BAD = (218, 54, 51)

# Matches the terminal version's red/cyan/green move categories.
KIND_STYLE = {
    "attack": {"fill": (74, 31, 31), "edge": (184, 67, 61), "text": (255, 180, 174)},
    "defense": {"fill": (18, 54, 66), "edge": (61, 151, 184), "text": (169, 228, 245)},
    "heal": {"fill": (21, 58, 34), "edge": (63, 163, 92), "text": (167, 232, 187)},
}

STAGE_TOP = 92
GROUND_Y = 316
STAGE_BOTTOM = 332
MESSAGE_TOP = 332
PLAYER_X = 250
RIVAL_X = 710

# (row top, first move index, last move index exclusive)
BUTTON_ROWS = ((408, 0, 4), (456, 4, 7), (520, 7, 11), (584, 11, 12))
GROUP_LABELS = ((388, "ATTACKS", "attack"), (500, "DEFENSES", "defense"), (564, "HEAL", "heal"))

# Moves 1-9 sit on the number row; 10, 11 and 12 continue onto 0, - and =.
SHORTCUT_KEYS = (
    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6,
    pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0, pygame.K_MINUS, pygame.K_EQUALS,
)

# Adding a move to moves.py without also giving it a button and a shortcut key
# would silently drop it from the window version. Fail at startup instead.
_BUTTON_SLOTS = sum(last - first for _, first, last in BUTTON_ROWS)
if len(MOVES) != len(SHORTCUT_KEYS) or len(MOVES) != _BUTTON_SLOTS:
    raise RuntimeError(
        "moves.py has {} moves, but visual_game.py lays out {} buttons and {} "
        "shortcut keys. Update BUTTON_ROWS and SHORTCUT_KEYS to match.".format(
            len(MOVES), _BUTTON_SLOTS, len(SHORTCUT_KEYS)
        )
    )


class Button:
    def __init__(self, rect, move, number):
        self.rect = rect
        self.move = move
        self.number = number


def build_buttons():
    margin, gap, height = 24, 10, 42
    width = (WINDOW_SIZE[0] - 2 * margin - 3 * gap) // 4
    buttons = []
    for top, first, last in BUTTON_ROWS:
        for column, index in enumerate(range(first, last)):
            left = margin + column * (width + gap)
            buttons.append(Button(pygame.Rect(left, top, width, height), MOVES[index], index + 1))
    return buttons


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("helveticaneue,helvetica,arial", 40, bold=True)
        self.font = pygame.font.SysFont("helveticaneue,helvetica,arial", 18)
        self.bold = pygame.font.SysFont("helveticaneue,helvetica,arial", 16, bold=True)
        self.label_font = pygame.font.SysFont("helveticaneue,helvetica,arial", 12, bold=True)
        self.buttons = build_buttons()

        self.running = True
        self.state = "title"
        self.typed_name = ""
        self.player = None
        self.rival = None
        self.message = ""
        self.timeline = None
        self.frame = None
        self.elapsed_ms = 0
        self.outcome = "ongoing"
        self.hover = None

    # ----- state changes -------------------------------------------------

    def start_battle(self):
        name = self.typed_name.strip() or "You"
        self.player = Fighter(name=name, hp=START_HP, max_hp=START_HP)
        self.rival = Fighter(name=random.choice(RIVAL_NAMES), hp=START_HP, max_hp=START_HP)
        self.message = "{} vs. {}! Let the fight begin!".format(self.player.name, self.rival.name)
        self.timeline = None
        self.frame = None
        self.elapsed_ms = 0
        self.outcome = "ongoing"
        self.hover = None
        self.state = "battle"

    # ----- input ---------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return
        if self.state == "title":
            self._handle_title(event)
        elif self.state == "battle":
            self._handle_battle(event)
        elif self.state == "result":
            self._handle_result(event)
        # "animating" ignores everything except quitting.

    def _handle_title(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.start_battle()
        elif event.key == pygame.K_BACKSPACE:
            self.typed_name = self.typed_name[:-1]
        elif event.unicode and event.unicode.isprintable() and len(self.typed_name) < 18:
            self.typed_name += event.unicode

    def _handle_battle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self._button_at(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            button = self._button_at(event.pos)
            if button is not None:
                self.take_turn(button.move)
        elif event.type == pygame.KEYDOWN and event.key in SHORTCUT_KEYS:
            self.take_turn(MOVES[SHORTCUT_KEYS.index(event.key)])

    def _handle_result(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.start_battle()

    def _button_at(self, position):
        for button in self.buttons:
            if button.rect.collidepoint(position):
                return button
        return None

    def take_turn(self, move):
        raise NotImplementedError("Task 8 wires this up")

    # ----- per-frame -----------------------------------------------------

    def update(self, dt_ms):
        pass

    def draw(self):
        if self.state == "title":
            self._draw_title()
        else:
            self._draw_battle()
            if self.state == "result":
                self._draw_result_overlay()

    # ----- drawing -------------------------------------------------------

    def _draw_title(self):
        self.screen.fill(COLOR_BG)
        self._centered(self.title_font, "SQUIRREL FIGHT", COLOR_TEXT, 150)
        self._centered(self.font, "Name your squirrel, then press Enter.", COLOR_DIM, 220)

        box = pygame.Rect(0, 0, 440, 56)
        box.center = (WINDOW_SIZE[0] // 2, 300)
        pygame.draw.rect(self.screen, COLOR_PANEL, box, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_DIM, box, width=2, border_radius=8)
        caret = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        typed = self.font.render(self.typed_name + caret, True, COLOR_TEXT)
        self.screen.blit(typed, (box.x + 16, box.centery - typed.get_height() // 2))

        self._centered(self.font, "Click a move, or use the number row: 1-9, then 0, - and =",
                       COLOR_DIM, 420)
        self._centered(self.font, "Esc quits at any time.", COLOR_DIM, 450)

    def _centered(self, font, text, color, top):
        surface = font.render(text, True, color)
        self.screen.blit(surface, (WINDOW_SIZE[0] // 2 - surface.get_width() // 2, top))

    def _draw_battle(self):
        self.screen.fill(COLOR_BG)
        self._draw_hp_panel()
        self._draw_stage()
        self._draw_message()
        self._draw_buttons()

    def _current_hp(self):
        if self.frame is not None:
            return self.frame.hp
        return {PLAYER: self.player.hp, RIVAL: self.rival.hp}

    def _draw_hp_panel(self):
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, WINDOW_SIZE[0], STAGE_TOP))
        hp = self._current_hp()
        self._draw_hp_bar(24, self.player.name, hp[PLAYER], self.player.max_hp,
                          COLOR_HP_GOOD, False)
        self._draw_hp_bar(WINDOW_SIZE[0] - 24 - 380, self.rival.name, hp[RIVAL],
                          self.rival.max_hp, COLOR_HP_BAD, True)

    def _draw_hp_bar(self, left, name, hp, max_hp, color, right_aligned):
        width = 380
        label = self.bold.render(name, True, COLOR_TEXT)
        amount = self.font.render("{} / {}".format(max(0, hp), max_hp), True, COLOR_DIM)
        if right_aligned:
            self.screen.blit(label, (left + width - label.get_width(), 14))
            self.screen.blit(amount, (left + width - amount.get_width(), 62))
        else:
            self.screen.blit(label, (left, 14))
            self.screen.blit(amount, (left, 62))

        track = pygame.Rect(left, 40, width, 16)
        pygame.draw.rect(self.screen, COLOR_TRACK, track, border_radius=8)
        filled = int(width * max(0, min(max_hp, hp)) / max_hp)
        if filled > 0:
            fill = pygame.Rect(left + (width - filled if right_aligned else 0), 40, filled, 16)
            pygame.draw.rect(self.screen, color, fill, border_radius=8)

    def _draw_stage(self):
        pygame.draw.rect(self.screen, COLOR_SKY, (0, STAGE_TOP, WINDOW_SIZE[0], GROUND_Y - STAGE_TOP))
        pygame.draw.rect(self.screen, COLOR_GRASS, (0, GROUND_Y, WINDOW_SIZE[0], STAGE_BOTTOM - GROUND_Y))
        self._draw_squirrel(PLAYER, PLAYER_X)
        self._draw_squirrel(RIVAL, RIVAL_X)

    def _draw_squirrel(self, actor, center_x):
        state = self.frame.actors[actor] if self.frame is not None else ActorState()
        image = load_pose(actor, "idle")
        if actor == RIVAL:
            image = pygame.transform.flip(image, True, False)
        if state.scale != 1.0:
            size = (max(1, int(image.get_width() * state.scale)),
                    max(1, int(image.get_height() * state.scale)))
            image = pygame.transform.smoothscale(image, size)
        if state.rotation:
            image = pygame.transform.rotate(image, -state.rotation)
        if state.tint > 0 or state.glow > 0 or state.alpha < 1.0:
            # Copy first: never colour the cached surface that sprites.py hands back.
            image = image.copy()
            if state.tint > 0:
                image.fill((int(210 * state.tint), 0, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if state.glow > 0:
                image.fill((0, int(170 * state.glow), 50, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if state.alpha < 1.0:
                image.set_alpha(int(255 * state.alpha))
        rect = image.get_rect()
        rect.midbottom = (int(center_x + state.offset_x), int(GROUND_Y + 10 + state.offset_y))
        self.screen.blit(image, rect)

    def _message_text(self):
        if self.state == "animating" and self.frame is not None:
            return self.frame.caption
        if self.hover is not None:
            return "{} — {}".format(self.hover.move.name, self.hover.move.description)
        return self.message

    def _draw_message(self):
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, MESSAGE_TOP, WINDOW_SIZE[0], 52))
        text = self.font.render(self._message_text(), True, COLOR_TEXT)
        self.screen.blit(text, (24, MESSAGE_TOP + 26 - text.get_height() // 2))

    def _draw_buttons(self):
        dimmed = self.state != "battle"
        for top, caption, kind in GROUP_LABELS:
            label = self.label_font.render(caption, True, KIND_STYLE[kind]["text"])
            self.screen.blit(label, (24, top))
        for button in self.buttons:
            style = KIND_STYLE[button.move.kind]
            fill, edge, text_color = style["fill"], style["edge"], style["text"]
            if dimmed:
                fill = tuple(channel // 2 for channel in fill)
                edge = tuple(channel // 2 for channel in edge)
                text_color = tuple(channel // 2 for channel in text_color)
            elif button is self.hover:
                fill = tuple(min(255, channel + 26) for channel in fill)
            pygame.draw.rect(self.screen, fill, button.rect, border_radius=7)
            pygame.draw.rect(self.screen, edge, button.rect, width=2, border_radius=7)
            caption = "{}  {}".format(button.number, button.move.name)
            text = self.bold.render(caption, True, text_color)
            self.screen.blit(text, text.get_rect(center=button.rect.center))

    def _draw_result_overlay(self):
        pass


def main():
    pygame.init()
    try:
        screen = pygame.display.set_mode(WINDOW_SIZE)
    except pygame.error:
        pygame.quit()
        sys.exit(
            "\n  No display available, so the window version can't run here.\n\n"
            "  Play the text version instead:\n"
            "    python3 squirrel-fight/game.py\n"
        )
    pygame.display.set_caption("Squirrel Fight")
    clock = pygame.time.Clock()
    game = Game(screen)
    while game.running:
        dt_ms = clock.tick(FPS)
        for event in pygame.event.get():
            game.handle_event(event)
        game.update(dt_ms)
        game.draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
