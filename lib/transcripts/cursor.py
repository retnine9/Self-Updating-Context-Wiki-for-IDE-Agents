"""Cursor transcript parser — relocated from extract_context.py.

Expects lines of shape:
    {"role": "user"|"assistant", "message": {"content": [...] | "str"}}
Content blocks: {type: text|tool_use|tool_result, ...}.
post-3.0 (mtime >= 2026-04-03): tool_use/tool_result blocks stripped.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

TRUNCATE_BYTES = 10_000

XML_WRAPPERS = [
    "user_query", "system_reminder", "attached_files",
    "open_and_recently_viewed_files", "task_notification", "rules",
    "agent_skills", "agent_transcripts", "user_info", "system-communication",
    "tone_and_style", "tool_calling", "making_code_changes", "linter_errors",
    "citing_code", "inline_line_numbers", "terminal_files_information",
    "task_management", "mode_selection", "available_skills",
    "always_applied_workspace_rules", "always_applied_workspace_rule",
]


def strip_xml_wrappers(text: str) -> str:
    for tag in XML_WRAPPERS:
        pattern = rf"<{tag}(?:\s[^>]*)?>[\s]*(.*?)[\s]*</{tag}>"
        text = re.sub(pattern, r"\1", text, flags=re.DOTALL)
        text = re.sub(rf"</?{tag}(?:\s[^>]*)?>", "", text)
    return text.strip()


def maybe_truncate(text: str, label: str = "content") -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= TRUNCATE_BYTES:
        return text
    kb = len(encoded) / 1024
    return f"{text[:500]}\n\n[...truncated {kb:.0f}kb {label}]"


def _extract_text_blocks(content: list, role: str, is_post30: bool) -> str:
    parts = []
    for block in content:
        btype = block.get("type", "")
        if btype == "text":
            text = block.get("text", "")
            if role == "user":
                text = strip_xml_wrappers(text)
            if text.strip():
                parts.append(maybe_truncate(text.strip(), "text block"))
        elif btype in ("tool_use", "tool_result") and is_post30:
            pass
        elif btype not in ("text", "tool_use", "tool_result"):
            text = block.get("text", "") or block.get("content", "")
            if isinstance(text, str) and text.strip():
                parts.append(maybe_truncate(text.strip(), "unknown block"))
    return "\n\n".join(parts)


def parse_cursor_turns(jsonl_path: Path, is_post30: bool) -> list[dict]:
    turns = []
    with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = obj.get("role", "unknown")
            message = obj.get("message", {})
            content = message.get("content", [])
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            text = _extract_text_blocks(content, role, is_post30)
            if text:
                turns.append({"role": role, "text": text})
    return turns
