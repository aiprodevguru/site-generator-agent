"""
Structured, coloured logger for the generator pipeline.

Import ``log`` directly for module-level logging, or call ``get_logger(name)``
to obtain a named child logger.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

# ── ANSI colour codes ──────────────────────────────────────────────────────────
_R  = "\033[0m"    # reset
_B  = "\033[1m"    # bold
_RE = "\033[91m"   # red
_GR = "\033[92m"   # green
_YE = "\033[93m"   # yellow
_BL = "\033[94m"   # blue
_MA = "\033[95m"   # magenta
_CY = "\033[96m"   # cyan
_GY = "\033[90m"   # grey


class _ColourFormatter(logging.Formatter):
    """Minimal single-line coloured formatter."""

    _LEVEL_COLOUR = {
        logging.DEBUG:    _GY,
        logging.INFO:     _CY,
        logging.WARNING:  _YE,
        logging.ERROR:    _RE,
        logging.CRITICAL: f"{_B}{_RE}",
    }

    def format(self, record: logging.LogRecord) -> str:
        ts    = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        color = self._LEVEL_COLOUR.get(record.levelno, _R)
        level = f"{color}{record.levelname:<8}{_R}"
        name  = f"{_GY}{record.name}{_R}"
        msg   = record.getMessage()
        # Include exception info if present
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        return f"{_GY}{ts}{_R}  {level}  {name}  {msg}"


def get_logger(
    name: str,
    *,
    level: int = logging.DEBUG,
    log_dir: Path | None = None,
) -> logging.Logger:
    """
    Return a named logger with a coloured console handler.

    If *log_dir* is provided, a plain-text file handler is also attached.
    Subsequent calls with the same *name* return the cached logger.
    """
    logger = logging.getLogger(f"whitepage.{name}")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Console
    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(_ColourFormatter())
    ch.setLevel(level)
    logger.addHandler(ch)

    # Optional file sink
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"generator_{stamp}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")
        )
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

    return logger


# Convenience root logger — import directly in other modules
log = get_logger("core")
