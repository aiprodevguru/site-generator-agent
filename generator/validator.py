"""
Post-generation output validator.

Verifies that all required files exist and are non-empty.
Returns a list of non-critical warnings and raises on critical failures.
"""
from __future__ import annotations

from pathlib import Path

from generator.config import REQUIRED_OUTPUT_FILES
from generator.logger import get_logger

log = get_logger("validator")


def validate_output(batch_dir: Path, game_folders: list[str]) -> list[str]:
    """
    Validate the generated whitepage under *batch_dir*.

    Parameters
    ----------
    batch_dir    : root of the generated batch
    game_folders : list of the two game folder slugs

    Returns
    -------
    list[str]
        Non-critical warnings (empty files, missing optional assets).

    Raises
    ------
    RuntimeError
        If any critical required file is missing.
    """
    warnings: list[str]  = []
    critical: list[str]  = []

    # ── Static required files ──────────────────────────────────────────────────
    for rel in REQUIRED_OUTPUT_FILES:
        path = batch_dir / rel
        if not path.exists():
            critical.append(rel)
        elif path.stat().st_size == 0:
            warnings.append(f"Empty file: {rel}")

    # ── Per-game banner images ─────────────────────────────────────────────────
    for folder in game_folders:
        banner = batch_dir / "games" / folder / "banner.png"
        if not banner.exists():
            warnings.append(f"Missing game banner: games/{folder}/banner.png")

    # ── Game folders exist in games/ ───────────────────────────────────────────
    for folder in game_folders:
        game_path = batch_dir / "games" / folder
        if not game_path.exists():
            critical.append(f"games/{folder}")

    # ── At least some icons ────────────────────────────────────────────────────
    icon_dir = batch_dir / "assets" / "icons"
    icon_count = sum(1 for f in icon_dir.iterdir() if f.suffix in {".png", ".jpg", ".svg"}) \
                 if icon_dir.exists() else 0
    if icon_count == 0:
        warnings.append("No icon images found in assets/icons/")

    # ── Report ─────────────────────────────────────────────────────────────────
    for w in warnings:
        log.warning(f"  ⚠  {w}")

    if critical:
        lines = "\n".join(f"  - {f}" for f in critical)
        msg = f"Validation failed — critical files missing:\n{lines}"
        log.error(msg)
        raise RuntimeError(msg)

    status = "✓" if not warnings else f"✓ ({len(warnings)} warning(s))"
    log.info(f"Validation {status}")
    return warnings
