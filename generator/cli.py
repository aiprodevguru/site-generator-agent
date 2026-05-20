"""
CLI argument parser.

Keeps argparse setup separate from business logic so that ``main.py`` stays
clean and the parser can be tested independently.
"""
from __future__ import annotations

import argparse
import sys
from typing import Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_whitepage",
        description=(
            "Generate a production-quality PHP whitepage for a batch of two local games."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python generate_whitepage.py --batch dragon-arena
  python generate_whitepage.py --batch space-duo --topic sci-fi --tone dark
  python generate_whitepage.py --batch fun-pack  --topic colorful --container_opacity 0.08

topics  : fantasy | sci-fi | battle | legend | sports | horror | adventure | colorful
tones   : dark | fierce | warm | colorful | horror
        """,
    )

    parser.add_argument(
        "--batch",
        required=True,
        metavar="NAME",
        help=(
            "Batch folder name that already exists under the htdocs root "
            "(e.g. 'dragon-arena').  Must contain exactly two game sub-directories."
        ),
    )
    parser.add_argument(
        "--topic",
        default=None,
        metavar="TOPIC",
        help="Content theme.  Inferred from game folder names when omitted.",
    )
    parser.add_argument(
        "--tone",
        default=None,
        metavar="TONE",
        help="Visual and copy tone.  Inferred from game folder names when omitted.",
    )
    parser.add_argument(
        "--container_opacity",
        type=float,
        default=None,
        metavar="FLOAT",
        help="Card container background opacity, 0.0–1.0  (default: 0.05).",
    )

    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse and validate CLI arguments.  Exits with a message on invalid input."""
    parser = build_parser()
    args   = parser.parse_args(argv)

    if args.container_opacity is not None:
        if not 0.0 <= args.container_opacity <= 1.0:
            parser.error("--container_opacity must be between 0.0 and 1.0")

    # Normalise strings
    if args.topic:
        args.topic = args.topic.strip().lower()
    if args.tone:
        args.tone = args.tone.strip().lower()
    args.batch = args.batch.strip()

    return args
