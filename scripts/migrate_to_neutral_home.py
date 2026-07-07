"""
migrate_to_neutral_home.py -- Move legacy ~/.cursor/wiki + ~/.cursor/context
to the neutral ~/.context-wiki/{runtime,data} home, leaving back-compat
symlinks/junctions at the old locations.

Idempotent. Safe to re-run. Use --dry-run to preview.

Run automatically by install_wiki.py on first install when legacy paths exist
and the neutral home does not. Can also be run manually.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _link(old: Path, new: Path, dry: bool) -> str | None:
    """Create a link/junction at `old` pointing to `new`. Returns note or None."""
    if dry:
        return f"would link {old} -> {new}"
    if old.exists() or old.is_symlink():
        return None  # already something there
    new_parent = old.parent
    new_parent.mkdir(parents=True, exist_ok=True)
    # Try symlink first
    try:
        os.symlink(new, old, target_is_directory=True)
        return f"symlink {old} -> {new}"
    except (OSError, NotImplementedError):
        pass
    # Windows junction fallback (no admin required)
    if sys.platform.startswith("win"):
        try:
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(old), str(new)],
                check=True, capture_output=True,
            )
            return f"junction {old} -> {new}"
        except subprocess.CalledProcessError:
            pass
    return f"WARNING: could not link {old} -> {new} (no symlink/junction privilege). Hooks.json was re-pointed; old path is gone."


def _move(src: Path, dst: Path, dry: bool) -> str:
    if not src.exists():
        return f"skip (no {src})"
    if dst.exists():
        return f"skip ({dst} already exists)"
    if dry:
        return f"would move {src} -> {dst}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return f"moved {src} -> {dst}"


def _repoint_cursor_hooks(new_runtime: Path, dry: bool) -> str:
    """Update ~/.cursor/hooks.json wiki hook commands to the neutral runtime."""
    hooks_file = Path.home() / ".cursor" / "hooks.json"
    if not hooks_file.exists():
        return "skip (no ~/.cursor/hooks.json)"
    try:
        data = json.loads(hooks_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "skip (invalid hooks.json)"
    new_hooks_dir = new_runtime / "hooks"
    changed = False
    hooks = data.get("hooks", data)
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        for e in entries:
            cmd = str(e.get("command", ""))
            if "wiki-on-start" in cmd or "inject-wiki-drain" in cmd:
                # Replace the path component between hooks/ and the script name
                # Conservative: rewrite to use the new hooks dir with the same script + args
                if "wiki-on-start.ps1" in cmd:
                    e["command"] = f'powershell -ExecutionPolicy Bypass -File "{new_hooks_dir / "wiki-on-start.ps1"}"'
                    changed = True
                elif "wiki-on-start.sh" in cmd:
                    e["command"] = f'bash "{new_hooks_dir / "wiki-on-start.sh"}"'
                    changed = True
                elif "inject-wiki-drain.ps1" in cmd:
                    e["command"] = f'powershell -ExecutionPolicy Bypass -File "{new_hooks_dir / "inject-wiki-drain.ps1"}"'
                    changed = True
                elif "inject-wiki-drain.sh" in cmd:
                    e["command"] = f'bash "{new_hooks_dir / "inject-wiki-drain.sh"}"'
                    changed = True
    if changed and not dry:
        hooks_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return f"repointed wiki hook paths -> {new_hooks_dir}" if changed else "no wiki hooks to repoint"


def migrate(dry: bool = False) -> dict:
    home = Path.home()
    neutral = home / ".context-wiki"
    runtime = neutral / "runtime"
    data = neutral / "data"
    legacy_wiki = home / ".cursor" / "wiki"
    legacy_context = home / ".cursor" / "context"

    result = {"dry_run": dry, "steps": []}

    if not legacy_wiki.exists() and not legacy_context.exists():
        result["steps"].append("nothing to migrate (no legacy ~/.cursor/wiki or ~/.cursor/context)")
        return result

    # If neutral already exists, we still re-point hooks but do not move.
    result["steps"].append(_move(legacy_wiki, runtime, dry))
    if not (runtime.exists() or dry):
        runtime.mkdir(parents=True, exist_ok=True)
    result["steps"].append(_move(legacy_context, data, dry))
    if not (data.exists() or dry):
        data.mkdir(parents=True, exist_ok=True)

    # Back-compat links at old locations
    link_note_wiki = _link(legacy_wiki, runtime, dry)
    if link_note_wiki:
        result["steps"].append(link_note_wiki)
    link_note_ctx = _link(legacy_context, data, dry)
    if link_note_ctx:
        result["steps"].append(link_note_ctx)

    # Re-point ~/.cursor/hooks.json to the neutral runtime hooks
    result["steps"].append(_repoint_cursor_hooks(runtime, dry))

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy ~/.cursor wiki home to ~/.context-wiki")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changing anything")
    args = parser.parse_args()

    result = migrate(dry=args.dry_run)
    print(f"Migration (dry_run={result['dry_run']}):")
    for s in result["steps"]:
        print(f"  - {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
