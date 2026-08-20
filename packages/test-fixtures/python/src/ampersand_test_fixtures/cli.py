from __future__ import annotations

import argparse
from pathlib import Path

from ampersand_contracts import FixturePartition

from .audio import generate_spoken_word_fixture
from .corpus import generate_fixture_corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a rights-clear deterministic Ampersand audio fixture.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--duration", type=float, default=6.0, help="Fixture duration in seconds (default: 6).")
    args = parser.parse_args()
    generate_spoken_word_fixture(args.output, duration_seconds=args.duration)
    print(args.output)
    return 0


def corpus_main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a versioned, rights-clear Ampersand synthetic fixture corpus."
    )
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--partition",
        action="append",
        choices=tuple(partition.value for partition in FixturePartition),
        help="Partition to generate; repeat for multiple partitions (default: development + validation).",
    )
    parser.add_argument(
        "--fixture",
        action="append",
        default=[],
        help="Generate one fixture ID (and its parent); repeat to select multiple fixtures.",
    )
    parser.add_argument(
        "--include-long-form",
        action="store_true",
        help="Include the optional one-hour durability fixture.",
    )
    args = parser.parse_args()
    partitions = (
        tuple(FixturePartition(value) for value in args.partition)
        if args.partition
        else (FixturePartition.DEVELOPMENT, FixturePartition.VALIDATION)
    )
    corpus = generate_fixture_corpus(
        args.output,
        partitions=partitions,
        include_long_form=args.include_long_form,
        fixture_ids=tuple(args.fixture),
    )
    print(f"{args.output} ({len(corpus.fixtures)} fixtures, corpus {corpus.corpus_version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
