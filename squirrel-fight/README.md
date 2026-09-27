# Squirrel Fight

A 1v1 squirrel duel. Name your squirrel, pick from 12 silly attack/defense/heal
moves each turn, and battle a randomly-named rival squirrel controlled by the
computer.

There are two ways to play the same fight.

## Play in the terminal

No extra installs, works anywhere:

```bash
python3 squirrel-fight/game.py
```

## Play in a window

Squirrels that lunge, stagger and flash, with clickable moves:

```bash
python3 -m pip install -r squirrel-fight/requirements.txt
python3 squirrel-fight/visual_game.py
```

Click a move, or use the number row — `1`–`9` for the first nine moves, then
`0`, `-` and `=` for moves 10, 11 and 12. Esc quits.

**Walk your squirrel** with the left and right arrow keys (or `A` and `D`) while
you're choosing a move. The rival wanders about on its own the whole time, so the
gap between you keeps changing.

Where you're standing decides what connects:

| Moves | Only work |
| --- | --- |
| Tail Smack, Cheek Barrel, Scratch, Steal | up close |
| Acorn Blast, Chirp, Chirp Insanely | at middle distance |
| Dance, Moonwalk, Scurry, Flex, Eat Garden | anywhere |

Back off too far and even an acorn drops short, so there's a middle distance worth
holding rather than just running away.

The world is three screens wide and scrolls as you walk. Neither squirrel can get more
than about a screen from the other, so you'll sometimes walk into a soft stop until the
rival's wandering gives you more rope — the two of you roam the world together rather
than either one touring it alone.

A move that can't reach is dimmed — you can still pick it, but it whiffs for no
damage. The rival wanders at random rather than cleverly, so it does this to
itself all the time.

Walking is a window-version feature. The terminal version plays as it always
has, with every move always reaching.

Neither version needs an API key. Both are fully offline.

## Drawing your own squirrels

Drop PNG files into `squirrel-fight/assets/` and they show up next run — no code
changes needed. Any squirrel you haven't drawn yet uses a simple code-drawn
placeholder, so the game always works and just gets better one drawing at a time.

**Give each rival its own drawing** by naming the file after them, in lowercase
with dashes instead of spaces. The name has to match one in `RIVAL_NAMES` in
`game.py`, or that squirrel will never turn up to fight:

| Rival in `game.py` | Draw this file |
| --- | --- |
| `JOHN CENA` | `assets/john-cena.png` |
| `BIG BUMBOY` | `assets/big-bumboy.png` |
| `sherlock gnomes` | `assets/sherlock-gnomes.png` |

Draw them **facing left**, on a see-through background. Both styles work, and
each is handled the way it wants to be:

- **Small pixel art** (32×32 and up to 48 tall) is blown up 8×, keeping every
  pixel sharp and square.
- **Bigger freehand drawings** are resized to stand about as tall as everyone
  else, keeping their soft edges.

So a pixel squirrel and a hand-drawn one end up roughly the same size on the
stage and can fight each other quite happily.

The player's squirrel borrows one of the rivals' drawings each battle, picking
one that isn't in the fight, so you never face your own twin.

These are all optional, and each one replaces a placeholder:

| File | When it shows |
| --- | --- |
| `john-cena_hurt.png` | While that squirrel is getting hit |
| `john-cena_attack.png` | While that squirrel is lunging |
| `player_idle.png`, `rival_idle.png` | Any squirrel with no drawing of its own |

## Drawing your own terrain

The arena is one file, `assets/background.png`, and it shows up next run — same as the
squirrels. Start from `source-art/background-template.png`, which is already the right
shape and has the ground marked.

Three things that catch people out:

- **Paint see-through bits pure white** (`#FFFFFF`), *not* transparent. Backgrounds are
  loaded without an alpha channel, so genuinely transparent pixels come out **black**.
  White drops out and lets the game's own sky and grass show through. (Squirrel drawings
  are the opposite — those do want real transparency.)
- **Draw it 4:1.** It gets stretched to 960×240, so a 4:1 image keeps its pixels square.
  The template is 240×60. The older `background.png` is 64×36, which is why its blocks
  look wide and squashed.
- **The ground is near the bottom.** In the 240×60 template the ground line is row 56 and
  the squirrels' feet land on row 58 — marked with a dotted line. Paint over the dots;
  they're only a guide.

Any size works — it's scaled with nearest-neighbour, so pixel art stays sharp.

The world is three screens wide, so your background is **tiled** across it — the same
picture repeated three times. Something with no strong left or right edge tiles best.
(Several different scenes, painted to the full world width, is the next thing planned.)

## The borrowed squirrels

Seven rivals — Nutsy McGee, Mr. tickle bum, Chompy Von Nutsalot, lord o Grey
Menace, SIR NUTS ALOT, lord acornut and ELON MUST — aren't hand-drawn. They all
come from one free squirrel someone else made: a CC0 (public domain) run cycle by
alizard, kept in `source-art/` with its credits.

`make_sprites.py` takes that one squirrel, makes its white background
see-through, picks three frames of the run to stand in for idle/attack/hurt, and
repaints the fur a different colour per rival:

```bash
python3 squirrel-fight/make_sprites.py
```

Edit the colours in `SQUIRREL_COLORS` and run it again to recolour the lot. It
only writes the files it generates, so hand-drawn squirrels are never clobbered.

They're on all fours, so they look a bit lower and longer than the ones Juliana
drew standing up — which is fine, they're squirrels. Replacing any of them is
just a matter of dropping your own `<name>.png` in `assets/` and deleting that
squirrel's line from `SQUIRREL_COLORS`.
| `background.png` | The arena, behind the fight |

The background is drawn as a frame over the sky and grass, so anything you leave
**pure white** in it becomes see-through and the sky shows through the gap.

## Run the tests

```bash
python3 -m pytest squirrel-fight/
```

`test_battle.py` covers the fight maths, `test_choreography.py` covers the
animation timeline, and `test_sprites.py` covers turning a rival's name into a
filename. The pygame drawing code has no tests — like `game.py`, it's checked by
playing it.

## How the code is split

| File | What it does |
| --- | --- |
| `moves.py` | The 12 moves, as data |
| `battle.py` | Turn resolution. Pure logic, no input or output |
| `game.py` | The terminal version |
| `visual_game.py` | The window version |
| `choreography.py` | Turns a resolved turn into animation. Pure, no pygame |
| `sprites.py` | Loads drawings, falls back to code-drawn squirrels |
