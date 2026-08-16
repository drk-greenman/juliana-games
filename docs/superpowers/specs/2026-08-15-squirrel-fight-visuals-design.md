# Squirrel Fight — Visual (pygame) Version

Adds a graphical version of Squirrel Fight: a pygame window showing two squirrel
drawings that lunge, stagger, flash and heal as a turn resolves, with clickable move
buttons and animated HP bars. The existing terminal game (`squirrel-fight/game.py`)
is untouched and keeps working; the new window is a second way to play the same
fight. `battle.py` and `moves.py` — the fight rules and move data — are shared
verbatim and not modified, so the two versions can never disagree about how a
battle works.

The artwork is hand-drawn by Juliana and arrives over time. The design therefore
treats every image as optional: any drawing that is missing is replaced by a
code-drawn placeholder squirrel, so the game is fully playable before a single PNG
exists and improves one file at a time.

## Decisions this design rests on

- **pygame window**, not terminal art and not a web page. Real image files and real
  motion are the point.
- **Motion comes from code, not from frames.** One drawing per squirrel is moved,
  rotated and tinted by the game. This is the option that looks the most alive for
  the least drawing. It does not preclude frame-by-frame animation later: poses are
  looked up by name, so extra drawings can be added without changing the animation
  engine.
- **Both versions, same folder.** `visual_game.py` sits beside `game.py` so both
  import `battle.py` and `moves.py` with no `sys.path` manipulation and no
  duplicated rules.
- **Engine first, art drops in.** Build order matches the code layers, so no step is
  rewritten by a later one, and no step is blocked waiting on a drawing.

## File layout

```
squirrel-fight/
  moves.py               unchanged
  battle.py              unchanged
  game.py                unchanged  (terminal version)
  test_battle.py         unchanged
  visual_game.py         NEW  pygame window: main loop, input, drawing
  choreography.py        NEW  pure: TurnResult -> animation timeline
  sprites.py             NEW  asset loading with code-drawn fallback
  test_choreography.py   NEW
  assets/                NEW  hand-drawn PNGs
  requirements.txt       NEW  pygame
```

`pygame` goes in a project-level `requirements.txt` rather than the root one.
`CLAUDE.md` already names pygame as the case for splitting dependencies, and this
keeps `word-combo-story` from inheriting a graphics library it does not use. The
root `requirements.txt` is unchanged.

## `choreography.py` — turning a turn into motion

`choreography.py` is to animation what `game.py`'s existing
`format_turn_result_lines()` is to text: both take the `TurnResult` returned by
`resolve_turn()` and turn it into presentation. One produces lines of text, the
other produces a timeline. It imports no pygame, which keeps it pure, testable, and
independent of how anything is drawn.

```python
@dataclass(frozen=True)
class Cue:
    start_ms: int
    duration_ms: int
    actor: str      # "player" | "rival"
    effect: str     # "lunge" | "stagger" | "flash" | "hop" | "brace" | "glow" | "faint"

@dataclass(frozen=True)
class ActorState:
    offset_x: float = 0.0
    offset_y: float = 0.0
    rotation: float = 0.0
    scale: float = 1.0
    tint: float = 0.0        # 0.0 = normal, 1.0 = fully flashed

@dataclass(frozen=True)
class HpTween:
    actor: str
    start_ms: int
    duration_ms: int
    hp_from: int
    hp_to: int

@dataclass(frozen=True)
class Timeline:
    cues: list[Cue]
    captions: list[tuple[int, str]]   # (start_ms, text) for the message strip
    hp_tweens: list[HpTween]
    total_ms: int

@dataclass(frozen=True)
class FrameState:
    actors: dict[str, ActorState]     # keyed "player" / "rival"
    hp: dict[str, int]                # keyed the same; already rounded for display
    caption: str                      # the most recent caption at or before t_ms
```

Two functions make up the interface:

```python
build_timeline(
    player_name: str, rival_name: str,
    player_move: Move, rival_move: Move,
    result: TurnResult,
    hp_before: dict[str, int],        # {"player": 42, "rival": 36}
) -> Timeline

sample(timeline: Timeline, t_ms: int) -> FrameState
```

`sample()` is pure math over the cues active at `t_ms`, and returns everything a
frame needs in one call — actor transforms, current HP-bar values, and the caption
to show. Overlapping cues on the same actor compose: a `stagger` and a `flash` at
once produce both the displacement and the tint.

### Which outcome produces which cues

| Situation | Cues |
| --- | --- |
| Attack lands | attacker `lunge`, defender `stagger` + `flash` |
| Attack fully blocked | attacker `lunge`, defender `brace` (no `flash`) |
| Attack dodged | attacker `lunge`, defender `hop` |
| Heal (`Eat Garden`) | healer `glow` |
| Lifesteal (`Steal`) | attacker `lunge` + `glow`, defender `stagger` + `flash` |
| Both defending | both `brace`, plus the existing flavor-text caption |
| Fighter reaches 0 HP | that fighter `faint` (topple and fade) |

The player's action plays first, then the rival's — roughly 700 ms each, about
1.6 s per turn. `battle.py` resolves both moves simultaneously, but narrating them
in sequence reads better and matches the order `format_turn_result_lines()` already
uses. Captions are emitted alongside the cues so the message strip narrates the same
beats the terminal version prints.

### HP snapshot

`resolve_turn()` mutates `Fighter.hp` in place. `visual_game.py` must therefore
record both fighters' HP *before* calling it and pass those values in as `hp_before`.
The timeline tweens each bar from the old value to the already-final new one. The
animation never re-simulates the fight — it only visualises a result that has
already been computed.

## `sprites.py` — art loading and fallback

One function is the whole interface:

```python
load_pose(actor: str, pose: str) -> pygame.Surface
```

