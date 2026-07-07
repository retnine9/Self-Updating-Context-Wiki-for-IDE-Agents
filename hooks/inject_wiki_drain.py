"""Unified drain emitter for all platforms (Cursor, Claude Code, Codex CLI).

Reads the platform from WIKI_PLATFORM (or auto-detect), calls
update_wiki.py --drain-message --platform <p>, and prints the hook stdout JSON
in the platform-correct envelope:

  cursor: {"agent_message": "..."}
  claude: {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}
  codex:  {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}

One-shot guard via .drain_injected prevents re-injection on every prompt in a
session (matters for Codex where additionalContext is currently persisted into
the rollout — see docs/PLATFORM_QUIRKS.md).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wiki_common  # noqa: E402

sys.path.insert(0, str(wiki_common.REPO_ROOT))
from lib.platform import get_platform  # noqa: E402


def _emit_empty() -> None:
    print("{}")
    sys.exit(0)


def main() -> int:
    wiki_common.load_wiki_env()
    wiki_home = wiki_common.resolve_wiki_home()
    ctx = wiki_common.resolve_context_dir()
    drain_file = ctx / ".drain_required.json"
    injected_file = ctx / ".drain_injected"

    if not drain_file.exists() or injected_file.exists():
        _emit_empty()
        return 0

    try:
        json.loads(drain_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        _emit_empty()
        return 0

    platform = get_platform()
    os.environ["CONTEXT_WIKI_DIR"] = str(ctx)
    os.environ["WIKI_HOME"] = str(wiki_home)
    os.environ.setdefault("WIKI_PLATFORM", platform.name)

    py = wiki_common.find_python()
    cmd = py.split() + [str(wiki_home / "scripts" / "update_wiki.py"),
                        "--drain-message", "--platform", platform.name]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        payload = proc.stdout.strip()
    except Exception as e:  # noqa: BLE001
        wiki_common.log(f"drain error: {e}")
        _emit_empty()
        return 0

    if not payload or payload == "{}":
        _emit_empty()
        return 0

    # update_wiki.py --drain-message already emits the platform-correct JSON
    # envelope (agent_message for Cursor, hookSpecificOutput.additionalContext
    # for Claude/Codex). We just guard + forward.
    try:
        injected_file.touch()
    except OSError:
        pass
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
