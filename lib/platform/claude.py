"""Claude Code platform adapter.

Transcripts: ~/.claude/projects/<encoded-cwd>/<uuid>.jsonl (flat file).
Hooks: ~/.claude/settings.json + .claude/settings.json under top-level `hooks`.
Drain inject: UserPromptSubmit -> hookSpecificOutput.additionalContext.
"""
from __future__ import annotations

import os
from pathlib import Path

from .base import Platform, SessionRef


def encode_cwd(cwd: str) -> str:
    """/Users/me/proj -> -Users-me-proj ; C:\\Users\\me -> -C-Users-me."""
    s = cwd.replace("/", "-").replace("\\", "-").replace(":", "-")
    return s.lstrip("-")


class ClaudePlatform:
    name = "claude"

    def __init__(self) -> None:
        self.claude_home = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))

    def _project_dir(self) -> Path:
        cwd = os.environ.get("WIKI_PROJECT_CWD", "").strip()
        if cwd:
            return self.claude_home / "projects" / encode_cwd(cwd)
        return self._most_recent_project()

    def _most_recent_project(self) -> Path:
        projects = self.claude_home / "projects"
        if not projects.exists():
            return projects / "default"
        best: Path | None = None
        best_mtime = 0.0
        for p in projects.iterdir():
            if not p.is_dir():
                continue
            try:
                m = max(
                    (f.stat().st_mtime for f in p.glob("*.jsonl")),
                    default=0.0,
                )
            except OSError:
                m = 0.0
            if m > best_mtime:
                best_mtime = m
                best = p
        return best or (projects / "default")

    def resolve_transcripts_dir(self) -> Path:
        override = os.environ.get("TRANSCRIPTS_DIR", "")
        if override:
            return Path(override)
        return self._project_dir()

    def discover_sessions(self) -> list[SessionRef]:
        root = self.resolve_transcripts_dir()
        if not root.exists():
            return []
        refs: list[SessionRef] = []
        for f in sorted(root.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
            # Filename is <uuid>.jsonl (UUID may contain hyphens).
            uuid = f.stem
            refs.append(SessionRef(uuid=uuid, main_jsonl=f, subagent_jsonls=[],
                                   mtime=f.stat().st_mtime))
        return refs

    def find_session(self, uuid_prefix: str) -> SessionRef | None:
        for ref in self.discover_sessions():
            if ref.uuid.startswith(uuid_prefix):
                return ref
        return None

    def hook_config_paths(self) -> list[Path]:
        # User-global then project-local; install merges into the first that
        # exists or is writable. We list user-global as primary.
        return [self.claude_home / "settings.json"]

    def rules_install_dir(self) -> Path:
        return self.claude_home / "agents"

    def skills_install_dir(self) -> Path | None:
        return None

    def drain_output_format(self) -> str:
        return "additionalContext"

    def default_synthesis_model(self) -> str:
        return "claude-haiku-4-5"

    def hook_event_names(self) -> tuple[str, str]:
        return ("SessionStart", "UserPromptSubmit")

    def read_hook_stdin_transcript_path(self, stdin_json: dict | None) -> Path | None:
        return None
