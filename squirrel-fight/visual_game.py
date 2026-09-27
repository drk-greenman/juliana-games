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

import arena
from battle import Fighter, battle_outcome, resolve_turn
from choreography import PLAYER, RIVAL, ActorState, build_timeline, sample
from game import RIVAL_NAMES
from moves import MOVES
from sprites import available_squirrels, load_background, load_pose, slug

WINDOW_SIZE = (960, 840)
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
# The stage is 440px tall so a squirrel can climb a tree and still fit under the
# ceiling. Everything below it sits 200px lower than it used to; the bottom
# margin is unchanged (buttons end at 826 of 840, as they ended at 626 of 640).
GROUND_Y = 516
STAGE_BOTTOM = 532
MESSAGE_TOP = 532

# (row top, first move index, last move index exclusive)
BUTTON_ROWS = ((608, 0, 4), (656, 4, 7), (720, 7, 11), (784, 11, 12))
GROUP_LABELS = ((588, "ATTACKS", "attack"), (700, "DEFENSES", "defense"), (764, "HEAL", "heal"))

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


def pick_player_art(rival_name):
    """Borrow a drawing for the player, avoiding the one the rival is using.

    Every drawing so far is a named rival, and the player's squirrel is whoever
    Juliana says it is — so the player borrows a face rather than going without
    one. Returns None when there is nothing to borrow, which lands the player
    back on the code-drawn placeholder.
    """
    others = sorted(available_squirrels() - {slug(rival_name)})
    return random.choice(others) if others else None


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
        self.art_names = {PLAYER: None, RIVAL: None}
        self.message = ""
        self.timeline = None
        self.frame = None
        self.elapsed_ms = 0
        self.outcome = "ongoing"
        self.hover = None
        self.player_x = arena.PLAYER_START
        self.rival_x = arena.RIVAL_START
        self.wander = arena.Wander()

    # ----- state changes -------------------------------------------------

    def start_battle(self):
        name = self.typed_name.strip() or "You"
        self.player = Fighter(name=name, hp=START_HP, max_hp=START_HP)
        self.rival = Fighter(name=random.choice(RIVAL_NAMES), hp=START_HP, max_hp=START_HP)
        # The rival is drawn as itself where a drawing exists; the player has no
        # drawing of their own, so they borrow one of the others.
        self.art_names = {PLAYER: pick_player_art(self.rival.name), RIVAL: self.rival.name}
        self.message = "{} vs. {}! Let the fight begin!".format(self.player.name, self.rival.name)
        self.timeline = None
        self.frame = None
        self.elapsed_ms = 0
        self.outcome = "ongoing"
        self.hover = None
        # Both squirrels go back to their marks, so a rematch doesn't start
        # wherever the last fight happened to finish.
        self.player_x = arena.PLAYER_START
        self.rival_x = arena.RIVAL_START
        self.wander = arena.Wander()
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
        rival_move = random.choice(MOVES)
        # resolve_turn() mutates Fighter.hp in place, so snapshot first.
        hp_before = {PLAYER: self.player.hp, RIVAL: self.rival.hp}
        result = resolve_turn(
            self.player, move, self.rival, rival_move,
            band=arena.band(self.player_x, self.rival_x),
        )
        hp_after = {PLAYER: self.player.hp, RIVAL: self.rival.hp}
        self.timeline = build_timeline(
            self.player.name, self.rival.name, move, rival_move, result,
            hp_before, hp_after, self.player.max_hp,
        )
        self.elapsed_ms = 0
        self.frame = sample(self.timeline, 0)
        self.outcome = battle_outcome(self.player, self.rival)
        self.hover = None
        self.state = "animating"

    # ----- per-frame -----------------------------------------------------

    def update(self, dt_ms):
        if self.state == "battle":
            self._walk(dt_ms)
            return
        if self.state != "animating":
            return
        self.elapsed_ms = min(self.elapsed_ms + dt_ms, self.timeline.total_ms)
        self.frame = sample(self.timeline, self.elapsed_ms)
        if self.elapsed_ms >= self.timeline.total_ms:
            self.message = self.frame.caption
            self.state = "result" if self.outcome != "ongoing" else "battle"

    def _walk(self, dt_ms):
        """Move both squirrels while the player is choosing a move.

        Arrow keys are read as held state rather than as KEYDOWN events, because
        walking has to continue for as long as the key is down. The rival ambles
        the whole time too, so the gap keeps changing and the player has to
        commit at a moment when their move will actually reach.
        """
        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1
        if direction:
            self.player_x = arena.walk_player(self.player_x, direction, dt_ms, self.rival_x)
        self.rival_x, self.wander = arena.step_wander(
            self.wander, self.rival_x, self.player_x, dt_ms
        )

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
        # Everything on the stage is drawn relative to the camera, which is just
        # the midpoint between the fighters clamped to the world.
        camera = arena.camera_x(self.player_x, self.rival_x)

        # The arena drawing is a frame — trunks down the sides, leaves above,
        # dirt below — with a see-through middle, so the sky and grass are laid
        # down first and show through it rather than being replaced by it.
        pygame.draw.rect(self.screen, COLOR_SKY,
                         (0, STAGE_TOP, WINDOW_SIZE[0], GROUND_Y - STAGE_TOP))
        pygame.draw.rect(self.screen, COLOR_GRASS,
                         (0, GROUND_Y, WINDOW_SIZE[0], STAGE_BOTTOM - GROUND_Y))
        background = load_background()
        if background is not None:
            # One screen of scenery repeated across a world several screens wide.
            # A tiled frame repeats its edges, which reads as a continuous burrow
            # wall — good enough until there is proper wide scenery to draw.
            tile_width = background.get_width()
            left = int(camera // tile_width) * tile_width
            while left < camera + WINDOW_SIZE[0]:
                self.screen.blit(background, (left - camera, STAGE_TOP))
                left += tile_width
        # Squirrels are drawn after the HP panel, so a big enough hop or a wide
        # rotation would otherwise paint over the HP bars. The effects are tuned
        # to stay inside the stage; this makes that a guarantee rather than a
        # thing to remember every time an effect is added.
        self.screen.set_clip(pygame.Rect(0, STAGE_TOP, WINDOW_SIZE[0], STAGE_BOTTOM - STAGE_TOP))
        self._draw_squirrel(PLAYER, self.player_x - camera)
        self._draw_squirrel(RIVAL, self.rival_x - camera)
        self.screen.set_clip(None)

    def _pose_for(self, actor):
        """Pick a drawing by what the squirrel is currently doing.

        `sprites.load_pose` falls back to `idle` for any pose that has no PNG,
        so this is safe whether or not the extra drawings have been made yet.
        """
        if self.state not in ("animating", "result") or self.timeline is None:
            return "idle"
        active = {
            cue.effect
            for cue in self.timeline.cues
            if cue.actor == actor
            and cue.start_ms <= self.elapsed_ms <= cue.start_ms + cue.duration_ms
        }
        if "stagger" in active or "faint" in active:
            return "hurt"
        if "lunge" in active:
            return "attack"
        return "idle"

    def _draw_squirrel(self, actor, center_x):
        state = self.frame.actors[actor] if self.frame is not None else ActorState()
        image = load_pose(actor, self._pose_for(actor), self.art_names.get(actor))
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
        frozen = self.state != "battle"
        for top, caption, kind in GROUP_LABELS:
            label = self.label_font.render(caption, True, KIND_STYLE[kind]["text"])
            self.screen.blit(label, (24, top))
        for button in self.buttons:
            style = KIND_STYLE[button.move.kind]
            fill, edge, text_color = style["fill"], style["edge"], style["text"]
            # A move that can't reach from here is dimmed but still clickable —
            # choosing it anyway and whiffing is allowed, and funny.
            out_of_range = not arena.reaches(button.move, self.player_x, self.rival_x)
            if frozen or out_of_range:
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

    def _outcome_text(self):
        if self.outcome == "draw":
            return "Both squirrels are down! It's a draw!"
        if self.outcome == "a_wins":
            return "{} wins!".format(self.player.name)
        if self.outcome == "b_wins":
            return "{} wins!".format(self.rival.name)
        return ""

    def _draw_result_overlay(self):
        shade = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        self.screen.blit(shade, (0, 0))

        panel = pygame.Rect(0, 0, 560, 190)
        panel.center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_DIM, panel, width=2, border_radius=12)

        headline = self.title_font.render(self._outcome_text(), True, COLOR_TEXT)
        if headline.get_width() > panel.width - 40:
            headline = self.bold.render(self._outcome_text(), True, COLOR_TEXT)
        self.screen.blit(headline, headline.get_rect(center=(panel.centerx, panel.centery - 28)))

        prompt = self.font.render("Press Enter to play again, or Esc to quit.", True, COLOR_DIM)
        self.screen.blit(prompt, prompt.get_rect(center=(panel.centerx, panel.centery + 36)))


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
