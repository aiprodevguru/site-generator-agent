"""
Shared utility functions used across the generator pipeline.

Includes: retry decorator, text helpers, slug conversion, name inference.
"""
from __future__ import annotations

import re
import time
import functools
from typing import TypeVar, Callable, Any

from generator.logger import get_logger

log = get_logger("utils")

_F = TypeVar("_F", bound=Callable[..., Any])


# ── Retry decorator ────────────────────────────────────────────────────────────

def retry(
    max_attempts: int = 3,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[_F], _F]:
    """
    Exponential-backoff retry decorator.

    Parameters
    ----------
    max_attempts : int
        Total number of attempts (including the first).
    backoff : float
        Base delay in seconds.  Delay after attempt N = backoff ** (N-1).
    exceptions : tuple
        Only retry on these exception types.

    Example
    -------
    ::

        @retry(max_attempts=3, backoff=2.0, exceptions=(openai.OpenAIError,))
        def call_api() -> dict: ...
    """
    def decorator(fn: _F) -> _F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    wait = backoff ** (attempt - 1)
                    log.warning(
                        f"{fn.__name__} — attempt {attempt}/{max_attempts} failed: "
                        f"{type(exc).__name__}: {exc}"
                        + (f" — retrying in {wait:.1f}s" if attempt < max_attempts else "")
                    )
                    if attempt < max_attempts:
                        time.sleep(wait)
            raise RuntimeError(
                f"{fn.__name__} failed after {max_attempts} attempts"
            ) from last_exc
        return wrapper  # type: ignore[return-value]
    return decorator


# ── Text helpers ───────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """
    Convert human-readable text to a URL-safe slug.

    'Dragon Quest 2' → 'dragon-quest-2'
    """
    text = text.lower().strip()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^a-z0-9\-]", "", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def folder_to_title(folder: str) -> str:
    """
    Convert a file-system folder name to a display title.

    'dragon-quest'  → 'Dragon Quest'
    'space_blast_2' → 'Space Blast 2'
    """
    return re.sub(r"[-_]+", " ", folder).title()


def escape_php_string(text: str) -> str:
    """
    Escape a value for safe embedding inside a PHP single-quoted string.

    PHP single-quoted strings only need backslash and single-quote escaped.
    """
    return text.replace("\\", "\\\\").replace("'", "\\'")


def escape_html_attr(text: str) -> str:
    """Escape text for safe use inside an HTML attribute value."""
    return (
        text
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def contains_banned_words(text: str, banned: list[str]) -> list[str]:
    """Return banned terms found as standalone words or phrases."""
    lower = text.lower()
    matches: list[str] = []
    for banned_term, pattern in _compiled_banned_patterns(tuple(banned)):
        if pattern.search(lower):
            matches.append(banned_term)
    return matches


@functools.lru_cache(maxsize=8)
def _compiled_banned_patterns(
    banned: tuple[str, ...],
) -> tuple[tuple[str, re.Pattern[str]], ...]:
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for term in banned:
        tokens = re.findall(r"[a-z0-9]+", term.lower())
        if not tokens:
            continue
        joined = r"[\W_]*".join(re.escape(token) for token in tokens)
        compiled.append(
            (
                term,
                re.compile(rf"(?<![a-z0-9]){joined}(?![a-z0-9])", re.IGNORECASE),
            )
        )
    return tuple(compiled)


_TLD_RE   = re.compile(r'\.[a-z]{2,6}$', re.IGNORECASE)
_SPLIT_RE = re.compile(r'[-_.\s]+')


def build_brand_name(batch_name: str) -> str:
    """
    Derive a human-readable brand hint from a batch/domain name.

    Steps:
      1. Strip the TLD (.com, .net, .io, .gg, …)
      2. Split camelCase / PascalCase on boundaries
      3. Split on hyphens, underscores, and dots
      4. Title-case each word and join

    The result is passed to GPT-4o as a ``brand_hint`` so the model can
    refine it into a polished brand name.

    Examples
    --------
    'lunargamesummit.com' → 'Lunargamesummit'   (GPT refines → 'Lunar Game Summit')
    'dragon-arena.net'    → 'Dragon Arena'
    'lunar-game-summit'   → 'Lunar Game Summit'
    'LunarGameSummit'     → 'Lunar Game Summit'
    """
    name = _TLD_RE.sub('', batch_name)
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)   # camelCase split
    parts = [p for p in _SPLIT_RE.split(name) if p]
    return ' '.join(p.capitalize() for p in parts) if parts else batch_name


def infer_topic(game_folders: list[str], keyword_map: dict[str, str], default: str) -> str:
    """
    Match folder name tokens against *keyword_map* and return the first topic found.
    Falls back to *default* if no keyword matches.
    """
    combined = " ".join(game_folders).lower()
    for keyword, topic in keyword_map.items():
        if keyword in combined:
            return topic
    return default


def infer_tone(game_folders: list[str], keyword_map: dict[str, str], default: str) -> str:
    """Same as ``infer_topic`` but for tone."""
    combined = " ".join(game_folders).lower()
    for keyword, tone in keyword_map.items():
        if keyword in combined:
            return tone
    return default
