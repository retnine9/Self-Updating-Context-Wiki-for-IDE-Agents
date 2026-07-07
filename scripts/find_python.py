"""
find_python.py -- Locate a usable Python for context wiki hooks.

Usage:
  python find_python.py              # Print path to stdout
  python find_python.py --write-env  # Write ~/.cursor/wiki/wiki.env
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from lib.paths import CURSOR_HOME, WIKI_ENV_FILE


def _try_run(cmd: list[str]) -> bool:
    try:
        r = subprocess.run(
            cmd + ["-c", "import sys; print(sys.version_info.major)"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0 and r.stdout.strip() in ("3", "3\n")
    except (OSError, subprocess.TimeoutExpired):
        return False


def find_python() -> str | None:
    candidates: list[list[str]] = []

    if sys.platform == "win32":
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "Python"
        if local.exists():
            for p in sorted(local.glob("pythoncore-*/python.exe"), reverse=True):
                candidates.append([str(p)])
        for name in ("python3.exe", "python.exe"):
            p = shutil.which(name)
            if p:
                candidates.append([p])
        candidates.append(["py", "-3"])
    else:
        for name in ("python3", "python"):
            p = shutil.which(name)
            if p:
                candidates.append([p])

    seen = set()
    for cmd in candidates:
        key = tuple(cmd)
        if key in seen:
            continue
        seen.add(key)
        if _try_run(cmd):
            return cmd[0] if len(cmd) == 1 else " ".join(cmd)
    return None


def write_env(python_cmd: str) -> Path:
    WIKI_ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    wiki_home = CURSOR_HOME / "wiki"
    lines = [
        f"WIKI_PYTHON={python_cmd}",
        f"WIKI_HOME={wiki_home}",
        f"CONTEXT_WIKI_DIR={CURSOR_HOME / 'context'}",
    ]
    WIKI_ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return WIKI_ENV_FILE


def main() -> int:
    parser = argparse.ArgumentParser(description="Find Python for context wiki")
    parser.add_argument("--write-env", action="store_true", help="Write ~/.cursor/wiki/wiki.env")
    args = parser.parse_args()

    found = find_python()
    if not found:
        print("ERROR: No Python 3 found. Install Python 3 and retry.", file=sys.stderr)
        return 1

    print(found)
    if args.write_env:
        path = write_env(found)
        print(f"Wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
