"""Extract (Layer 1) end-to-end tests: fixture JSONL -> session markdown."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from lib.platform.base import SessionRef
from lib.platform.cursor import CursorPlatform
from lib.platform.claude import ClaudePlatform

FIX = Path(__file__).resolve().parent / "fixtures" / "transcripts"


def _make_cursor_ref() -> SessionRef:
    session_dir = FIX / "cursor" / "abc123de-1111-2222-3333-444455556666"
    main = session_dir / "abc123de-1111-2222-3333-444455556666.jsonl"
    subs = [session_dir / "subagents" / "sub111111-aaaa-bbbb-cccc-ddddeeeeffff.jsonl"]
    return SessionRef(uuid="abc123de-1111-2222-3333-444455556666",
                      main_jsonl=main, subagent_jsonls=subs, mtime=main.stat().st_mtime)


def test_cursor_extract_writes_session_md(isolated_context):
    from scripts import extract_context as ex
    ref = _make_cursor_ref()
    result = ex.process_session(ref, force=True)
    assert result is not None
    assert result["skipped"] is False
    md = result["path"].read_text(encoding="utf-8")
    assert "session: abc123de" in md
    assert "## User" in md and "## Assistant" in md
    assert "plan the port" in md
    # Subagent section present
    assert "## Subagents" in md
    assert "### Subagent sub11111" in md


def test_cursor_extract_post30_era_label(isolated_context, monkeypatch):
    from scripts import extract_context as ex
    # Force post-3.0 mtime
    ref = _make_cursor_ref()
    ref.mtime = datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp()
    result = ex.process_session(ref, force=True)
    md = result["path"].read_text(encoding="utf-8")
    assert "era: post-3.0" in md


def test_claude_extract_writes_session_md(isolated_context, monkeypatch):
    from scripts import extract_context as ex
    monkeypatch.setenv("WIKI_PLATFORM", "claude")
    from lib.platform import reset_platform_cache
    reset_platform_cache()
    main = FIX / "claude" / "claude-string.jsonl"
    ref = SessionRef(uuid="claude-string", main_jsonl=main, subagent_jsonls=[],
                     mtime=main.stat().st_mtime)
    result = ex.process_session(ref, force=True)
    assert result is not None
    md = result["path"].read_text(encoding="utf-8")
    assert "session: claude-s" in md
    assert "plan the port" in md
    # No tool noise (post-3.0 default since fixture mtime is recent)
    assert "tool_use" not in md


def test_extract_skip_if_exists(isolated_context):
    from scripts import extract_context as ex
    ref = _make_cursor_ref()
    first = ex.process_session(ref, force=True)
    second = ex.process_session(ref, force=False)
    assert second["skipped"] is True
    assert second["path"] == first["path"]


def test_extract_all_builds_index(isolated_context, monkeypatch, tmp_path):
    from scripts import extract_context as ex
    # Point transcripts dir at cursor fixtures via env + custom platform
    monkeypatch.setenv("TRANSCRIPTS_DIR", str(FIX / "cursor"))
    monkeypatch.setenv("WIKI_PLATFORM", "cursor")
    from lib.platform import reset_platform_cache
    reset_platform_cache()
    importlib_reload_paths()
    summary = ex.extract_all(force=True)
    assert summary["processed"] >= 1
    from lib.paths import INDEX_FILE
    assert INDEX_FILE.exists()
    assert "Session Index" in INDEX_FILE.read_text(encoding="utf-8")


def importlib_reload_paths():
    import importlib
    import lib.paths
    importlib.reload(lib.paths)
    import scripts.extract_context as ex
    importlib.reload(ex)
