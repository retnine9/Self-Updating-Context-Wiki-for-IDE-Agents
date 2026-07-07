"""Platform abstraction for the context wiki.

Auto-detects the host IDE/CLI (Cursor, Claude Code, Codex CLI) and exposes a
unified Platform interface for transcript discovery, hook config, drain output
format, rules/skills install locations, and per-platform synthesis defaults.

Override with WIKI_PLATFORM=cursor|claude|codex.
"""
from __future__ import annotations

import os
from pathlib import Path

from .base import Platform

__all__ = ["Platform", "get_platform"]

_CACHE: Platform | None = None


def _auto_detect() -> str:
    env = os.environ.get("WIKI_PLATFORM", "").strip().lower()
    if env in ("cursor", "claude", "codex"):
        return env
    home = Path.home()
    cursor = home / ".cursor"
    claude = home / ".claude"
    codex = home / ".codex"
    has_cursor = cursor.exists() and (cursor / "projects").exists()
    has_claude = claude.exists() and (claude / "projects").exists()
    has_codex = codex.exists() and (codex / "sessions").exists()
    if has_cursor:
        return "cursor"
    if has_claude:
        return "claude"
    if has_codex:
        return "codex"
    return "cursor"


def get_platform() -> Platform:
    """Return the active Platform instance (cached)."""
    global _CACHE
    if _CACHE is None:
        name = _auto_detect()
        if name == "cursor":
            from .cursor import CursorPlatform
            _CACHE = CursorPlatform()
        elif name == "claude":
            from .claude import ClaudePlatform
            _CACHE = ClaudePlatform()
        elif name == "codex":
            from .codex import CodexPlatform
            _CACHE = CodexPlatform()
        else:
            raise RuntimeError(f"Unknown platform: {name}")
    return _CACHE


def reset_platform_cache() -> None:
    """Test hook: clear the cached platform so env changes take effect."""
    global _CACHE
    _CACHE = None
