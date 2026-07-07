"""Transcript parsers — JSONL -> unified turns.

Unified turn shape (internal):
    {"role": "user" | "assistant", "text": str}

Dispatcher selects the parser by platform name. Each parser is defensive: it
skips lines it cannot recognise rather than raising, so schema drift between
IDE releases degrades gracefully instead of crashing Layer 1.
"""
from __future__ import annotations

from pathlib import Path


def parse_turns(jsonl_path: Path, platform: str, is_post30: bool) -> list[dict]:
    if platform == "cursor":
        from .cursor import parse_cursor_turns
        return parse_cursor_turns(jsonl_path, is_post30)
    if platform == "claude":
        from .claude import parse_claude_turns
        return parse_claude_turns(jsonl_path, is_post30)
    if platform == "codex":
        from .codex import parse_codex_turns
        return parse_codex_turns(jsonl_path, is_post30)
    raise ValueError(f"Unknown platform: {platform}")
