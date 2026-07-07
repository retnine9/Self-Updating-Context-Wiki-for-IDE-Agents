"""Portable path resolution for the context wiki."""

from __future__ import annotations

import os
from pathlib import Path

# Repo root (parent of lib/)
REPO_ROOT = Path(__file__).resolve().parent.parent

CURSOR_HOME = Path(os.environ.get("CURSOR_HOME", Path.home() / ".cursor"))

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
LOG_FILE = CONTEXT_DIR / "wiki.log"

# Agent transcript source (Layer 1 input)
_project_slug = os.environ.get("CURSOR_PROJECT_SLUG", "")
if _project_slug:
    TRANSCRIPTS_DIR = CURSOR_HOME / "projects" / _project_slug / "agent-transcripts"
else:
    # Auto-discover: use most recently modified project with agent-transcripts
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

SCRIPTS_DIR = REPO_ROOT / "scripts"
HOOKS_DIR = REPO_ROOT / "hooks"

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
