"""
install_wiki.py -- Install context wiki runtime to ~/.cursor/wiki/

Implements docs/SETUP.md steps programmatically. Used by install.ps1/sh
and by agents after clone.

Usage:
  python install_wiki.py --source-repo /path/to/clone
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from lib.paths import CURSOR_HOME, DEFAULT_WIKI_HOME, INSTALL_VERSION
from scripts.find_python import find_python, write_env

RULE_NAMES = [
    "context-wiki.mdc",
    "context-wiki-drain.mdc",
    "decision-capture.mdc",
]

WIKI_HOOK_PS1 = {
    "sessionStart": {
        "command": 'powershell -ExecutionPolicy Bypass -File "{hooks}/wiki-on-start.ps1"',
        "timeout": 120,
    },
    "beforeSubmitPrompt": {
        "command": 'powershell -ExecutionPolicy Bypass -File "{hooks}/inject-wiki-drain.ps1"',
        "matcher": "UserPromptSubmit",
        "timeout": 15,
    },
}

WIKI_HOOK_SH = {
    "sessionStart": {
        "command": 'bash "{hooks}/wiki-on-start.sh"',
        "timeout": 120,
    },
    "beforeSubmitPrompt": {
        "command": 'bash "{hooks}/inject-wiki-drain.sh"',
        "matcher": "UserPromptSubmit",
        "timeout": 15,
    },
}


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_runtime(source: Path, wiki_home: Path) -> None:
    wiki_home.mkdir(parents=True, exist_ok=True)
    preserved: dict[str, str] = {}
    for fname in ("wiki.env", "install.json"):
        p = wiki_home / fname
        if p.exists():
            preserved[fname] = p.read_text(encoding="utf-8")
    for name in ("lib", "scripts", "hooks"):
        _copy_tree(source / name, wiki_home / name)
    for fname, content in preserved.items():
        (wiki_home / fname).write_text(content, encoding="utf-8")


def copy_rules(source: Path) -> None:
    rules_dst = CURSOR_HOME / "rules"
    rules_dst.mkdir(parents=True, exist_ok=True)
    for f in (source / "cursor" / "rules").glob("*.mdc"):
        shutil.copy2(f, rules_dst / f.name)


def copy_skills(source: Path) -> None:
    for skill in ("lint-context", "setup-context-wiki"):
        src = source / "skills" / skill / "SKILL.md"
        if not src.exists():
            continue
        dst_dir = CURSOR_HOME / "skills" / skill
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_dir / "SKILL.md")


def init_context(source: Path) -> None:
    ctx = CURSOR_HOME / "context"
    for sub in ("sessions", "extracts", "synthesis"):
        (ctx / sub).mkdir(parents=True, exist_ok=True)

    templates = source / "templates" / "synthesis"
    if templates.exists():
        for f in templates.glob("*.md"):
            dest = ctx / "synthesis" / f.name
            if not dest.exists():
                shutil.copy2(f, dest)

    cfg = ctx / "wiki_config.json"
    if not cfg.exists():
        example = source / "templates" / "wiki_config.example.json"
        if example.exists():
            shutil.copy2(example, cfg)

    state = ctx / "wiki_state.json"
    if not state.exists():
        state.write_text(
            '{"last_extract":null,"last_synthesis":null,"pending_sessions":[]}\n',
            encoding="utf-8",
        )

    index = ctx / "INDEX.md"
    if not index.exists():
        index.write_text("# Session Index\n\n*No sessions yet.*\n", encoding="utf-8")


def _hook_already_present(entries: list, marker: str) -> bool:
    for e in entries:
        if marker in str(e.get("command", "")):
            return True
    return False


def merge_hooks(wiki_home: Path, use_powershell: bool = True) -> None:
    hooks_file = CURSOR_HOME / "hooks.json"
    template = WIKI_HOOK_PS1 if use_powershell else WIKI_HOOK_SH
    hooks_path = wiki_home / "hooks"

    new_entries = {}
    for event, spec in template.items():
        cmd = spec["command"].format(hooks=hooks_path)
        entry = {"command": cmd, "timeout": spec["timeout"]}
        if "matcher" in spec:
            entry["matcher"] = spec["matcher"]
        new_entries[event] = entry

    if hooks_file.exists():
        data = json.loads(hooks_file.read_text(encoding="utf-8"))
    else:
        data = {"version": 1, "hooks": {}}

    hooks = data.setdefault("hooks", {})
    for event, entry in new_entries.items():
        existing = hooks.get(event, [])
        marker = "wiki-on-start" if event == "sessionStart" else "inject-wiki-drain"
        if _hook_already_present(existing, marker):
            # Update command paths in place for wiki hooks only
            updated = []
            replaced = False
            for e in existing:
                if marker in str(e.get("command", "")):
                    if not replaced:
                        updated.append(entry)
                        replaced = True
                else:
                    updated.append(e)
            if not replaced:
                updated.append(entry)
            hooks[event] = updated
        else:
            hooks[event] = existing + [entry]

    hooks_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_install_json(source: Path, wiki_home: Path) -> None:
    meta = {
        "version": INSTALL_VERSION,
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_repo": str(source.resolve()),
        "wiki_home": str(wiki_home.resolve()),
    }
    (wiki_home / "install.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def install(source: Path, use_powershell: bool = True) -> None:
    source = source.resolve()
    if not (source / "scripts" / "update_wiki.py").exists():
        raise SystemExit(f"Invalid source repo: {source}")

    wiki_home = DEFAULT_WIKI_HOME
    print(f"Installing runtime to {wiki_home}")

    py = find_python()
    if not py:
        raise SystemExit("ERROR: Python 3 not found. Install Python 3 first.")
    write_env(py)
    print(f"Python: {py}")

    copy_runtime(source, wiki_home)
    print("Copied lib/, scripts/, hooks/")

    copy_rules(source)
    print("Copied rules")

    copy_skills(source)
    print("Copied skills")

    init_context(source)
    print(f"Initialized {CURSOR_HOME / 'context'}")

    merge_hooks(wiki_home, use_powershell=use_powershell)
    print(f"Merged hooks into {CURSOR_HOME / 'hooks.json'}")

    write_install_json(source, wiki_home)
    print("Wrote install.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install context wiki to ~/.cursor/wiki/")
    parser.add_argument(
        "--source-repo",
        type=Path,
        default=_REPO,
        help="Path to cloned repository (default: parent of this script)",
    )
    parser.add_argument(
        "--bash-hooks",
        action="store_true",
        help="Use bash hook scripts instead of PowerShell (macOS/Linux)",
    )
    args = parser.parse_args()

    install(args.source_repo.resolve(), use_powershell=not args.bash_hooks)

    # Run doctor from installed location
    import subprocess

    doctor = DEFAULT_WIKI_HOME / "scripts" / "doctor.py"
    py = find_python() or "python"
    cmd = py.split() if " " in py else [py]
    print("\nRunning doctor...")
    r = subprocess.run(cmd + [str(doctor)], cwd=str(DEFAULT_WIKI_HOME))
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
