"""Claude Code transcript parser.

Each JSONL line is one JSON object discriminated by top-level `type`:
    user       -> {"message": {"role":"user","content": str | [blocks]}}
    assistant  -> {"message": {"role":"assistant","content": [blocks]}}
    summary / system / tool-use-status / telemetry -> skipped

Content block types: text, thinking, tool_use ({id,name,input}),
tool_result ({tool_use_id, content}). tool_result blocks arrive inside a
later `type:user` row matching the tool_use_id.

The schema is undocumented and drifts between Claude Code releases; this parser
is permissive and skips anything it does not recognise.

post-3.0 (mtime >= 2026-04-03): tool_use/tool_result blocks stripped from the
emitted text, matching the Cursor adapter's behaviour so session markdown is
shape-identical across platforms.
"""
from __future__ import annotations

import json
from pathlib import Path

from .cursor import maybe_truncate, strip_xml_wrappers

TRUNCATE_BYTES = 10_000


def _content_to_blocks(content) -> list:
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return content
    return []


def _blocks_text(blocks: list, role: str, is_post30: bool) -> str:
    parts = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        btype = block.get("type", "")
        if btype == "text":
            text = block.get("text", "")
            if role == "user":
                text = strip_xml_wrappers(text)
            if isinstance(text, str) and text.strip():
                parts.append(maybe_truncate(text.strip(), "text block"))
        elif btype == "thinking":
            thinking = block.get("thinking", "")
            if isinstance(thinking, str) and thinking.strip() and not is_post30:
                parts.append(maybe_truncate(thinking.strip(), "thinking"))
        elif btype in ("tool_use", "tool_result") and is_post30:
            pass
        elif btype in ("tool_use", "tool_result"):
            # pre-3.0: include a compact rendering of the tool call/result
            if btype == "tool_use":
                name = block.get("name", "tool")
                parts.append(maybe_truncate(f"[tool_use: {name}]", "tool_use"))
            else:
                c = block.get("content", "")
                if isinstance(c, list):
                    c = " ".join(
                        b.get("text", "") for b in c if isinstance(b, dict)
                    )
                if isinstance(c, str) and c.strip():
                    parts.append(maybe_truncate(c.strip(), "tool_result"))
        else:
            text = block.get("text", "") or block.get("content", "")
            if isinstance(text, str) and text.strip():
                parts.append(maybe_truncate(text.strip(), "unknown block"))
    return "\n\n".join(parts)


def parse_claude_turns(jsonl_path: Path, is_post30: bool) -> list[dict]:
    turns: list[dict] = []
    with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ttype = obj.get("type", "")
            if ttype not in ("user", "assistant"):
                continue
            message = obj.get("message", {}) or {}
            role = message.get("role") or ttype
            blocks = _content_to_blocks(message.get("content", []))
            text = _blocks_text(blocks, role, is_post30)
            if text:
                turns.append({"role": role, "text": text})
    return turns
