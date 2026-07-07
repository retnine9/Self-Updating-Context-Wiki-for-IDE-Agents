"""
doctor.py -- Health checks for context wiki installation.

Usage:
  python doctor.py           # Human-readable report
  python doctor.py --json    # Machine-readable for agents
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
    CURSOR_HOME,
    DEFAULT_WIKI_HOME,
    INSTALL_JSON,
    LOG_FILE,
    WIKI_HOME,
    WIKI_STATE_FILE,
)
from scripts.find_python import find_python

RULE_NAMES = [
    "context-wiki.mdc",
    "context-wiki-drain.mdc",
    "decision-capture.mdc",
]

WIKI_HOOK_MARKERS = ("wiki-on-start", "inject-wiki-drain")


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
    # Dev mode from clone
    clone_script = WIKI_HOME / "scripts" / "update_wiki.py"
    if clone_script.exists() and INSTALL_JSON.exists() is False:
        return _status(
            "wiki_runtime",
            True,
            f"Dev mode: {clone_script}",
            warn=True,
        )
    return _status(
        "wiki_runtime",
        False,
        f"Missing {script}",
        "Follow docs/SETUP.md step 3 or run: python scripts/install_wiki.py --source-repo <clone>",
    )


def check_context_dir() -> dict:
    if not CONTEXT_DIR.exists():
        return _status(
            "context_dir",
            False,
            f"Missing {CONTEXT_DIR}",
            "SETUP.md step 6: create context dirs from templates",
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
    projects = CURSOR_HOME / "projects"
    if not projects.exists():
        return _status(
            "transcripts",
            True,
            "No ~/.cursor/projects yet (new user)",
            warn=True,
        )
    found = []
    for p in projects.iterdir():
        if not p.is_dir():
            continue
        at = p / "agent-transcripts"
        if at.exists() and any(at.rglob("*.jsonl")):
            found.append(str(at))
    if found:
        return _status("transcripts", True, f"{len(found)} project(s) with transcripts")
    return _status(
        "transcripts",
        True,
        "No agent transcripts yet — wiki will populate after Cursor sessions",
        warn=True,
    )


def _load_hooks() -> dict | None:
    hooks_file = CURSOR_HOME / "hooks.json"
    if not hooks_file.exists():
        return None
    try:
        return json.loads(hooks_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def check_hooks() -> dict:
    data = _load_hooks()
    if data is None:
        return _status(
            "hooks",
            False,
            "Missing or invalid ~/.cursor/hooks.json",
            "SETUP.md step 7: merge wiki hooks",
        )
    hooks = data.get("hooks", data)
    issues = []
    for event in ("sessionStart", "beforeSubmitPrompt"):
        entries = hooks.get(event, [])
        if not entries:
            issues.append(f"no {event}")
            continue
        cmds = " ".join(str(e.get("command", "")) for e in entries)
        if not any(m in cmds for m in WIKI_HOOK_MARKERS):
            issues.append(f"{event} missing wiki hook script")
    if issues:
        return _status("hooks", False, "; ".join(issues), "SETUP.md step 7")
    return _status("hooks", True, "sessionStart + beforeSubmitPrompt configured")


def check_rules() -> dict:
    rules_dir = CURSOR_HOME / "rules"
    missing = [n for n in RULE_NAMES if not (rules_dir / n).exists()]
    if missing:
        return _status(
            "rules",
            False,
            f"Missing: {missing}",
            "SETUP.md step 4: copy cursor/rules/*.mdc",
        )
    return _status("rules", True, f"All {len(RULE_NAMES)} rules present")


def check_wiki_state() -> dict:
    if not WIKI_STATE_FILE.exists():
        return _status(
            "wiki_state",
            True,
            "wiki_state.json not created yet (will init on first run)",
            warn=True,
        )
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
    ]
    has_fail = any(c["status"] == "fail" for c in checks)
    has_warn = any(c["status"] == "warn" for c in checks)
    code = 2 if has_fail else (1 if has_warn else 0)
    return checks, code


def main() -> int:
    parser = argparse.ArgumentParser(description="Context wiki health checks")
    parser.add_argument("--json", action="store_true", help="JSON output for agents")
    args = parser.parse_args()

    checks, code = run_all()
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "wiki_home": str(WIKI_HOME),
        "context_dir": str(CONTEXT_DIR),
        "checks": checks,
        "exit_code": code,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return code

    print("Context Wiki Doctor")
    print("===================")
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
