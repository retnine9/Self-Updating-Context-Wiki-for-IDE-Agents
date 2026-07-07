"""Portable path resolution for the context wiki."""

from __future__ import annotations

import json
import os
from pathlib import Path

# Repo root when running from clone (parent of lib/)
REPO_ROOT = Path(__file__).resolve().parent.parent

CURSOR_HOME = Path(os.environ.get("CURSOR_HOME", Path.home() / ".cursor"))
DEFAULT_WIKI_HOME = CURSOR_HOME / "wiki"
INSTALL_JSON = DEFAULT_WIKI_HOME / "install.json"
WIKI_ENV_FILE = DEFAULT_WIKI_HOME / "wiki.env"


def load_wiki_env() -> None:
    """Load wiki.env into process environment if present.

    Reads the neutral runtime home first, then the legacy Cursor wiki home, so
    installs on Claude/Codex (runtime at ~/.context-wiki/runtime/) and legacy
    Cursor installs (runtime at ~/.cursor/wiki/) both work.
    """
    neutral_env = Path.home() / ".context-wiki" / "runtime" / "wiki.env"
    legacy_env = WIKI_ENV_FILE  # ~/.cursor/wiki/wiki.env
    for env_file in (neutral_env, legacy_env):
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def resolve_wiki_home() -> Path:
    """
    Runtime home for scripts and hooks.
    1. WIKI_HOME env
    2. Neutral ~/.context-wiki/runtime/ if install.json exists (Claude/Codex)
    3. ~/.cursor/wiki/ if install.json exists (legacy Cursor)
    4. REPO_ROOT (dev / examples from clone)
    """
    if os.environ.get("WIKI_HOME"):
        return Path(os.environ["WIKI_HOME"]).resolve()
    neutral = Path.home() / ".context-wiki" / "runtime"
    if (neutral / "install.json").exists():
        return neutral.resolve()
    if INSTALL_JSON.exists():
        return DEFAULT_WIKI_HOME.resolve()
    return REPO_ROOT.resolve()


def _resolve_context_dir() -> Path:
    """Resolve the wiki data directory with back-compat for legacy Cursor installs.

    Priority:
      1. CONTEXT_WIKI_DIR env
      2. ~/.context-wiki/data (neutral — Claude/Codex installs, post-migration)
      3. ~/.cursor/context (legacy Cursor — pre-migration)
      4. ~/.context-wiki/data (default for fresh installs)
    """
    env = os.environ.get("CONTEXT_WIKI_DIR", "").strip()
    if env:
        return Path(env).resolve()
    neutral = Path.home() / ".context-wiki" / "data"
    legacy = CURSOR_HOME / "context"
    if neutral.exists():
        return neutral.resolve()
    if legacy.exists():
        return legacy.resolve()
    return neutral.resolve()


load_wiki_env()
WIKI_HOME = resolve_wiki_home()

# Context wiki data directory (sessions, extracts, synthesis)
CONTEXT_DIR = _resolve_context_dir()

SESSIONS_DIR = CONTEXT_DIR / "sessions"
EXTRACTS_DIR = CONTEXT_DIR / "extracts"
SYNTHESIS_DIR = CONTEXT_DIR / "synthesis"
INDEX_FILE = CONTEXT_DIR / "INDEX.md"
WIKI_STATE_FILE = CONTEXT_DIR / "wiki_state.json"
WIKI_CONFIG_FILE = CONTEXT_DIR / "wiki_config.json"
DRAIN_FLAG_FILE = CONTEXT_DIR / ".drain_required.json"
SKIP_FLAG_FILE = CONTEXT_DIR / ".wiki_skip"
DRAIN_INJECTED_FILE = CONTEXT_DIR / ".drain_injected"
LOG_FILE = CONTEXT_DIR / "wiki.log"


def _resolve_transcripts_dir() -> Path:
    """Delegate transcript dir resolution to the active platform adapter.

    Honors TRANSCRIPTS_DIR env override (all platforms) and CURSOR_PROJECT_SLUG
    (Cursor) via the adapter. Falls back to the legacy Cursor default if the
    platform layer is unavailable (e.g. during early import)."""
    try:
        from lib.platform import get_platform
        return get_platform().resolve_transcripts_dir()
    except Exception:
        # Legacy fallback — Cursor default
        slug = os.environ.get("CURSOR_PROJECT_SLUG", "")
        if slug:
            return CURSOR_HOME / "projects" / slug / "agent-transcripts"
        return Path(
            os.environ.get(
                "TRANSCRIPTS_DIR",
                str(CURSOR_HOME / "projects" / "default" / "agent-transcripts"),
            )
        )


TRANSCRIPTS_DIR = _resolve_transcripts_dir()

SCRIPTS_DIR = WIKI_HOME / "scripts"
HOOKS_DIR = WIKI_HOME / "hooks"

SYNTHESIS_FILES = [
    "CAUSAL_MAP.md",
    "ERROR_REFERENCE.md",
    "OPEN_QUESTIONS.md",
    "RULES_DRAFT.md",
    "SKILLS_DRAFT.md",
    "DEVELOPMENT_HISTORY.md",
]

EXTRACT_SECTIONS = [
    "## Decisions",
    "## Errors",
    "## Rejected approaches",
    "## Constraints identified",
    "## Technical debt noted",
    "## Open questions",
    "## Summary",
]

INSTALL_VERSION = 1


def read_install_meta() -> dict:
    if not INSTALL_JSON.exists():
        return {}
    try:
        return json.loads(INSTALL_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
