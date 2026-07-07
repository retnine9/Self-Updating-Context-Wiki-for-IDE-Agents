"""Cursor platform adapter — reference implementation; do not break."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from .base import Platform, SessionRef


class CursorPlatform:
    name = "cursor"

    def __init__(self) -> None:
        self.cursor_home = Path(os.environ.get("CURSOR_HOME", Path.home() / ".cursor"))

    def resolve_transcripts_dir(self) -> Path:
        slug = os.environ.get("CURSOR_PROJECT_SLUG", "")
        if slug:
            return self.cursor_home / "projects" / slug / "agent-transcripts"
        override = os.environ.get("TRANSCRIPTS_DIR", "")
        projects = self.cursor_home / "projects"
        if override:
            return Path(override)
        default = projects / "default" / "agent-transcripts"
        if projects.exists():
            candidates = sorted(
                (p / "agent-transcripts" for p in projects.iterdir() if p.is_dir()),
                key=lambda p: p.stat().st_mtime if p.exists() else 0,
                reverse=True,
            )
            for c in candidates:
                if c.exists() and any(c.iterdir()):
                    return c
        return default

    def discover_sessions(self) -> list[SessionRef]:
        root = self.resolve_transcripts_dir()
        if not root.exists():
            return []
        refs: list[SessionRef] = []
        for d in sorted(
            [p for p in root.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
        ):
            uuid = d.name
            main = d / f"{uuid}.jsonl"
            if not main.exists():
                continue
            subs = sorted((d / "subagents").glob("*.jsonl")) if (d / "subagents").exists() else []
            refs.append(SessionRef(uuid=uuid, main_jsonl=main, subagent_jsonls=subs,
                                   mtime=main.stat().st_mtime))
        return refs

    def find_session(self, uuid_prefix: str) -> SessionRef | None:
        for ref in self.discover_sessions():
            if ref.uuid.startswith(uuid_prefix):
                return ref
        return None

    def hook_config_paths(self) -> list[Path]:
        return [self.cursor_home / "hooks.json"]

    def rules_install_dir(self) -> Path:
        return self.cursor_home / "rules"

    def skills_install_dir(self) -> Path | None:
        return self.cursor_home / "skills"

    def drain_output_format(self) -> str:
        return "agent_message"

    def default_synthesis_model(self) -> str:
        return "claude-4.5-haiku-thinking"

    def hook_event_names(self) -> tuple[str, str]:
        return ("sessionStart", "beforeSubmitPrompt")

    def read_hook_stdin_transcript_path(self, stdin_json: dict | None) -> Path | None:
        return None
