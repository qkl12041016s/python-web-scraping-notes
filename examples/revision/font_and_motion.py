import argparse
from pathlib import Path


def inspect_font(path):
    from fontTools.ttLib import TTFont

    with TTFont(path) as font:
        return font.getBestCmap() or {}


def motion(distance, steps=10, duration=1.0):
    if steps < 1 or duration <= 0:
        raise ValueError("positive steps and duration required")
    return [
        (duration * i / steps,
         distance * (3 * (i / steps) ** 2 - 2 * (i / steps) ** 3))
        for i in range(steps + 1)
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", type=Path)
    args = parser.parse_args()
    # This map belongs to our own synthetic fixture, not an inferred map.
    known_map = {"\ue001": "1", "\ue002": "2"}
    encoded = "\ue001\ue002"
    print("decoded fixture:", "".join(known_map[c] for c in encoded))
    print("local motion:", motion(100)[-1])
    if args.font:
        for codepoint, glyph in sorted(inspect_font(args.font).items())[:8]:
            print(hex(codepoint), glyph)


if __name__ == "__main__":
    main()
