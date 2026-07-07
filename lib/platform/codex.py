"""Codex CLI platform adapter.

Transcripts: transcript_path from hook stdin JSON, or ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl
Hooks: ~/.codex/hooks.json (nested {hooks:{Event:[{matcher,hooks:[...]}]}}).
Drain inject: UserPromptSubmit -> hookSpecificOutput.additionalContext.
"""
from __future__ import annotations

import os
from pathlib import Path

from .base import Platform, SessionRef


class CodexPlatform:
    name = "codex"

    def __init__(self) -> None:
        self.codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))

    def resolve_transcripts_dir(self) -> Path:
        override = os.environ.get("TRANSCRIPTS_DIR", "")
        if override:
            return Path(override)
        return self.codex_home / "sessions"

    def discover_sessions(self) -> list[SessionRef]:
        root = self.resolve_transcripts_dir()
        if not root.exists():
            return []
        refs: list[SessionRef] = []
        for f in sorted(root.rglob("rollout-*.jsonl"), key=lambda p: p.stat().st_mtime):
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
        return [self.codex_home / "hooks.json"]

    def rules_install_dir(self) -> Path:
        return self.codex_home / "agents"

    def skills_install_dir(self) -> Path | None:
        return None

    def drain_output_format(self) -> str:
        return "additionalContext"

    def default_synthesis_model(self) -> str:
        return "gpt-5.4-mini"

    def hook_event_names(self) -> tuple[str, str]:
        return ("SessionStart", "UserPromptSubmit")

    def read_hook_stdin_transcript_path(self, stdin_json: dict | None) -> Path | None:
        if stdin_json and stdin_json.get("transcript_path"):
            return Path(stdin_json["transcript_path"])
        return None
