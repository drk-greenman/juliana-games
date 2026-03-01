import os
import random
import anthropic
from dotenv import load_dotenv

load_dotenv()

ADJECTIVES = [
    "slimy", "invisible", "grumpy", "sparkly", "giant", "tiny", "backwards",
    "stinky", "bouncy", "frozen", "sneaky", "wobbly", "electric", "fluffy",
    "melting", "spiky", "glowing", "upside-down", "polka-dotted", "musical",
    "crunchy", "soggy", "exploding", "whispering", "stretchy", "ticklish",
    "purple", "chaotic", "sleepy", "reverse",
]

NOUNS = [
    "wizard", "sandwich", "penguin", "cloud", "sock", "librarian", "volcano",
    "hamster", "robot", "taco", "detective", "snail", "astronaut", "pickle",
    "dragon", "umbrella", "mailbox", "pancake", "cactus", "submarine",
    "broom", "noodle", "captain", "pineapple", "ghost", "toaster", "knight",
    "jellyfish", "professor", "banana",
]

BANNER = r"""
 __        __            _   ____                  _
 \ \      / /__  _ __ __| | / ___|___  _ __ ___   | |__   ___
  \ \ /\ / / _ \| '__/ _` || |   / _ \| '_ ` _ \  | '_ \ / _ \
   \ V  V / (_) | | | (_| || |__| (_) | | | | | | | |_) | (_) |
    \_/\_/ \___/|_|  \__,_| \____\___/|_| |_| |_| |_.__/ \___/

         ~~~  A Word Combo Story Game  ~~~
"""


def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nOops! No API key found.")
        print("Add it to a .env file in this folder:")
        print("  echo 'ANTHROPIC_API_KEY=your-key-here' > .env\n")
        raise SystemExit(1)
    return anthropic.Anthropic(api_key=api_key)


def generate_story(client, adjective, noun, description):
    combo = f"{adjective} {noun}"
    print("\n  --- Your story ---\n")
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=(
            "You are a funny storyteller for kids. "
            "Write very short (3-5 sentences), silly, imaginative stories."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"The thing is called a '{combo}'. "
                    f"Here's what it is: {description}. "
                    "Write a funny short story about it!"
                ),
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print("\n")


def play_round(client):
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    combo = f"{adjective} {noun}"

    print(f"\n  Your combo is:  >>> {combo.upper()} <<<\n")
    description = input(f"  What IS a {combo}? Describe it!\n  > ").strip()

    if not description:
        print("  (No description? Okay, I'll make something up anyway!)")
        description = "something totally mysterious"

    generate_story(client, adjective, noun, description)


def main():
    print(BANNER)
    client = get_client()

    while True:
        play_round(client)
        again = input("  Play again? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            print("\n  Thanks for playing! Bye! :)\n")
            break


if __name__ == "__main__":
    main()
