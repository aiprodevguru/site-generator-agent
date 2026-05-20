"""
File-system layer — directory scaffolding, game folder relocation, and
writing generated content to disk.

All writes are funnelled through this module so path logic stays in one place.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from generator.logger import get_logger

log = get_logger("file_manager")

# Sub-directories that must exist inside every batch root
_SCAFFOLD_DIRS: list[str] = [
    "games",
    "assets/images",
    "assets/icons",
    "partials",
]


def scaffold_directories(batch_dir: Path) -> None:
    """
    Create the required output directory tree under *batch_dir*.

    Safe to call on an already-scaffolded directory — existing folders are
    left untouched.
    """
    for rel in _SCAFFOLD_DIRS:
        target = batch_dir / rel
        target.mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured: {target.relative_to(batch_dir.parent)}")

    log.info(f"Directory scaffold ready under '{batch_dir.name}/'")


def move_game_folders(batch_dir: Path, game_folders: list[str]) -> None:
    """
    Move each *game_folder* from *batch_dir/* into *batch_dir/games/*.

    Already-moved folders (src missing, dst present) are silently skipped so
    re-running the generator is idempotent.

    Raises
    ------
    FileNotFoundError
        If a game folder is missing from both locations.
    """
    games_dir = batch_dir / "games"

    for folder in game_folders:
        src = batch_dir / folder
        dst = games_dir / folder

        if dst.exists():
            log.debug(f"'{folder}' already in games/ — skip move")
            continue

        if not src.exists():
            raise FileNotFoundError(
                f"Game folder not found at '{src}' and not yet in 'games/'."
            )

        log.info(f"Moving  {batch_dir.name}/{folder}  →  games/{folder}")
        shutil.move(str(src), str(dst))


def write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """
    Write *content* to *path*, creating all parent directories as needed.

    Uses UTF-8 by default; BOM-free.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    log.debug(f"Wrote text  : {path.name}  ({len(content):,} chars)")


def write_binary(path: Path, data: bytes) -> None:
    """Write raw *data* to *path*, creating all parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    log.debug(f"Wrote binary: {path.name}  ({len(data):,} bytes)")
