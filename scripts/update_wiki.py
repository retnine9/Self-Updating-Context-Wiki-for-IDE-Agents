"""
update_wiki.py -- Context wiki orchestrator

Single entry point for extract, prepare, status, manifest, and complete.

Usage:
  python update_wiki.py --all        # extract + prepare (sessionStart hook)
  python update_wiki.py --extract    # Layer 1 only
  python update_wiki.py --prepare    # Find pending sessions, set drain flag
  python update_wiki.py --status     # Human-readable status
  python update_wiki.py --manifest   # JSON for agent synthesis
  python update_wiki.py --complete   # Clear pending after synthesis
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from lib.paths import (
    CONTEXT_DIR,
    DRAIN_FLAG_FILE,
    EXTRACTS_DIR,
    SESSIONS_DIR,
    SKIP_FLAG_FILE,
    SYNTHESIS_DIR,
    WIKI_CONFIG_FILE,
    WIKI_STATE_FILE,
)
from lib.platform import get_platform
from scripts import extract_context
from scripts.synthesize_manifest import (
    DEFAULT_SYNTHESIS_MODEL,
    build_agent_instructions,
    build_drain_agent_message,
    build_full_manifest,
    extract_uuid8,
    find_pending_sessions,
    get_extract_path,
    is_synthesized,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    line = f"[{_now_iso()}] {msg}"
    print(line, file=sys.stderr)
    try:
        CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONTEXT_DIR / "wiki.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def load_config() -> dict:
    default = {
        "auto_update_on_session_start": True,
        "batch_size": 10,
        "synthesis_model": _resolve_synthesis_model(),
    }
    if WIKI_CONFIG_FILE.exists():
        try:
            data = json.loads(WIKI_CONFIG_FILE.read_text(encoding="utf-8"))
            default.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return default


def _resolve_synthesis_model() -> str:
    """Platform-aware default synthesis model."""
    try:
        return get_platform().default_synthesis_model()
    except Exception:
        return DEFAULT_SYNTHESIS_MODEL


def load_state() -> dict:
    default = {"last_extract": None, "last_synthesis": None, "pending_sessions": []}
    if WIKI_STATE_FILE.exists():
        try:
            data = json.loads(WIKI_STATE_FILE.read_text(encoding="utf-8"))
            default.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return default


def save_state(state: dict) -> None:
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    WIKI_STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def should_skip_session_start() -> bool:
    if SKIP_FLAG_FILE.exists():
        return True
    config = load_config()
    return not config.get("auto_update_on_session_start", True)


def cmd_extract() -> dict:
    summary = extract_context.extract_all(force=False)
    state = load_state()
    state["last_extract"] = _now_iso()
    save_state(state)
    log(f"Extract: {summary}")
    return summary


def discover_pending() -> list[str]:
    """All session uuid8 values missing extracts."""
    if not SESSIONS_DIR.exists():
        return []
    pending = []
    for session_path in sorted(SESSIONS_DIR.glob("*.md")):
        if not is_synthesized(session_path):
            pending.append(extract_uuid8(session_path))
    return pending


def cmd_prepare() -> dict:
    pending = discover_pending()
    state = load_state()
    # Dedupe while preserving order
    seen = set()
    deduped = []
    for u in pending:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    state["pending_sessions"] = deduped
    save_state(state)

    if deduped:
        config = load_config()
        DRAIN_FLAG_FILE.write_text(
            json.dumps({
                "count": len(deduped),
                "uuids": deduped,
                "set_at": _now_iso(),
                "synthesis_model": config.get("synthesis_model", DEFAULT_SYNTHESIS_MODEL),
            }, indent=2),
            encoding="utf-8",
        )
        log(f"Prepare: {len(deduped)} sessions pending synthesis")
    elif DRAIN_FLAG_FILE.exists():
        DRAIN_FLAG_FILE.unlink()

    return {"pending": len(deduped), "uuids": deduped}


def cmd_status() -> None:
    state = load_state()
    pending = discover_pending()
    session_count = len(list(SESSIONS_DIR.glob("*.md"))) if SESSIONS_DIR.exists() else 0
    extract_count = len(list(EXTRACTS_DIR.glob("*_extract.md"))) if EXTRACTS_DIR.exists() else 0
    synthesis_count = len(list(SYNTHESIS_DIR.glob("*.md"))) if SYNTHESIS_DIR.exists() else 0

    print("Context Wiki Status")
    print("-------------------")
    print(f"Context dir:      {CONTEXT_DIR}")
    print(f"Sessions:         {session_count}")
    print(f"Extracts:         {extract_count}")
    print(f"Synthesis files:  {synthesis_count}")
    print(f"Pending synthesis:{len(pending)}")
    print(f"Last extract:     {state.get('last_extract') or 'never'}")
    print(f"Last synthesis:   {state.get('last_synthesis') or 'never'}")
    print(f"Drain flag:       {'yes' if DRAIN_FLAG_FILE.exists() else 'no'}")
    print(f"Skip flag:        {'yes' if SKIP_FLAG_FILE.exists() else 'no'}")
    config = load_config()
    print(f"Synthesis model:  {config.get('synthesis_model', DEFAULT_SYNTHESIS_MODEL)}")


def cmd_manifest(platform: str | None = None) -> None:
    state = load_state()
    config = load_config()
    uuid8_list = state.get("pending_sessions") or discover_pending()
    pending_paths = find_pending_sessions(uuid8_list if uuid8_list else None)

    if not pending_paths:
        print(json.dumps({"pending_count": 0, "message": "No sessions pending synthesis."}))
        return

    synthesis_model = config.get("synthesis_model") or _resolve_synthesis_model()
    manifest = build_full_manifest(
        pending_paths,
        batch_size=config.get("batch_size", 10),
        synthesis_model=synthesis_model,
    )
    from lib.paths import SCRIPTS_DIR

    p_name = platform or _active_platform_name()
    manifest["platform"] = p_name
    manifest["agent_instructions"] = build_agent_instructions(
        synthesis_model, str(SCRIPTS_DIR), platform=p_name
    )
    print(json.dumps(manifest, indent=2))


def cmd_drain_message(platform: str | None = None) -> None:
    """JSON for the drain hook, in the platform-correct envelope."""
    if not DRAIN_FLAG_FILE.exists():
        print("{}")
        return
    try:
        drain = json.loads(DRAIN_FLAG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print("{}")
        return
    config = load_config()
    model = drain.get("synthesis_model") or config.get("synthesis_model") or _resolve_synthesis_model()
    count = drain.get("count", 0)
    from lib.paths import WIKI_HOME

    p_name = platform or _active_platform_name()
    msg = build_drain_agent_message(count, model, str(WIKI_HOME), platform=p_name)

    try:
        plat = get_platform() if p_name == _auto_platform_name() else _platform_by_name(p_name)
    except Exception:
        plat = None
    fmt = plat.drain_output_format() if plat else "agent_message"
    if fmt == "agent_message":
        print(json.dumps({"agent_message": msg}))
    else:
        event = plat.hook_event_names()[1] if plat else "UserPromptSubmit"
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": event,
                "additionalContext": msg,
            }
        }))


def _active_platform_name() -> str:
    try:
        return get_platform().name
    except Exception:
        return "cursor"


def _auto_platform_name() -> str:
    return _active_platform_name()


def _platform_by_name(name: str):
    from lib.platform.cursor import CursorPlatform
    from lib.platform.claude import ClaudePlatform
    from lib.platform.codex import CodexPlatform
    return {"cursor": CursorPlatform, "claude": ClaudePlatform, "codex": CodexPlatform}[name]()


def cmd_complete() -> None:
    state = load_state()
    state["pending_sessions"] = []
    state["last_synthesis"] = _now_iso()
    save_state(state)
    if DRAIN_FLAG_FILE.exists():
        DRAIN_FLAG_FILE.unlink()
    if SKIP_FLAG_FILE.exists():
        SKIP_FLAG_FILE.unlink()
    log("Synthesis marked complete.")


def cmd_all() -> int:
    if should_skip_session_start():
        log("Session start wiki update skipped (.wiki_skip or config).")
        return 0
    cmd_extract()
    result = cmd_prepare()
    if result["pending"]:
        print(f"Wiki: {result['pending']} session(s) pending synthesis.", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Context wiki orchestrator")
    parser.add_argument("--all", action="store_true", help="Extract + prepare")
    parser.add_argument("--extract", action="store_true", help="Layer 1 extract only")
    parser.add_argument("--prepare", action="store_true", help="Find pending, set drain flag")
    parser.add_argument("--status", action="store_true", help="Print status")
    parser.add_argument("--manifest", action="store_true", help="JSON manifest for agent")
    parser.add_argument("--complete", action="store_true", help="Clear pending after synthesis")
    parser.add_argument(
        "--drain-message",
        action="store_true",
        help="JSON drain message for the platform's UserPromptSubmit hook",
    )
    parser.add_argument(
        "--platform",
        choices=("cursor", "claude", "codex"),
        default=None,
        help="Override platform for --manifest / --drain-message output shape",
    )
    args = parser.parse_args()

    if not any(v for k, v in vars(args).items() if k != "platform"):
        parser.print_help()
        return 0

    if args.all:
        return cmd_all()
    if args.extract:
        cmd_extract()
        return 0
    if args.prepare:
        cmd_prepare()
        return 0
    if args.status:
        cmd_status()
        return 0
    if args.manifest:
        cmd_manifest(platform=args.platform)
        return 0
    if args.complete:
        cmd_complete()
        return 0
    if args.drain_message:
        cmd_drain_message(platform=args.platform)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
