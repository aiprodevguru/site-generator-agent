#!/usr/bin/env python3
"""
Entry point for the whitepage generator.

Usage:
    python generate_whitepage.py --batch <batch_name>
    python generate_whitepage.py --batch dragon-arena --topic fantasy --tone dark
    python generate_whitepage.py --batch space-duo --container_opacity 0.08

The batch folder must exist under C:\\xampp\\htdocs\\ and contain exactly
two game sub-directories.
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `generator` is importable
# regardless of the working directory the script is called from.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generator.main import run  # noqa: E402

if __name__ == "__main__":
    run()
