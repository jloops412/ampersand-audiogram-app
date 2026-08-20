from __future__ import annotations

import argparse
from pathlib import Path

from .audio import generate_spoken_word_fixture


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a rights-clear deterministic Ampersand audio fixture.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--duration", type=float, default=6.0, help="Fixture duration in seconds (default: 6).")
    args = parser.parse_args()
    generate_spoken_word_fixture(args.output, duration_seconds=args.duration)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
