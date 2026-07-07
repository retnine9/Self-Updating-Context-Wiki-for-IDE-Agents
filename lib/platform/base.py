"""Platform Protocol — the contract every IDE/CLI adapter implements."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol


@dataclass
class SessionRef:
    """A discoverable transcript session, platform-agnostic.

    main_jsonl points at the primary transcript file. subagent_jsonls are
    optional (Cursor nests subagents under <uuid>/subagents/; other platforms
    may track them as separate rollout files referenced by parent_thread_id).
    """
    uuid: str
    main_jsonl: Path
    subagent_jsonls: list[Path] = field(default_factory=list)
    mtime: float = 0.0  # epoch seconds; 0 means "derive from main_jsonl"


class Platform(Protocol):
    """Per-platform behavior contract.

    Implementations live in lib/platform/{cursor,claude,codex}.py.
    """

    @property
    def name(self) -> str: ...

    def resolve_transcripts_dir(self) -> Path:
        """Directory to scan for sessions (or where a pinned transcript lives)."""
        ...

    def discover_sessions(self) -> list[SessionRef]:
        """All sessions under resolve_transcripts_dir(), oldest-first."""
        ...

    def find_session(self, uuid_prefix: str) -> SessionRef | None:
        """Locate one session by UUID prefix (for --session)."""
        ...

    def hook_config_paths(self) -> list[Path]:
        """Config files to merge wiki hooks into (highest precedence first)."""
        ...

    def rules_install_dir(self) -> Path: ...
    def skills_install_dir(self) -> Path | None: ...

    def drain_output_format(self) -> str:
        """'agent_message' (Cursor) or 'additionalContext' (Claude/Codex)."""
        ...

    def default_synthesis_model(self) -> str: ...

    def hook_event_names(self) -> tuple[str, str]:
        """(session_start_event, drain_event) for this platform."""
        ...

    def read_hook_stdin_transcript_path(self, stdin_json: dict | None) -> Path | None:
        """Extract transcript_path from hook stdin JSON (Codex); others return None."""
        ...


def session_mtime(ref: SessionRef) -> datetime:
    from datetime import timezone
    if ref.mtime:
        return datetime.fromtimestamp(ref.mtime, tz=timezone.utc)
    if ref.main_jsonl.exists():
        return datetime.fromtimestamp(ref.main_jsonl.stat().st_mtime, tz=timezone.utc)
    return datetime.now(tz=timezone.utc)
