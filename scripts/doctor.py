"""
doctor.py -- Health checks for context wiki installation (per platform).

Usage:
  python doctor.py                      # auto-detect platform
  python doctor.py --platform claude    # force platform
  python doctor.py --json               # machine-readable for agents
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from lib.paths import (
    CONTEXT_DIR,
    DEFAULT_WIKI_HOME,
    INSTALL_JSON,
    LOG_FILE,
    WIKI_HOME,
    WIKI_STATE_FILE,
)
from lib.platform import get_platform
from scripts.find_python import find_python

CURSOR_RULE_NAMES = [
    "context-wiki.mdc",
    "context-wiki-drain.mdc",
    "decision-capture.mdc",
]

WIKI_HOOK_MARKERS = ("wiki_on_start", "inject_wiki_drain", "wiki-on-start", "inject-wiki-drain")


def _status(name: str, ok: bool, detail: str, fix: str = "", warn: bool = False) -> dict:
    level = "pass" if ok else ("warn" if warn else "fail")
    return {"check": name, "status": level, "detail": detail, "fix": fix}


def check_python() -> dict:
    found = find_python()
    env_py = os.environ.get("WIKI_PYTHON")
    if found:
        return _status("python", True, f"Found: {found}" + (f" (env: {env_py})" if env_py else ""))
    return _status(
        "python",
        False,
        "No Python 3 on PATH",
        "Run: python scripts/find_python.py --write-env (from clone) or install Python 3",
    )


def check_wiki_runtime() -> dict:
    script = DEFAULT_WIKI_HOME / "scripts" / "update_wiki.py"
    if script.exists():
        return _status("wiki_runtime", True, str(script))
    clone_script = WIKI_HOME / "scripts" / "update_wiki.py"
    if clone_script.exists() and INSTALL_JSON.exists() is False:
        return _status("wiki_runtime", True, f"Dev mode: {clone_script}", warn=True)
    return _status(
        "wiki_runtime",
        False,
        f"Missing {script}",
        "Follow docs/SETUP.md or run: python scripts/install_wiki.py --source-repo <clone>",
    )


def check_context_dir() -> dict:
    if not CONTEXT_DIR.exists():
        return _status(
            "context_dir",
            False,
            f"Missing {CONTEXT_DIR}",
            "Run install_wiki.py, or create sessions/ extracts/ synthesis/ under the context dir",
        )
    missing = [d for d in ("sessions", "extracts", "synthesis") if not (CONTEXT_DIR / d).is_dir()]
    if missing:
        return _status(
            "context_dir",
            False,
            f"Missing subdirs: {missing}",
            "Create sessions/, extracts/, synthesis/ under context dir",
        )
    if not os.access(CONTEXT_DIR, os.W_OK):
        return _status("context_dir", False, f"Not writable: {CONTEXT_DIR}")
    return _status("context_dir", True, str(CONTEXT_DIR))


def check_transcripts() -> dict:
    platform = get_platform()
    sessions = platform.discover_sessions()
    if sessions:
        return _status("transcripts", True, f"{len(sessions)} session(s) at {platform.resolve_transcripts_dir()}")
    return _status(
        "transcripts",
        True,
        f"No transcripts yet at {platform.resolve_transcripts_dir()} — wiki populates after sessions",
        warn=True,
    )


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _cursor_hooks_ok(data: dict, start_event: str, drain_event: str) -> list[str]:
    """Flat Cursor hooks.json shape: {hooks: {Event: [{command, ...}]}}."""
    hooks = data.get("hooks", data)
    issues = []
    for event in (start_event, drain_event):
        entries = hooks.get(event, [])
        if not entries:
            issues.append(f"no {event}")
            continue
        cmds = " ".join(str(e.get("command", "")) for e in entries)
        if not any(m in cmds for m in WIKI_HOOK_MARKERS):
            issues.append(f"{event} missing wiki hook script")
    return issues


def _nested_hooks_ok(data: dict, start_event: str, drain_event: str) -> list[str]:
    """Claude/Codex nested shape: {hooks: {Event: [{matcher, hooks:[{type,command}]}]}}."""
    hooks = data.get("hooks", {})
    issues = []
    for event in (start_event, drain_event):
        blocks = hooks.get(event, [])
        if not blocks:
            issues.append(f"no {event}")
            continue
        cmds = []
        for block in blocks:
            for h in block.get("hooks", []):
                cmds.append(str(h.get("command", "")))
        joined = " ".join(cmds)
        if not any(m in joined for m in WIKI_HOOK_MARKERS):
            issues.append(f"{event} missing wiki hook script")
    return issues


def check_hooks() -> dict:
    platform = get_platform()
    start_event, drain_event = platform.hook_event_names()
    config_paths = platform.hook_config_paths()
    if not config_paths:
        return _status("hooks", False, "No hook config path for platform", "Run install_wiki.py --platform " + platform.name)
    primary = config_paths[0]
    data = _load_json(primary)
    if data is None:
        return _status(
            "hooks",
            False,
            f"Missing or invalid {primary}",
            f"Run: python scripts/install_wiki.py --platform {platform.name}",
        )
    if platform.name == "cursor":
        issues = _cursor_hooks_ok(data, start_event, drain_event)
    else:
        issues = _nested_hooks_ok(data, start_event, drain_event)
    if issues:
        return _status("hooks", False, "; ".join(issues), f"install_wiki.py --platform {platform.name}")
    return _status("hooks", True, f"{start_event} + {drain_event} configured in {primary}")


def check_rules() -> dict:
    platform = get_platform()
    rules_dir = platform.rules_install_dir()
    if platform.name == "cursor":
        missing = [n for n in CURSOR_RULE_NAMES if not (rules_dir / n).exists()]
        if missing:
            return _status("rules", False, f"Missing: {missing}", "install_wiki.py --platform cursor")
        return _status("rules", True, f"All {len(CURSOR_RULE_NAMES)} rules present at {rules_dir}")
    if platform.name == "claude":
        # Subagent definition + CLAUDE.md snippet
        have_subagent = (rules_dir / "wiki-synthesizer.md").exists()
        have_snippet = (rules_dir.parent / "CLAUDE.md").exists()
        missing = []
        if not have_subagent:
            missing.append("agents/wiki-synthesizer.md")
        if not have_snippet:
            missing.append("CLAUDE.md")
        if missing:
            return _status("rules", False, f"Missing: {missing}", "install_wiki.py --platform claude")
        return _status("rules", True, f"Subagent + CLAUDE.md present at {rules_dir}")
    if platform.name == "codex":
        have_subagent = (rules_dir / "wiki-synthesizer.toml").exists()
        have_snippet = (rules_dir.parent / "AGENTS.md").exists()
        missing = []
        if not have_subagent:
            missing.append("agents/wiki-synthesizer.toml")
        if not have_snippet:
            missing.append("AGENTS.md")
        if missing:
            return _status("rules", False, f"Missing: {missing}", "install_wiki.py --platform codex")
        return _status("rules", True, f"Subagent + AGENTS.md present at {rules_dir}")
    return _status("rules", True, str(rules_dir))


def check_wiki_state() -> dict:
    if not WIKI_STATE_FILE.exists():
        return _status("wiki_state", True, "wiki_state.json not created yet (will init on first run)", warn=True)
    try:
        state = json.loads(WIKI_STATE_FILE.read_text(encoding="utf-8"))
        pending = len(state.get("pending_sessions", []))
        return _status("wiki_state", True, f"pending_sessions={pending}")
    except (json.JSONDecodeError, OSError) as e:
        return _status("wiki_state", False, str(e), "Delete or fix wiki_state.json")


def check_log() -> dict:
    if not LOG_FILE.exists():
        return _status("log", True, "No wiki.log yet", warn=True)
    try:
        lines = LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
        tail = lines[-5:] if lines else []
        return _status("log", True, "Last lines: " + " | ".join(tail[-2:]))
    except OSError as e:
        return _status("log", True, f"Could not read log: {e}", warn=True)


def check_platform_hint() -> dict:
    """Honesty guard: warn if non-Cursor transcripts are present but WIKI_PLATFORM unset."""
    if os.environ.get("WIKI_PLATFORM"):
        return _status("platform_hint", True, f"WIKI_PLATFORM={os.environ['WIKI_PLATFORM']}")
    home = Path.home()
    found: list[str] = []
    claude_projects = home / ".claude" / "projects"
    codex_sessions = home / ".codex" / "sessions"
    if claude_projects.exists() and any(claude_projects.rglob("*.jsonl")):
        found.append("claude")
    if codex_sessions.exists() and any(codex_sessions.rglob("*.jsonl")):
        found.append("codex")
    if not found:
        return _status("platform_hint", True, "No non-Cursor transcripts detected")
    return _status(
        "platform_hint",
        True,
        f"Detected {found} transcripts but WIKI_PLATFORM unset",
        "Set WIKI_PLATFORM=claude|codex (or run install_wiki.py --platform <p>).",
        warn=True,
    )


def check_platform_specific() -> dict:
    platform = get_platform()
    if platform.name == "claude":
        settings = Path.home() / ".claude" / "settings.json"
        data = _load_json(settings)
        if data is None:
            return _status("platform_specific", True, "No ~/.claude/settings.json yet", warn=True)
        cleanup = data.get("cleanupPeriodDays")
        if isinstance(cleanup, int) and cleanup < 90:
            return _status(
                "platform_specific",
                True,
                f"cleanupPeriodDays={cleanup} (<90): transcripts purged before drain can fire",
                "Set cleanupPeriodDays>=90 in ~/.claude/settings.json (install_wiki.py does this)",
                warn=True,
            )
        return _status("platform_specific", True, f"cleanupPeriodDays={cleanup}")
    if platform.name == "codex":
        # Trust-flow reminder
        return _status(
            "platform_specific",
            True,
            "Codex requires hook trust: run `/hooks` once in the CLI to trust wiki hooks",
            "After install, open Codex CLI and run /hooks to review + trust the wiki hooks",
            warn=True,
        )
    return _status("platform_specific", True, "No platform-specific caveats")


def run_all() -> tuple[list[dict], int]:
    checks = [
        check_python(),
        check_wiki_runtime(),
        check_context_dir(),
        check_transcripts(),
        check_hooks(),
        check_rules(),
        check_wiki_state(),
        check_log(),
        check_platform_hint(),
        check_platform_specific(),
    ]
    has_fail = any(c["status"] == "fail" for c in checks)
    has_warn = any(c["status"] == "warn" for c in checks)
    code = 2 if has_fail else (1 if has_warn else 0)
    return checks, code


def main() -> int:
    parser = argparse.ArgumentParser(description="Context wiki health checks")
    parser.add_argument("--json", action="store_true", help="JSON output for agents")
    parser.add_argument(
        "--platform",
        choices=("cursor", "claude", "codex"),
        default=None,
        help="Force platform (default: auto-detect)",
    )
    args = parser.parse_args()

    if args.platform:
        os.environ["WIKI_PLATFORM"] = args.platform
        # Reset cached platform + re-import paths so CONTEXT_DIR/TRANSCRIPTS_DIR reflect it
        from lib.platform import reset_platform_cache
        reset_platform_cache()
        import importlib
        import lib.paths as _paths
        importlib.reload(_paths)
        # Re-bind module-level names used by doctor
        global CONTEXT_DIR, WIKI_STATE_FILE, LOG_FILE
        CONTEXT_DIR = _paths.CONTEXT_DIR
        WIKI_STATE_FILE = _paths.WIKI_STATE_FILE
        LOG_FILE = _paths.LOG_FILE

    platform = get_platform()
    checks, code = run_all()
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform.name,
        "wiki_home": str(WIKI_HOME),
        "context_dir": str(CONTEXT_DIR),
        "checks": checks,
        "exit_code": code,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return code

    print(f"Context Wiki Doctor ({platform.name})")
    print("=" * (22 + len(platform.name)))
    for c in checks:
        icon = {"pass": "OK", "warn": "WARN", "fail": "FAIL"}[c["status"]]
        print(f"[{icon}] {c['check']}: {c['detail']}")
        if c["fix"] and c["status"] != "pass":
            print(f"      fix: {c['fix']}")
    print()
    if code == 0:
        print("All checks passed.")
    elif code == 1:
        print("Passed with warnings.")
    else:
        print("Failures found — see docs/SETUP.md or docs/TROUBLESHOOTING.md")
    return code


if __name__ == "__main__":
    sys.exit(main())
