"""Install + doctor tests — per-platform, in an isolated HOME."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str], env: dict, cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120, cwd=cwd)


def _install_and_doctor(platform: str, home: Path) -> int:
    env = dict(__import__("os").environ)
    env["USERPROFILE"] = str(home)
    env["HOME"] = str(home)
    env.pop("CONTEXT_WIKI_DIR", None)
    env.pop("WIKI_HOME", None)
    env.pop("WIKI_PLATFORM", None)
    py = sys.executable
    install = _run(
        [py, str(REPO_ROOT / "scripts" / "install_wiki.py"),
         "--platform", platform, "--source-repo", str(REPO_ROOT)],
        env, str(REPO_ROOT),
    )
    assert install.returncode == 0, f"install failed: {install.stdout}\n{install.stderr}"
    # Doctor already runs inside install; run again explicitly to assert exit 0
    doctor = _run(
        [py, str(home / ".context-wiki" / "runtime" / "scripts" / "doctor.py"),
         "--platform", platform],
        env, str(home / ".context-wiki" / "runtime"),
    )
    return doctor.returncode


def test_install_doctor_cursor(isolated_home):
    assert _install_and_doctor("cursor", isolated_home) == 0
    # Cursor-specific artifacts
    assert (isolated_home / ".cursor" / "rules" / "context-wiki.mdc").exists()
    assert (isolated_home / ".cursor" / "hooks.json").exists()
    hooks = (isolated_home / ".cursor" / "hooks.json").read_text()
    assert "context-wiki" in hooks or "wiki-on-start" in hooks


def test_install_doctor_claude(isolated_home):
    assert _install_and_doctor("claude", isolated_home) == 0
    settings = (isolated_home / ".claude" / "settings.json")
    assert settings.exists()
    import json
    data = json.loads(settings.read_text())
    assert "SessionStart" in data["hooks"]
    assert "UserPromptSubmit" in data["hooks"]
    assert data.get("cleanupPeriodDays") >= 90
    assert (isolated_home / ".claude" / "agents" / "wiki-synthesizer.md").exists()
    assert (isolated_home / ".claude" / "CLAUDE.md").exists()


def test_install_doctor_codex(isolated_home):
    assert _install_and_doctor("codex", isolated_home) == 0
    hooks = (isolated_home / ".codex" / "hooks.json")
    assert hooks.exists()
    import json
    data = json.loads(hooks.read_text())
    assert "SessionStart" in data["hooks"]
    assert "UserPromptSubmit" in data["hooks"]
    assert (isolated_home / ".codex" / "agents" / "wiki-synthesizer.toml").exists()
    assert (isolated_home / ".codex" / "AGENTS.md").exists()
