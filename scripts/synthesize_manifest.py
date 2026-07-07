"""
synthesize_manifest.py -- Layer 2+3 manifest builder for agent-driven synthesis.

The IDE agent reads the manifest JSON and uses its LLM to write extracts and
update synthesis wiki files. No external API keys required.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from lib.paths import EXTRACTS_DIR, EXTRACT_SECTIONS, SESSIONS_DIR, SYNTHESIS_DIR, SYNTHESIS_FILES

SYNTHESIS_PROMPT = """Read this session transcript and extract, using only what is explicitly stated:

1. **Decisions** -- key choices made and the stated reasoning
2. **Errors** -- every error/failure encountered, its root cause if identified, and the resolution
3. **Rejected approaches** -- things tried and abandoned, and why
4. **Constraints identified** -- any invariant, rule, or "never do X" that emerged
5. **Technical debt noted** -- known shortcuts flagged for later
6. **Open questions** -- things discussed but not resolved
7. **One-sentence summary** -- what this session was fundamentally about

Cite nothing that isn't in the transcript. Use the section headings exactly as listed. Be concise -- aim for 300-500 words total.

Session transcript:

---
{session_content}
---

Write the structured extract now. Start directly with "## Decisions" (or "## Decisions\\n_(none)_" if none). Include all 7 sections."""

LAYER3_INSTRUCTIONS = {
    "CAUSAL_MAP.md": (
        "Linked problems, bugs, and decisions with root causes. "
        "Add new chains from new extracts; update recurrence counts. Preserve existing entries."
    ),
    "ERROR_REFERENCE.md": (
        "Error signatures, causes, and fixes grouped by subsystem. "
        "Add new patterns; mark resolved errors. Do not remove resolved entries."
    ),
    "OPEN_QUESTIONS.md": (
        "Unresolved items with status (open / partially-resolved / resolved). "
        "Mark resolved questions; add new ones from extracts."
    ),
    "RULES_DRAFT.md": (
        "Constraints discovered through failure. Tag [DRAFT] or [INSTALLED]."
    ),
    "SKILLS_DRAFT.md": (
        "Repeatable workflows that worked. Tag [DRAFT] or [INSTALLED]."
    ),
    "DEVELOPMENT_HISTORY.md": (
        "Chronological major architectural decisions only. Append new entries; omit minor tweaks."
    ),
}


def extract_uuid8(session_path: Path) -> str:
    return session_path.stem.rsplit("_", 1)[-1]


def extract_date_str(session_path: Path) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", session_path.stem)
    return match.group(1) if match else "0000-00-00"


def get_extract_path(session_path: Path) -> Path:
    return EXTRACTS_DIR / f"{extract_date_str(session_path)}_{extract_uuid8(session_path)}_extract.md"


def is_synthesized(session_path: Path) -> bool:
    return get_extract_path(session_path).exists()


def read_session(session_path: Path) -> str:
    content = session_path.read_text(encoding="utf-8")
    if len(content.encode("utf-8")) > 200_000:
        content = content[:180_000] + "\n\n[...session truncated for synthesis]"
    return content


def find_pending_sessions(uuid8_list: list[str] | None = None) -> list[Path]:
    """Sessions missing extracts. If uuid8_list given, filter to those."""
    if not SESSIONS_DIR.exists():
        return []
    all_sessions = sorted(SESSIONS_DIR.glob("*.md"), key=lambda p: p.name)
    pending = [s for s in all_sessions if not is_synthesized(s)]
    if uuid8_list:
        allowed = set(uuid8_list)
        pending = [s for s in pending if extract_uuid8(s) in allowed]
    return pending


def build_layer2_batches(sessions: list[Path], batch_size: int = 10) -> list[dict]:
    batches = []
    for i in range(0, len(sessions), batch_size):
        batch = sessions[i : i + batch_size]
        entries = []
        for session_path in batch:
            entries.append({
                "session_path": str(session_path),
                "extract_path": str(get_extract_path(session_path)),
                "uuid8": extract_uuid8(session_path),
                "date": extract_date_str(session_path),
                "prompt": SYNTHESIS_PROMPT.format(session_content=read_session(session_path)),
            })
        batches.append({"batch_index": len(batches), "sessions": entries})
    return batches


def build_full_manifest(
    pending_sessions: list[Path],
    batch_size: int = 10,
) -> dict:
    return {
        "layer2_batches": build_layer2_batches(pending_sessions, batch_size),
        "layer2_template_sections": EXTRACT_SECTIONS,
        "layer3_files": [
            {
                "filename": name,
                "path": str(SYNTHESIS_DIR / name),
                "instruction": LAYER3_INSTRUCTIONS[name],
            }
            for name in SYNTHESIS_FILES
        ],
        "layer3_instruction": (
            "After Layer 2 extracts are written, read each new extract and update all "
            "six synthesis files in-place. Output complete replacement files. "
            "Preserve existing content unless new extracts supersede it. "
            "Prefer newer extract over older when contradictions arise."
        ),
        "pending_count": len(pending_sessions),
    }
