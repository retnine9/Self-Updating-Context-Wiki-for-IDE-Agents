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
    """Load ~/.cursor/wiki/wiki.env into process environment if present."""
    if not WIKI_ENV_FILE.exists():
        return
    for line in WIKI_ENV_FILE.read_text(encoding="utf-8").splitlines():
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
    2. ~/.cursor/wiki/ if install.json exists
    3. REPO_ROOT (dev / examples from clone)
    """
    if os.environ.get("WIKI_HOME"):
        return Path(os.environ["WIKI_HOME"]).resolve()
    if INSTALL_JSON.exists():
        return DEFAULT_WIKI_HOME.resolve()
    return REPO_ROOT.resolve()


load_wiki_env()
WIKI_HOME = resolve_wiki_home()

# Context wiki data directory (sessions, extracts, synthesis)
CONTEXT_DIR = Path(
    os.environ.get("CONTEXT_WIKI_DIR", CURSOR_HOME / "context")
).resolve()

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

# Agent transcript source (Layer 1 input)
_project_slug = os.environ.get("CURSOR_PROJECT_SLUG", "")
if _project_slug:
    TRANSCRIPTS_DIR = CURSOR_HOME / "projects" / _project_slug / "agent-transcripts"
else:
    _projects = CURSOR_HOME / "projects"
    TRANSCRIPTS_DIR = Path(
        os.environ.get(
            "TRANSCRIPTS_DIR",
            str(_projects / "default" / "agent-transcripts"),
        )
    )
    if _projects.exists():
        candidates = sorted(
            (p / "agent-transcripts" for p in _projects.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )
        for c in candidates:
            if c.exists() and any(c.iterdir()):
                TRANSCRIPTS_DIR = c
                break

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
