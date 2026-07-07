"""Migration tests — legacy ~/.cursor home -> neutral ~/.context-wiki."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.migrate_to_neutral_home import migrate


def _seed_legacy(home: Path) -> None:
    cur = home / ".cursor"
    (cur / "wiki" / "scripts").mkdir(parents=True, exist_ok=True)
    (cur / "wiki" / "scripts" / "update_wiki.py").write_text("# wiki", encoding="utf-8")
    (cur / "context" / "sessions").mkdir(parents=True, exist_ok=True)
    (cur / "context" / "sessions" / "old.md").write_text("old session", encoding="utf-8")
    hooks = {
        "version": 1,
        "hooks": {
            "sessionStart": [{"command": "powershell -File C:\\old\\.cursor\\wiki\\hooks\\wiki-on-start.ps1", "timeout": 120}],
            "beforeSubmitPrompt": [{"command": "powershell -File C:\\old\\.cursor\\wiki\\hooks\\inject-wiki-drain.ps1", "matcher": "UserPromptSubmit", "timeout": 15}],
            "other": [{"command": "keep-me"}],
        },
    }
    (cur / "hooks.json").write_text(json.dumps(hooks), encoding="utf-8")


def test_migration_moves_data_and_repoints_hooks(isolated_home):
    _seed_legacy(isolated_home)
    result = migrate(dry=False)
    steps = "\n".join(result["steps"])
    assert "moved" in steps

    # Data moved
    assert (isolated_home / ".context-wiki" / "data" / "sessions" / "old.md").exists()
    assert (isolated_home / ".context-wiki" / "runtime" / "scripts" / "update_wiki.py").exists()

    # hooks.json repointed to neutral runtime, other hook preserved
    hooks = json.loads((isolated_home / ".cursor" / "hooks.json").read_text())
    cmds = json.dumps(hooks)
    assert ".context-wiki" in cmds
    assert "keep-me" in cmds

    # Legacy location is now a link (symlink or junction)
    legacy_wiki = isolated_home / ".cursor" / "wiki"
    assert legacy_wiki.exists()  # junction/symlink resolves


def test_migration_idempotent(isolated_home):
    _seed_legacy(isolated_home)
    migrate(dry=False)
    result2 = migrate(dry=False)
    steps2 = "\n".join(result2["steps"])
    # Second run must not re-move (dst exists) and must not crash
    assert "moved" not in steps2


def test_migration_dry_run_does_not_touch_fs(isolated_home):
    _seed_legacy(isolated_home)
    migrate(dry=True)
    # Legacy still real dirs (not moved)
    assert (isolated_home / ".cursor" / "wiki" / "scripts" / "update_wiki.py").exists()
    assert not (isolated_home / ".context-wiki").exists()


def test_migration_no_legacy_is_noop(isolated_home):
    result = migrate(dry=False)
    assert "nothing to migrate" in "\n".join(result["steps"])
