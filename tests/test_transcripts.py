"""Parser tests — JSONL -> unified turns, per platform."""
from __future__ import annotations

from pathlib import Path

from lib.transcripts.cursor import parse_cursor_turns
from lib.transcripts.claude import parse_claude_turns
from lib.transcripts.codex import parse_codex_turns

FIX = Path(__file__).resolve().parent / "fixtures" / "transcripts"


def test_cursor_post30_strips_tool_blocks():
    f = FIX / "cursor" / "abc123de-1111-2222-3333-444455556666" / "abc123de-1111-2222-3333-444455556666.jsonl"
    turns = parse_cursor_turns(f, True)
    assert [t["role"] for t in turns] == ["user", "assistant", "assistant"]
    assert "plan the port" in turns[0]["text"]
    # tool_use/tool_result dropped (Cursor parser drops tool blocks in both eras)
    assert "tool_use" not in "".join(t["text"] for t in turns)
    assert "file.txt" not in "".join(t["text"] for t in turns)


def test_cursor_pre30_keeps_text_turns():
    turns = parse_cursor_turns(FIX / "cursor" / "abc123de-1111-2222-3333-444455556666" / "abc123de-1111-2222-3333-444455556666.jsonl", False)
    # Cursor parser drops tool_use/tool_result blocks in both eras (matches the
    # original extract_context behavior); text turns survive.
    assert [t["role"] for t in turns] == ["user", "assistant", "assistant"]
    joined = "\n".join(t["text"] for t in turns)
    assert "Plan the port" in joined
    assert "I will plan it." in joined


def test_cursor_xml_wrapper_stripped_from_user():
    turns = parse_cursor_turns(FIX / "cursor" / "abc123de-1111-2222-3333-444455556666" / "abc123de-1111-2222-3333-444455556666.jsonl", True)
    assert "<user_query>" not in turns[0]["text"]


def test_claude_string_content():
    turns = parse_claude_turns(FIX / "claude" / "claude-string.jsonl", True)
    assert [t["role"] for t in turns] == ["user", "assistant", "assistant"]
    assert "plan the port" in turns[0]["text"]


def test_claude_post30_strips_tool_and_thinking():
    turns = parse_claude_turns(FIX / "claude" / "claude-string.jsonl", True)
    joined = "\n".join(t["text"] for t in turns)
    assert "let me think" not in joined  # thinking stripped
    assert "tool_use" not in joined
    assert "file.txt" not in joined  # tool_result stripped


def test_claude_pre30_keeps_thinking_and_tool():
    turns = parse_claude_turns(FIX / "claude" / "claude-string.jsonl", False)
    joined = "\n".join(t["text"] for t in turns)
    assert "let me think" in joined
    assert "[tool_use: Bash]" in joined
    assert "file.txt" in joined


def test_claude_skips_unknown_top_types():
    f = FIX / "claude" / "claude-string.jsonl"
    # post-3.0: tool_result-only user turn vanishes (no text left) -> 3 turns
    post = parse_claude_turns(f, True)
    assert len(post) == 3
    # pre-3.0: tool_result rendered -> 4 turns (user, assistant, user, assistant)
    pre = parse_claude_turns(f, False)
    assert len(pre) == 4
    # system + summary lines never produce turns in either era
    assert all(t["text"] for t in post) and all(t["text"] for t in pre)


def test_claude_task_and_agent_tool_names_both_parsed():
    turns = parse_claude_turns(FIX / "claude" / "claude-task-rename.jsonl", False)
    joined = "\n".join(t["text"] for t in turns)
    assert "[tool_use: Task]" in joined
    assert "[tool_use: Agent]" in joined


def test_codex_message_and_function_call():
    turns = parse_codex_turns(FIX / "codex" / "rollout-2026-05-02T10-00-00-000Z-aaa.jsonl", False)
    # user msg, assistant msg, tool_use (function_call), tool_result (function_call_output)
    assert turns[0]["role"] == "user" and "do the thing" in turns[0]["text"]
    assert turns[1]["role"] == "assistant" and "ok doing it" in turns[1]["text"]
    joined = "\n".join(t["text"] for t in turns)
    assert "[tool_use: shell]" in joined
    assert "done" in joined


def test_codex_post30_strips_tool_calls():
    turns = parse_codex_turns(FIX / "codex" / "rollout-2026-05-02T10-00-00-000Z-aaa.jsonl", True)
    assert [t["role"] for t in turns] == ["user", "assistant"]
    joined = "\n".join(t["text"] for t in turns)
    assert "tool_use" not in joined and "done" not in joined


def test_codex_unknown_types_skipped_defensively():
    turns = parse_codex_turns(FIX / "codex" / "rollout-unknown.jsonl", True)
    # Only the one valid message turn survives; unknown types skipped
    assert len(turns) == 1
    assert turns[0]["role"] == "user"
    assert "only this turn survives" in turns[0]["text"]
