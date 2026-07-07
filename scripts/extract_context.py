"""
extract_context.py -- Layer 1: JSONL -> markdown

Parses agent-transcript sessions into readable markdown files.

Usage:
  python extract_context.py --all       # Process new sessions (skip already-extracted)
  python extract_context.py --session {uuid}
  python extract_context.py --force     # Re-extract everything
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as script from repo root or scripts/
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from lib.paths import CONTEXT_DIR, INDEX_FILE, SESSIONS_DIR, TRANSCRIPTS_DIR

POST30_CUTOFF = datetime(2026, 4, 3, tzinfo=timezone.utc)
TRUNCATE_BYTES = 10_000

XML_WRAPPERS = [
    "user_query",
    "system_reminder",
    "attached_files",
    "open_and_recently_viewed_files",
    "task_notification",
    "rules",
    "agent_skills",
    "agent_transcripts",
    "user_info",
    "system-communication",
    "tone_and_style",
    "tool_calling",
    "making_code_changes",
    "linter_errors",
    "citing_code",
    "inline_line_numbers",
    "terminal_files_information",
    "task_management",
    "mode_selection",
    "available_skills",
    "always_applied_workspace_rules",
    "always_applied_workspace_rule",
]


def get_session_mtime(session_dir: Path) -> datetime:
    main_jsonl = session_dir / f"{session_dir.name}.jsonl"
    if main_jsonl.exists():
        return datetime.fromtimestamp(main_jsonl.stat().st_mtime, tz=timezone.utc)
    return datetime.fromtimestamp(session_dir.stat().st_mtime, tz=timezone.utc)


def strip_xml_wrappers(text: str) -> str:
    for tag in XML_WRAPPERS:
        pattern = rf"<{tag}(?:\s[^>]*)?>[\s]*(.*?)[\s]*</{tag}>"
        text = re.sub(pattern, r"\1", text, flags=re.DOTALL)
        text = re.sub(rf"</?{tag}(?:\s[^>]*)?>", "", text)
    return text.strip()


def maybe_truncate(text: str, label: str = "content") -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= TRUNCATE_BYTES:
        return text
    kb = len(encoded) / 1024
    return f"{text[:500]}\n\n[...truncated {kb:.0f}kb {label}]"


def extract_text_blocks(content: list, role: str, is_post30: bool) -> str:
    parts = []
    for block in content:
        btype = block.get("type", "")
        if btype == "text":
            text = block.get("text", "")
            if role == "user":
                text = strip_xml_wrappers(text)
            if text.strip():
                parts.append(maybe_truncate(text.strip(), "text block"))
        elif btype in ("tool_use", "tool_result") and is_post30:
            pass
        elif btype not in ("text", "tool_use", "tool_result"):
            text = block.get("text", "") or block.get("content", "")
            if isinstance(text, str) and text.strip():
                parts.append(maybe_truncate(text.strip(), "unknown block"))
    return "\n\n".join(parts)


def parse_jsonl(filepath: Path, is_post30: bool) -> list[dict]:
    turns = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = obj.get("role", "unknown")
            message = obj.get("message", {})
            content = message.get("content", [])
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            text = extract_text_blocks(content, role, is_post30)
            if text:
                turns.append({"role": role, "text": text})
    return turns


def slugify(text: str, max_len: int = 40) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:max_len] or "untitled"


def derive_title(turns: list[dict]) -> str:
    for turn in turns:
        if turn["role"] == "user":
            first_line = turn["text"].strip().split("\n")[0].strip()
            if first_line:
                return first_line[:80]
    return "Untitled session"


def build_session_markdown(
    uuid: str,
    date: datetime,
    title: str,
    era: str,
    turns: list[dict],
    subagent_sections: list[str],
) -> str:
    lines = [
        "---",
        f"session: {uuid[:8]}",
        f"date: {date.strftime('%Y-%m-%d')}",
        f"title: {title}",
        f"era: {era}",
        "---",
        "",
    ]
    for turn in turns:
        role_label = "## User" if turn["role"] == "user" else "## Assistant"
        lines.extend([role_label, turn["text"], ""])
    if subagent_sections:
        lines.extend(["---", "", "## Subagents", ""])
        for section in subagent_sections:
            lines.extend([section, ""])
    return "\n".join(lines)


def process_session(session_dir: Path, force: bool = False) -> dict | None:
    uuid = session_dir.name
    main_jsonl = session_dir / f"{uuid}.jsonl"
    if not main_jsonl.exists():
        return None

    mtime = get_session_mtime(session_dir)
    date_str = mtime.strftime("%Y-%m-%d")
    is_post30 = mtime >= POST30_CUTOFF
    era = "post-3.0" if is_post30 else "pre-3.0"

    existing = list(SESSIONS_DIR.glob(f"*_{uuid[:8]}.md"))
    if existing and not force:
        md_path = existing[0]
        with open(md_path, "r", encoding="utf-8") as f:
            header = f.read(500)
        title_match = re.search(r"^title: (.+)$", header, re.MULTILINE)
        title = title_match.group(1) if title_match else "Untitled"
        return {
            "uuid": uuid,
            "uuid8": uuid[:8],
            "date": mtime,
            "date_str": date_str,
            "title": title,
            "path": md_path,
            "skipped": True,
        }

    turns = parse_jsonl(main_jsonl, is_post30)
    if not turns:
        return None

    title = derive_title(turns)
    subagent_sections = []
    subagents_dir = session_dir / "subagents"
    if subagents_dir.exists():
        for sub_file in sorted(subagents_dir.glob("*.jsonl")):
            sub_uuid = sub_file.stem
            sub_turns = parse_jsonl(sub_file, is_post30)
            if not sub_turns:
                continue
            sub_title = derive_title(sub_turns)
            section_lines = [f"### Subagent {sub_uuid[:8]}: {sub_title}"]
            for t in sub_turns:
                role_label = "**User:**" if t["role"] == "user" else "**Assistant:**"
                section_lines.append(f"\n{role_label}\n\n{t['text']}")
            subagent_sections.append("\n".join(section_lines))

    out_path = SESSIONS_DIR / f"{date_str}_{slugify(title)}_{uuid[:8]}.md"
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        build_session_markdown(uuid, mtime, title, era, turns, subagent_sections),
        encoding="utf-8",
    )

    return {
        "uuid": uuid,
        "uuid8": uuid[:8],
        "date": mtime,
        "date_str": date_str,
        "title": title,
        "path": out_path,
        "skipped": False,
    }


def collect_all_metadata() -> list[dict]:
    meta_list = []
    if not SESSIONS_DIR.exists():
        return meta_list
    for md_file in SESSIONS_DIR.glob("*.md"):
        header = md_file.read_text(encoding="utf-8")[:600]
        date_match = re.search(r"^date: (.+)$", header, re.MULTILINE)
        title_match = re.search(r"^title: (.+)$", header, re.MULTILINE)
        if not date_match or not title_match:
            continue
        date_str = date_match.group(1).strip()
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            date = datetime.now(tz=timezone.utc)
        meta_list.append({
            "uuid8": md_file.stem.rsplit("_", 1)[-1],
            "date": date,
            "date_str": date_str,
            "title": title_match.group(1).strip(),
            "path": md_file,
        })
    return meta_list


def build_index(sessions: list[dict]) -> None:
    sessions_sorted = sorted(sessions, key=lambda x: x["date"], reverse=True)
    lines = [
        "# Session Index",
        "",
        f"*{len(sessions)} sessions — auto-generated*",
        "",
        "| Date | Title | File |",
        "|------|-------|------|",
    ]
    for s in sessions_sorted:
        title = s["title"].replace("|", "\\|")
        lines.append(f"| {s['date_str']} | {title} | [link](sessions/{s['path'].name}) |")
    lines.append("")
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")


def extract_all(force: bool = False) -> dict:
    """Extract all transcript sessions. Returns summary dict."""
    if not TRANSCRIPTS_DIR.exists():
        return {"processed": 0, "skipped": 0, "failed": 0, "error": f"No transcripts dir: {TRANSCRIPTS_DIR}"}

    session_dirs = sorted(
        [d for d in TRANSCRIPTS_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
    )
    processed = skipped = failed = 0
    all_meta = []

    for session_dir in session_dirs:
        try:
            result = process_session(session_dir, force=force)
            if result:
                all_meta.append(result)
                if result.get("skipped"):
                    skipped += 1
                else:
                    processed += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    if all_meta or SESSIONS_DIR.exists():
        # Rebuild from all session files on disk
        build_index(collect_all_metadata())

    return {"processed": processed, "skipped": skipped, "failed": failed}


def main() -> None:
    parser = argparse.ArgumentParser(description="Layer 1: Extract transcripts to markdown")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--session", metavar="UUID")
    group.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.session:
        matches = [d for d in TRANSCRIPTS_DIR.iterdir() if d.is_dir() and d.name.startswith(args.session)] if TRANSCRIPTS_DIR.exists() else []
        if not matches:
            print(f"ERROR: No session for {args.session!r}", file=sys.stderr)
            sys.exit(1)
        result = process_session(matches[0], force=True)
        if result:
            print(f"Extracted: {result['path'].name}")
        build_index(collect_all_metadata())
        return

    summary = extract_all(force=args.force)
    print(f"Done: {summary['processed']} extracted, {summary['skipped']} skipped, {summary['failed']} failed.")
    if summary.get("error"):
        print(summary["error"], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
