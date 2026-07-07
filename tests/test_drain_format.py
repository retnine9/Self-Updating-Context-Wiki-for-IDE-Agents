"""Drain message envelope tests — per-platform JSON shape."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_drain(platform: str, context_dir: Path) -> dict:
    """Run update_wiki.py --drain-message --platform in a fresh subprocess."""
    env = dict(__import__("os").environ)
    env["CONTEXT_WIKI_DIR"] = str(context_dir)
    env["WIKI_HOME"] = str(REPO_ROOT)
    env["WIKI_PLATFORM"] = platform
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "update_wiki.py"),
           "--drain-message", "--platform", platform]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
    return json.loads(proc.stdout.strip())


def _seed_drain(context_dir: Path, model: str = "test-model") -> None:
    context_dir.mkdir(parents=True, exist_ok=True)
    (context_dir / ".drain_required.json").write_text(json.dumps({
        "count": 2, "uuids": ["aaaaaaaa", "bbbbbbbb"],
        "set_at": "2026-07-07T00:00:00Z", "synthesis_model": model,
    }), encoding="utf-8")


def test_drain_cursor_envelope(tmp_path):
    _seed_drain(tmp_path)
    out = _run_drain("cursor", tmp_path)
    assert "agent_message" in out
    assert "MANDATORY CONTEXT WIKI DRAIN" in out["agent_message"]
    assert "hookSpecificOutput" not in out


def test_drain_claude_envelope(tmp_path):
    _seed_drain(tmp_path)
    out = _run_drain("claude", tmp_path)
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "additionalContext" in out["hookSpecificOutput"]
    assert "Agent tool" in out["hookSpecificOutput"]["additionalContext"]
    assert "agent_message" not in out


def test_drain_codex_envelope(tmp_path):
    _seed_drain(tmp_path)
    out = _run_drain("codex", tmp_path)
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "additionalContext" in out["hookSpecificOutput"]
    assert "agent_message" not in out


def test_drain_empty_when_no_flag(tmp_path):
    out = _run_drain("cursor", tmp_path)  # no .drain_required.json
    assert out == {}
