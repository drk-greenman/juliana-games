import os
import random

from battle import Fighter, resolve_turn, battle_outcome
from moves import MOVES

RIVAL_NAMES = [
    "BIG BUMBOY",
    "Nutsy McGee",
    "Bushy Malone godski",
    "Duchess Acornald",
    "Mr. tickle bum",
    "Chompy Von Nutsalot",
    "lord o Grey Menace",
    "SIR NUTS ALOT",
    "sherlock gnomes",
    "lord acornut",
    "JOHN CENA",
    "ELON MUST",
]

BANNER = r"""
  #################################################
  #                                               #
  #               SQUIRREL FIGHT!                 #
  #                                               #
  #################################################
"""

HP_BAR_WIDTH = 20

COLOR_RESET = "\033[0m"
MOVE_KIND_COLOR = {
    "attack": "\033[91m",
    "defense": "\033[96m",
    "heal": "\033[92m",
}


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def hp_bar(fighter: Fighter) -> str:
    filled = round((fighter.hp / fighter.max_hp) * HP_BAR_WIDTH)
    filled = max(0, min(HP_BAR_WIDTH, filled))
    bar = "#" * filled + "-" * (HP_BAR_WIDTH - filled)
    return f"[{bar}] {fighter.hp}/{fighter.max_hp}"


def print_status(player: Fighter, computer: Fighter) -> None:
    print(f"\n  {player.name:<20} {hp_bar(player)}")
    print(f"  {computer.name:<20} {hp_bar(computer)}\n")


def print_header(player: Fighter, computer: Fighter) -> None:
    print(f"  🐿️  SQUIRREL FIGHT — {player.name} vs. {computer.name}")


def print_move_details() -> None:
    color = MOVE_KIND_COLOR["attack"]
    print(f"  {color}Attacks:{COLOR_RESET}")
    for i, move in enumerate(MOVES[:7], start=1):
        print(f"  {color}  {i}) {move.name} - {move.description}{COLOR_RESET}")
    color = MOVE_KIND_COLOR["defense"]
    print(f"  {color}Defenses:{COLOR_RESET}")
    for i, move in enumerate(MOVES[7:11], start=8):
        print(f"  {color}  {i}) {move.name} - {move.description}{COLOR_RESET}")
    color = MOVE_KIND_COLOR["heal"]
    print(f"  {color}Heal:{COLOR_RESET}")
    for i, move in enumerate(MOVES[11:], start=12):
        print(f"  {color}  {i}) {move.name} - {move.description}{COLOR_RESET}")


def _print_move_row_group(entries: list[str], color: str, row_size: int) -> None:
    for i in range(0, len(entries), row_size):
        row = entries[i:i + row_size]
        print(f"  {color}  " + "   ".join(row) + COLOR_RESET)


def print_menu_compact() -> None:
    color = MOVE_KIND_COLOR["attack"]
    print(f"  {color}Attacks:{COLOR_RESET}")
    entries = [f"{i}) {move.name}" for i, move in enumerate(MOVES[:7], start=1)]
    _print_move_row_group(entries, color, row_size=3)

    color = MOVE_KIND_COLOR["defense"]
    print(f"  {color}Defenses:{COLOR_RESET}")
    entries = [f"{i}) {move.name}" for i, move in enumerate(MOVES[7:11], start=8)]
    _print_move_row_group(entries, color, row_size=4)

    color = MOVE_KIND_COLOR["heal"]
    print(f"  {color}Heal:{COLOR_RESET}")
    entries = [f"{i}) {move.name}" for i, move in enumerate(MOVES[11:], start=12)]
    _print_move_row_group(entries, color, row_size=4)


def prompt_move(fighter_name: str):
    while True:
        choice = input(f"  {fighter_name}, pick a move (1-12, or ? for move details): ").strip()
        if choice == "?":
            print()
            print_move_details()
            print()
            continue
        if choice.isascii() and choice.isdigit() and 1 <= int(choice) <= len(MOVES):
            return MOVES[int(choice) - 1]
        print("  Not a valid move, try again.")


def computer_choose_move():
    return random.choice(MOVES)


def format_turn_result_lines(player: Fighter, computer: Fighter, player_move, computer_move, result) -> list[str]:
    lines = [
        f"  {player.name} uses {result.fighter_a.move_name}!",
        f"  {computer.name} uses {result.fighter_b.move_name}!",
    ]
    if result.flavor_text:
        lines.append(f"  {result.flavor_text}")
    if result.fighter_b.dodged:
        lines.append(f"  {computer.name} dodges out of the way!")
    if result.fighter_a.damage_dealt:
        lines.append(f"  {player.name} hits {computer.name} for {result.fighter_a.damage_dealt} damage!")
    elif player_move.kind == "attack" and (computer_move.block_reduction is not None or computer_move.block_flat is not None):
        lines.append(f"  {computer.name} fully blocks the attack!")
    if result.fighter_a.dodged:
        lines.append(f"  {player.name} dodges out of the way!")
    if result.fighter_b.damage_dealt:
        lines.append(f"  {computer.name} hits {player.name} for {result.fighter_b.damage_dealt} damage!")
    elif computer_move.kind == "attack" and (player_move.block_reduction is not None or player_move.block_flat is not None):
        lines.append(f"  {player.name} fully blocks the attack!")
    if result.fighter_a.healed:
        lines.append(f"  {player.name} heals {result.fighter_a.healed} HP!")
    if result.fighter_b.healed:
        lines.append(f"  {computer.name} heals {result.fighter_b.healed} HP!")
    return lines


def play_battle() -> None:
    name = input("  Name your squirrel: ").strip() or "You"
    player = Fighter(name=name, hp=60, max_hp=60)
    computer = Fighter(name=random.choice(RIVAL_NAMES), hp=60, max_hp=60)

    recap_lines = [f"  {player.name} vs. {computer.name}! Let the fight begin!"]

    while True:
        # Beat 1: recap of the last turn (or the intro line, on turn 1)
        clear_screen()
        print_header(player, computer)
        print_status(player, computer)
        for line in recap_lines:
            print(line)
        print()

        outcome = battle_outcome(player, computer)
        if outcome != "ongoing":
            if outcome == "draw":
                print("  Both squirrels are down! It's a draw!\n")
            elif outcome == "a_wins":
                print(f"  {player.name} wins!\n")
            elif outcome == "b_wins":
                print(f"  {computer.name} wins!\n")
            break

        input("  Press Enter to continue...")

        # Beat 2: the move menu
        clear_screen()
        print_header(player, computer)
        print_status(player, computer)
        print("  " + "-" * 45)
        print_menu_compact()
        print()

        player_move = prompt_move(player.name)
        computer_move = computer_choose_move()
        result = resolve_turn(player, player_move, computer, computer_move)
        recap_lines = format_turn_result_lines(player, computer, player_move, computer_move, result)


def main() -> None:
    print(BANNER)
    while True:
        play_battle()
        again = input("  Play again? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            print("\n  Thanks for playing! Bye! :)\n")
            break


if __name__ == "__main__":
    main()
