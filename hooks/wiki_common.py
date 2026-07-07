"""Shared helpers for Python wiki hooks (all platforms).

Resolves WIKI_HOME and CONTEXT_DIR the same way the shell hooks do:
  1. ~/.context-wiki/runtime/wiki.env (or legacy ~/.cursor/wiki/wiki.env)
  2. WIKI_HOME / CONTEXT_WIKI_DIR env if already set
  3. install.json presence at the neutral or legacy runtime home
  4. dev fallback: repo root (parent of hooks/)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent
HOME = Path.home()

NEUTRAL_RUNTIME = HOME / ".context-wiki" / "runtime"
LEGACY_CURSOR_WIKI = HOME / ".cursor" / "wiki"


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load_wiki_env() -> dict[str, str]:
    for env_file in (NEUTRAL_RUNTIME / "wiki.env", LEGACY_CURSOR_WIKI / "wiki.env"):
        parsed = _parse_env_file(env_file)
        for k, v in parsed.items():
            os.environ.setdefault(k, v)
        if parsed:
            return parsed
    return {}


def resolve_wiki_home() -> Path:
    if os.environ.get("WIKI_HOME"):
        return Path(os.environ["WIKI_HOME"])
    for cand in (NEUTRAL_RUNTIME, LEGACY_CURSOR_WIKI):
        if (cand / "install.json").exists():
            return cand
    # dev fallback: hooks/ -> repo root
    return REPO_ROOT


def resolve_context_dir() -> Path:
    if os.environ.get("CONTEXT_WIKI_DIR"):
        return Path(os.environ["CONTEXT_WIKI_DIR"])
    # Match lib/paths default for the active platform
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from lib.paths import CONTEXT_DIR  # noqa: F401
        from lib import paths  # noqa: F401
        return paths.CONTEXT_DIR
    except Exception:
        return LEGACY_CURSOR_WIKI.parent / "context"


def find_python() -> str:
    p = os.environ.get("WIKI_PYTHON")
    if p:
        return p
    import shutil
    for cmd in ("python3", "python", "py"):
        if shutil.which(cmd):
            return "py -3" if cmd == "py" else cmd
    return "python"


def log(msg: str) -> None:
    ctx = resolve_context_dir()
    try:
        ctx.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        with open(ctx / "wiki.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] hook: {msg}\n")
    except OSError:
        pass
