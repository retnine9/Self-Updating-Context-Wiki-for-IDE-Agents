"""Unified session-start hook for all platforms.

Runs update_wiki.py --all (Layer 1 extract + prepare). Honors .wiki_skip.
Always prints `{}` (Cursor) / no special JSON (Claude/Codex accept plain
stdout; emitting `{}` is harmless).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wiki_common  # noqa: E402

sys.path.insert(0, str(wiki_common.REPO_ROOT))
from lib.platform import get_platform  # noqa: E402


def main() -> int:
    wiki_common.load_wiki_env()
    wiki_home = wiki_common.resolve_wiki_home()
    ctx = wiki_common.resolve_context_dir()
    skip_file = ctx / ".wiki_skip"

    if skip_file.exists():
        wiki_common.log("sessionStart skipped (.wiki_skip exists)")
        try:
            skip_file.unlink()
        except OSError:
            pass
        print("{}")
        return 0

    os.environ["CONTEXT_WIKI_DIR"] = str(ctx)
    os.environ["WIKI_HOME"] = str(wiki_home)
    try:
        platform = get_platform()
        os.environ.setdefault("WIKI_PLATFORM", platform.name)
    except Exception:
        pass

    py = wiki_common.find_python()
    cmd = py.split() + [str(wiki_home / "scripts" / "update_wiki.py"), "--all"]
    wiki_common.log(f"sessionStart: update_wiki.py --all (wiki={wiki_home})")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.stderr:
            wiki_common.log(f"sessionStart stderr: {proc.stderr.strip()[:500]}")
    except Exception as e:  # noqa: BLE001
        wiki_common.log(f"sessionStart ERROR: {e}")

    print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
