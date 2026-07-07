"""Codex CLI transcript parser.

Rollout JSONL lines: {"timestamp","type","payload"}. Core types:
    session_meta / turn_context / config_snapshot / event_msg -> skipped
    input_item        -> user prompt/attachment
    response_item     -> payload.type in {message, function_call, function_call_output}

A model tool call is response_item with payload.type=="function_call" (args are
a stringified JSON in `arguments`); paired by call_id to a later
function_call_output. Assistant text is response_item payload.type=="message",
role=="assistant", content array of {type:"output_text", text}.

OpenAI states the transcript format is NOT a stable interface. This parser is
defensive: unknown `type` or `payload.type` values are skipped.

post-3.0 (mtime >= 2026-04-03): tool_use/tool_result blocks stripped from the
emitted text, matching the Cursor/Claude adapters.
"""
from __future__ import annotations

import json
from pathlib import Path

from .cursor import maybe_truncate, strip_xml_wrappers


def _msg_blocks_text(content: list, role: str, is_post30: bool) -> str:
    parts = []
    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type", "")
        text = block.get("text", "")
        if btype in ("input_text", "output_text", "text") and isinstance(text, str):
            if role == "user":
                text = strip_xml_wrappers(text)
            if text.strip():
                parts.append(maybe_truncate(text.strip(), "text block"))
        elif btype == "reasoning" and isinstance(text, str) and not is_post30:
            if text.strip():
                parts.append(maybe_truncate(text.strip(), "reasoning"))
    return "\n\n".join(parts)


def parse_codex_turns(jsonl_path: Path, is_post30: bool) -> list[dict]:
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
            rtype = obj.get("type", "")
            if rtype != "response_item":
                # input_item, session_meta, turn_context, config_snapshot, event_msg
                continue
            payload = obj.get("payload", {}) or {}
            ptype = payload.get("type", "")
            if ptype == "message":
                role = payload.get("role", "assistant")
                content = payload.get("content", [])
                if not isinstance(content, list):
                    content = []
                text = _msg_blocks_text(content, role, is_post30)
                if text:
                    turns.append({"role": role, "text": text})
            elif ptype == "function_call" and not is_post30:
                name = payload.get("name", "tool")
                turns.append({"role": "assistant", "text": maybe_truncate(f"[tool_use: {name}]", "tool_use")})
            elif ptype == "function_call_output" and not is_post30:
                out = payload.get("output", "")
                if isinstance(out, str) and out.strip():
                    turns.append({"role": "user", "text": maybe_truncate(out.strip(), "tool_result")})
    return turns
