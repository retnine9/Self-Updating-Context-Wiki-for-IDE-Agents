"""
install_wiki.py -- Install context wiki runtime per platform.

Usage:
  python install_wiki.py --source-repo /path/to/clone [--platform cursor|claude|codex]

Default platform is auto-detected (Cursor if ~/.cursor/projects exists, else
Claude if ~/.claude/projects exists, else Codex if ~/.codex/sessions exists,
else Cursor).
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

from lib.paths import INSTALL_VERSION
from scripts.find_python import find_python, write_env

RULE_NAMES = [
    "context-wiki.mdc",
    "context-wiki-drain.mdc",
    "decision-capture.mdc",
]

# --- Cursor hook templates (flat ~/.cursor/hooks.json shape) ---
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


def _wiki_home_for(platform: str) -> Path:
    # All platforms use the neutral runtime home. Legacy ~/.cursor/wiki is
    # migrated to the neutral home on first install (see install()).
    return Path.home() / ".context-wiki" / "runtime"


def _context_dir_for(platform: str) -> Path:
    # All platforms share the neutral data home. Legacy ~/.cursor/context is
    # migrated on first install.
    return Path.home() / ".context-wiki" / "data"


def _rules_install_dir(platform: str) -> Path:
    home = Path.home()
    if platform == "cursor":
        return home / ".cursor" / "rules"
    if platform == "claude":
        return home / ".claude" / "agents"
    if platform == "codex":
        return home / ".codex" / "agents"
    raise ValueError(platform)


def _skills_install_dir(platform: str) -> Path | None:
    if platform == "cursor":
        return Path.home() / ".cursor" / "skills"
    return None


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


def copy_cursor_rules(source: Path, rules_dst: Path) -> None:
    rules_dst.mkdir(parents=True, exist_ok=True)
    for f in (source / "cursor" / "rules").glob("*.mdc"):
        shutil.copy2(f, rules_dst / f.name)


def copy_skills(source: Path, skills_dst: Path) -> None:
    for skill in ("lint-context", "setup-context-wiki"):
        src = source / "skills" / skill / "SKILL.md"
        if not src.exists():
            continue
        dst_dir = skills_dst / skill
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_dir / "SKILL.md")


def copy_platform_adapters(source: Path, platform: str, rules_dst: Path) -> None:
    """Copy CLAUDE.md / AGENTS.md snippets and subagent definitions."""
    adapter_dir = source / "adapters" / platform
    if not adapter_dir.exists():
        return
    rules_dst.mkdir(parents=True, exist_ok=True)
    # Subagent definitions live under adapters/<platform>/agents/
    agents_src = adapter_dir / "agents"
    if agents_src.exists():
        for f in agents_src.iterdir():
            if f.is_file():
                shutil.copy2(f, rules_dst / f.name)
    # Top-level snippet (CLAUDE.md / AGENTS.md) -> copied next to agents dir
    for snippet in ("CLAUDE.md", "AGENTS.md"):
        s = adapter_dir / snippet
        if s.exists():
            shutil.copy2(s, rules_dst.parent / snippet)


def init_context(source: Path, ctx: Path) -> None:
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


# --- Cursor hooks.json merge (flat shape) ---
def merge_cursor_hooks(wiki_home: Path, use_powershell: bool = True) -> None:
    hooks_file = Path.home() / ".cursor" / "hooks.json"
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


# --- Claude / Codex hooks merge (nested {hooks:{Event:[{matcher,hooks:[...]}]}}) ---
def _python_command(wiki_home: Path, script: str, on_windows: bool) -> str:
    py = "python" if on_windows else "python3"
    return f'{py} "{wiki_home / "hooks" / script}"'


def merge_nested_hooks(
    config_file: Path,
    wiki_home: Path,
    session_event: str,
    drain_event: str,
    on_windows: bool,
) -> None:
    """Merge wiki hooks into a Claude settings.json or Codex hooks.json.

    Both use the nested shape:
      { "hooks": { "<Event>": [ { "matcher": ..., "hooks": [ {type,command,timeout} ] } ] } }
    """
    start_cmd = _python_command(wiki_home, "wiki_on_start.py", on_windows)
    drain_cmd = _python_command(wiki_home, "inject_wiki_drain.py", on_windows)

    start_entry = {
        "matcher": "startup|resume|clear|compact",
        "hooks": [{"type": "command", "command": start_cmd, "timeout": 120}],
    }
    drain_entry = {
        "matcher": "*",
        "hooks": [{"type": "command", "command": drain_cmd, "timeout": 30}],
    }

    if config_file.exists():
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}

    # Claude stores hooks under top-level "hooks"; Codex too. Preserve other keys.
    hooks = data.setdefault("hooks", {})

    def _replace_or_append(event: str, new_entry: dict, marker: str) -> None:
        existing = hooks.get(event, [])
        # De-dup by marker in command string
        for block in existing:
            for h in block.get("hooks", []):
                if marker in str(h.get("command", "")):
                    h["command"] = new_entry["hooks"][0]["command"]
                    h["timeout"] = new_entry["hooks"][0]["timeout"]
                    return
        hooks[event] = existing + [new_entry]

    _replace_or_append(session_event, start_entry, "wiki_on_start.py")
    _replace_or_append(drain_event, drain_entry, "inject_wiki_drain.py")

    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_install_json(source: Path, wiki_home: Path, platform: str) -> None:
    meta = {
        "version": INSTALL_VERSION,
        "platform": platform,
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_repo": str(source.resolve()),
        "wiki_home": str(wiki_home.resolve()),
    }
    (wiki_home / "install.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def write_wiki_env(wiki_home: Path, py: str, platform: str, ctx: Path) -> None:
    env_file = wiki_home / "wiki.env"
    lines = [
        f'WIKI_PYTHON="{py}"',
        f'WIKI_PLATFORM="{platform}"',
        f'WIKI_HOME="{wiki_home}"',
        f'CONTEXT_WIKI_DIR="{ctx}"',
    ]
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def install(source: Path, platform: str, use_powershell: bool = True) -> Path:
    source = source.resolve()
    if not (source / "scripts" / "update_wiki.py").exists():
        raise SystemExit(f"Invalid source repo: {source}")

    wiki_home = _wiki_home_for(platform)
    ctx = _context_dir_for(platform)

    # Auto-migrate legacy Cursor home into the neutral home on first install
    # (preserves existing sessions/synthesis and re-points ~/.cursor/hooks.json).
    from scripts.migrate_to_neutral_home import migrate
    home = Path.home()
    legacy_wiki = home / ".cursor" / "wiki"
    legacy_context = home / ".cursor" / "context"
    if (legacy_wiki.exists() or legacy_context.exists()) and not wiki_home.parent.exists():
        print("Migrating legacy ~/.cursor wiki home -> ~/.context-wiki ...")
        migrate(dry=False)

    print(f"Installing platform={platform} runtime to {wiki_home}")
    print(f"Wiki data dir: {ctx}")

    py = find_python()
    if not py:
        raise SystemExit("ERROR: Python 3 not found. Install Python 3 first.")
    print(f"Python: {py}")

    copy_runtime(source, wiki_home)
    print("Copied lib/, scripts/, hooks/")

    rules_dst = _rules_install_dir(platform)
    if platform == "cursor":
        copy_cursor_rules(source, rules_dst)
        print(f"Copied rules -> {rules_dst}")
    else:
        copy_platform_adapters(source, platform, rules_dst)
        print(f"Copied platform adapter -> {rules_dst}")

    skills_dst = _skills_install_dir(platform)
    if skills_dst is not None:
        copy_skills(source, skills_dst)
        print(f"Copied skills -> {skills_dst}")

    init_context(source, ctx)
    print(f"Initialized {ctx}")

    if platform == "cursor":
        merge_cursor_hooks(wiki_home, use_powershell=use_powershell)
        print(f"Merged hooks into ~/.cursor/hooks.json")
    elif platform == "claude":
        on_windows = sys.platform.startswith("win")
        merge_nested_hooks(
            Path.home() / ".claude" / "settings.json",
            wiki_home, "SessionStart", "UserPromptSubmit", on_windows,
        )
        print("Merged hooks into ~/.claude/settings.json")
    elif platform == "codex":
        on_windows = sys.platform.startswith("win")
        merge_nested_hooks(
            Path.home() / ".codex" / "hooks.json",
            wiki_home, "SessionStart", "UserPromptSubmit", on_windows,
        )
        print("Merged hooks into ~/.codex/hooks.json")
        print("NOTE: run `/hooks` once in Codex CLI to trust the new hooks.")

    write_wiki_env(wiki_home, py, platform, ctx)
    write_install_json(source, wiki_home, platform)
    print("Wrote wiki.env + install.json")

    # Raise Claude cleanup window so transcripts survive until drain
    if platform == "claude":
        _raise_claude_cleanup()
    return wiki_home


def _raise_claude_cleanup() -> None:
    settings = Path.home() / ".claude" / "settings.json"
    try:
        data = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    except json.JSONDecodeError:
        data = {}
    current = data.get("cleanupPeriodDays")
    if current is None or (isinstance(current, int) and current < 90):
        data["cleanupPeriodDays"] = 90
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("Raised ~/.claude/settings.json cleanupPeriodDays to 90")


def _auto_detect_platform() -> str:
    import os
    p = os.environ.get("WIKI_PLATFORM", "").strip().lower()
    if p in ("cursor", "claude", "codex"):
        return p
    home = Path.home()
    if (home / ".cursor" / "projects").exists():
        return "cursor"
    if (home / ".claude" / "projects").exists():
        return "claude"
    if (home / ".codex" / "sessions").exists():
        return "codex"
    return "cursor"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install context wiki per platform")
    parser.add_argument(
        "--source-repo",
        type=Path,
        default=_REPO,
        help="Path to cloned repository (default: parent of this script)",
    )
    parser.add_argument(
        "--platform",
        choices=("cursor", "claude", "codex"),
        default=None,
        help="Target platform (default: auto-detect)",
    )
    parser.add_argument(
        "--bash-hooks",
        action="store_true",
        help="Cursor only: use bash hook scripts instead of PowerShell",
    )
    args = parser.parse_args()

    platform = args.platform or _auto_detect_platform()
    wiki_home = install(
        args.source_repo.resolve(),
        platform=platform,
        use_powershell=not args.bash_hooks,
    )

    import subprocess
    doctor = wiki_home / "scripts" / "doctor.py"
    py = find_python() or "python"
    cmd = py.split() if " " in py else [py]
    print("\nRunning doctor...")
    r = subprocess.run(cmd + [str(doctor), "--platform", platform], cwd=str(wiki_home))
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
