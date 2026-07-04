"""Minimal, dependency-free .env loading and Claude auth detection.

The Claude Agent SDK authenticates in one of two ways, and this module makes the
second one an easy, documented option for people who don't use Claude Code:

1. A logged-in ``claude`` CLI session (run ``claude`` once to log in), or
2. An ``ANTHROPIC_API_KEY`` in the environment.

External data-source keys (``NCBI_API_KEY``, ``OPENFDA_API_KEY``) are optional
and only raise rate limits. ``load_dotenv`` reads any of these from a local
``.env`` file into ``os.environ`` so they reach both this process and the
``claude`` subprocess the SDK spawns.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> list[str]:
    """Load ``KEY=VALUE`` lines from ``path`` into ``os.environ``.

    A variable already present in the real environment is never overwritten, so
    an exported value always wins over the file. Blank lines and ``#`` comments
    are ignored. Returns the names actually set; does nothing if the file is
    absent.
    """

    p = Path(path)
    if not p.is_file():
        return []
    loaded: list[str] = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded


def auth_note() -> str:
    """One-line description of how the Claude Agent SDK will authenticate."""

    if os.environ.get("ANTHROPIC_API_KEY"):
        return "auth: using ANTHROPIC_API_KEY from the environment."
    return (
        "auth: no ANTHROPIC_API_KEY set - using your logged-in `claude` CLI "
        "session (run `claude` to log in, or set ANTHROPIC_API_KEY in .env)."
    )
