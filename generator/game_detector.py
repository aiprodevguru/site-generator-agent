"""
Detects and normalises the two game folders inside a batch directory.

The detector deliberately ignores infrastructure folders (games/, assets/,
partials/) so that re-running the generator on an already-scaffolded batch
works correctly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from generator.logger import get_logger
from generator.utils import folder_to_title

log = get_logger("game_detector")

# Folders created by the scaffold step — not games
_SCAFFOLD_DIRS = frozenset({"games", "assets", "partials"})


@dataclass
class GameInfo:
    """Immutable record describing a single detected game."""

    folder:       str   # original folder slug, e.g. 'dragon-quest'
    display_name: str   # pretty title,          e.g. 'Dragon Quest'
    banner_image: str   # relative web path,     e.g. 'games/dragon-quest/banner.png'
    description:  str = field(default="")   # filled in later by ai_text


def detect_games(batch_dir: Path) -> tuple[GameInfo, GameInfo]:
    """
    Scan *batch_dir* for exactly two immediate sub-directories that are not
    part of the generator's own scaffold.

    Returns
    -------
    tuple[GameInfo, GameInfo]
        The two games in alphabetical order by folder name.

    Raises
    ------
    FileNotFoundError
        If *batch_dir* does not exist on disk.
    ValueError
        If the number of qualifying sub-directories is not exactly 2.
    """
    if not batch_dir.exists():
        raise FileNotFoundError(
            f"Batch directory does not exist: {batch_dir}\n"
            f"Create it under your htdocs root and add two game sub-folders."
        )
    if not batch_dir.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {batch_dir}")

    candidates: list[str] = sorted(
        d.name
        for d in batch_dir.iterdir()
        if d.is_dir()
        and d.name not in _SCAFFOLD_DIRS
        and not d.name.startswith(".")
    )

    if len(candidates) != 2:
        detail = f"found {len(candidates)}: {candidates}" if candidates else "found none"
        raise ValueError(
            f"Expected exactly 2 game folders in '{batch_dir.name}/', {detail}.\n"
            f"Make sure the batch contains two game directories and no extra folders."
        )

    log.info(f"Detected games: {candidates[0]}  +  {candidates[1]}")

    games = [
        GameInfo(
            folder       = folder,
            display_name = folder_to_title(folder),
            banner_image = f"games/{folder}/banner.png",
        )
        for folder in candidates
    ]
    return games[0], games[1]