It looks for `assets/{actor}_{pose}.png`. If the file is missing, unreadable, or
fails to decode, it returns a code-drawn placeholder squirrel instead — an ellipse
body, a circle head, and a curved tail, drawn with pygame primitives and tinted
differently for player and rival so the two are distinguishable. Results are cached
so the fallback is not redrawn every frame.

Poses are requested by name, and any pose that has no file falls back to `idle`
before falling back to the placeholder. This is what lets extra drawings be added
later with no code change.

### Asset brief

Day one needs two files:

- `assets/player_idle.png`
- `assets/rival_idle.png`

Format: PNG, transparent background, roughly 200×200, squirrel facing right. The
rival is flipped horizontally in code, so both drawings face the same way.

Everything below is optional, and each file simply displaces a fallback when it
appears:

- `player_hurt.png`, `rival_hurt.png` — shown during `stagger`
- `player_attack.png`, `rival_attack.png` — shown during `lunge`
- `background.png` — replaces the drawn sky-and-grass backdrop
- `acorn.png` — a projectile for `Acorn Blast` (step 4)

## `visual_game.py` — the window

960 × 640, one window, three screens.

**Title screen.** Asks for the player's squirrel name via a simple text field. An
empty name becomes `"You"`, matching the terminal game. Enter starts the fight
against a rival drawn at random from `game.py`'s existing `RIVAL_NAMES`.

**Battle screen**, top to bottom:

1. Both fighters' names, HP bars, and numeric HP
2. The battle stage — backdrop, both squirrels facing each other
3. A one-line message strip
4. All 12 moves as buttons, grouped and coloured by kind

Move buttons reuse the terminal version's colour scheme — attacks red, defenses
cyan, heal green — so the two versions read as the same game. Hovering a move shows
its `description` in the message strip; this replaces the terminal version's `?`
command, making descriptions always one hover away rather than a separate screen.
Number keys 1–12 work as shortcuts for the corresponding move. Esc quits.

Choosing a move resolves the turn immediately, then plays the resulting timeline.
During playback the buttons are greyed out and ignore input, and the message strip
shows each caption as its time arrives. There is no "press Enter to continue" — the
animation is the pause. When the timeline finishes, the buttons re-enable, unless
the battle is over.

**Result screen.** Shown when `battle_outcome()` returns anything other than
`"ongoing"`: the win/lose/draw line and a *Play again?* choice that either starts a
fresh battle or closes the window.

The main loop runs at a fixed 60 FPS via `pygame.time.Clock`, and animation is driven
by elapsed milliseconds rather than frame counts, so a slow frame stretches nothing.

## Error handling

- **Missing, unreadable, or corrupt image** — falls back to the code-drawn
  placeholder. Never fatal; no error text on screen.
- **pygame not installed** — `visual_game.py` catches the `ImportError`, prints
  `pip install -r squirrel-fight/requirements.txt`, and exits. This mirrors the
  pattern `word-combo-story/game.py`'s `get_client()` uses for a missing API key,
  as `CLAUDE.md` prescribes.
- **Window closed mid-battle** — the `pygame.QUIT` event exits cleanly with no
  traceback.
- **Empty name at the title screen** — becomes `"You"`.
- **No display available** (e.g. running over plain SSH) — `pygame.display.set_mode()`
  raises `pygame.error`; catch it, print that the terminal version is available at
  `python squirrel-fight/game.py`, and exit.

## Testing

`test_choreography.py` covers the pure timeline layer:

- At `t_ms == 0`, every actor's state is the neutral `ActorState()`
- A dodged attack produces a `hop` cue and no `flash`
- A fully blocked attack produces a `brace` cue and no `flash`
- A landed attack produces `stagger` and `flash` on the defender
- `Steal` produces both a `flash` on the defender and a `glow` on the attacker
- `timeline.total_ms` is at least `max(start_ms + duration_ms)` across all cues
- Captions are ordered by `start_ms`, and `sample()` returns the most recent one
- Sampling at `t_ms >= total_ms` reports each fighter's exact post-turn HP

`sprites.py` and `visual_game.py` are not tested, consistent with how `game.py` is
treated today: this repo tests logic, not I/O. `test_battle.py` is unchanged and
still passes. Both test files run with `pytest squirrel-fight/`.

## Build order

Each step ends with a game that runs.

1. **Playable window** — `visual_game.py`, `requirements.txt`, and a minimal
   inline placeholder squirrel. HP bars, message strip, clickable and keyboard-
   selectable moves, and all three screens (title, battle, result), with turns
   resolving instantly and no animation. A complete fight, start to rematch, is
   playable in a window.
2. **Art loads** — `sprites.py` and `assets/`. Dropping `player_idle.png` and
   `rival_idle.png` into `assets/` makes them appear; without them nothing changes.
3. **Motion** — `choreography.py` and `test_choreography.py`, wired into the main
   loop. Lunge, stagger, flash, hop, brace, glow, faint, and tweened HP bars.
4. **Polish** — result screen refinements, `hurt`/`attack` poses if drawn, a flying
   acorn for `Acorn Blast`, and a hand-drawn background.

`squirrel-fight/README.md` gains a section on the second way to run the game and on
where to put drawings. The root `README.md` already links `squirrel-fight/` and needs
no change.

## Explicitly out of scope

- Sound effects and music
- Two-player or networked play
- Any change to `battle.py` or `moves.py`, or to their test file
- Any change to the terminal `game.py` beyond leaving it alone
- Frame-by-frame flipbook animation — considered and deferred; the pose-by-name
  lookup in `sprites.py` is the hook that makes it addable later
- Packaging into a double-clickable application
- Sourcing art from anywhere other than Juliana's own drawings
