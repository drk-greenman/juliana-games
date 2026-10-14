"""Builds the double-clickable Squirrel Fight.app for the Desktop.

Turns `assets/app-icon.png` — a drawing, same as everything else in `assets/` —
into a Mac app icon, and wraps the game in a bundle you can keep on the Desktop.
Playing then means double-clicking a squirrel instead of typing a python command.

    python3 squirrel-fight/make_app.py          # plays from this checkout
    python3 squirrel-fight/make_app.py ../juliana-games-play/squirrel-fight

Redraw `assets/app-icon.png` and run this again to change the icon.

Four things about Mac bundles that cost time if you don't know them, all handled
here:

- **The icon must be an `.icns`**, built by `iconutil` from a folder of PNGs at
  fixed sizes. It and `sips` ship with macOS, so this needs nothing installed.
- **The bundle is ad-hoc code-signed**, and editing any file inside a signed
  bundle breaks the seal — macOS then refuses to open it as "damaged". So this
  rebuilds the whole bundle and re-signs it, rather than dropping a fresh icon
  into the old one.
- **Finder caches icons** per bundle, so a rebuilt app can go on showing the old
  picture. Touching the bundle at the end is what makes the new one appear.
- **The app gets no Terminal**, so anything the game prints — including the
  traceback if it won't start — would vanish. The launcher keeps a log instead,
  at `~/Library/Logs/squirrel-fight.log`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

HERE = Path(__file__).parent
ICON_SOURCE = HERE / "assets" / "app-icon.png"

APP_NAME = "Squirrel Fight"
DESKTOP = Path.home() / "Desktop"
BUNDLE_ID = "local.juliana.squirrelfight"

# The sizes an .icns holds. Each is also needed at @2x for retina screens, so
# the biggest picture actually built is 1024.
ICON_SIZES = (16, 32, 128, 256, 512)

LOG_PATH = "$HOME/Library/Logs/squirrel-fight.log"

LAUNCHER = """#!/bin/bash
# Launches Squirrel Fight with no Terminal attached, so everything it prints
# goes to the log. Rebuild with make_app.py if the game moves somewhere else.
LOG="{log}"
mkdir -p "$(dirname "$LOG")"
{{
  echo "=== launched $(date) ==="
  cd {game_dir} || exit 1
  exec {python} visual_game.py
}} >>"$LOG" 2>&1
"""

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>CFBundleName</key><string>{name}</string>
\t<key>CFBundleDisplayName</key><string>{name}</string>
\t<key>CFBundleIdentifier</key><string>{bundle_id}</string>
\t<key>CFBundleVersion</key><string>1.0</string>
\t<key>CFBundleShortVersionString</key><string>1.0</string>
\t<key>CFBundlePackageType</key><string>APPL</string>
\t<key>CFBundleExecutable</key><string>run</string>
\t<key>CFBundleIconFile</key><string>app</string>
\t<key>LSApplicationCategoryType</key><string>public.app-category.games</string>
\t<key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
"""


def squared(icon: pygame.Surface) -> pygame.Surface:
    """Centre a drawing on a square canvas, since Mac icons are square.

    A tall drawing used as-is would be squashed. Padding instead leaves it the
    shape it was drawn, with see-through space either side.
    """
    width, height = icon.get_size()
    if width == height:
        return icon
    side = max(width, height)
    canvas = pygame.Surface((side, side), pygame.SRCALPHA)
    canvas.blit(icon, ((side - width) // 2, (side - height) // 2))
    return canvas


def resized(icon: pygame.Surface, size: int) -> pygame.Surface:
    """Blow pixel art up without blurring it, but shrink it smoothly.

    Scaling up with nearest-neighbour keeps a drawn pixel a crisp square — the
    same reasoning as `sprites.PIXEL_SCALE`. Shrinking that way drops whole rows
    and comes out speckled, so the small sizes are sampled smoothly instead; at
    16 pixels across nobody can make out an individual pixel anyway.
    """
    if size >= icon.get_width():
        return pygame.transform.scale(icon, (size, size))
    return pygame.transform.smoothscale(icon, (size, size))


def build_icns(icon: pygame.Surface, destination: Path, workspace: Path) -> None:
    """Write the drawing out at every size `iconutil` wants, and convert it."""
    iconset = workspace / "app.iconset"
    iconset.mkdir()
    for size in ICON_SIZES:
        pygame.image.save(resized(icon, size), str(iconset / "icon_{0}x{0}.png".format(size)))
        pygame.image.save(
            resized(icon, size * 2), str(iconset / "icon_{0}x{0}@2x.png".format(size))
        )
    subprocess.run(
        ["iconutil", "--convert", "icns", str(iconset), "--output", str(destination)],
        check=True,
    )


def build_bundle(game_dir: Path, icon: pygame.Surface, workspace: Path) -> Path:
    """Assemble the .app in a scratch folder, so a failure leaves the old one."""
    bundle = workspace / (APP_NAME + ".app")
    macos = bundle / "Contents" / "MacOS"
    resources = bundle / "Contents" / "Resources"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)

    (bundle / "Contents" / "Info.plist").write_text(
        INFO_PLIST.format(name=APP_NAME, bundle_id=BUNDLE_ID)
    )

    launcher = macos / "run"
    launcher.write_text(
        LAUNCHER.format(
            log=LOG_PATH,
            # Quoted because these are real paths on someone's Mac, and a folder
            # called "juliana games" would otherwise split into two words.
            game_dir='"{}"'.format(game_dir),
            python='"{}"'.format(sys.executable),
        )
    )
    launcher.chmod(0o755)

    build_icns(icon, resources / "app.icns", workspace)
    return bundle


def install(bundle: Path, destination: Path) -> None:
    """Swap the new bundle in, then sign it and nudge Finder to look again."""
    if destination.exists():
        shutil.rmtree(destination)
    shutil.move(str(bundle), str(destination))
    # Ad-hoc signing, which is what an app nobody paid Apple for gets. Must come
    # after the move: the signature seals the files as they finally sit.
    subprocess.run(["codesign", "--force", "--sign", "-", str(destination)], check=True)
    subprocess.run(["touch", str(destination)], check=True)


def main() -> None:
    game_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.resolve()
    if not (game_dir / "visual_game.py").is_file():
        raise SystemExit("No visual_game.py in {} — is that the right folder?".format(game_dir))
    if not ICON_SOURCE.is_file():
        raise SystemExit(
            "No icon to build from.\n"
            "Draw a square picture, save it as {}, and run this again.".format(ICON_SOURCE)
        )

    pygame.init()
    pygame.display.set_mode((1, 1))
    icon = squared(pygame.image.load(str(ICON_SOURCE)).convert_alpha())

    destination = DESKTOP / (APP_NAME + ".app")
    with tempfile.TemporaryDirectory() as scratch:
        install(build_bundle(game_dir, icon, Path(scratch)), destination)

    print("Built {}".format(destination))
    print("  icon  {} at {}x{}".format(ICON_SOURCE.name, *icon.get_size()))
    print("  plays {}".format(game_dir))


if __name__ == "__main__":
    main()
