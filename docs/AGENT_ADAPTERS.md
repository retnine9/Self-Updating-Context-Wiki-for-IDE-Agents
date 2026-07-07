# Agent Adapters

The context wiki is **tool-agnostic** — it is markdown files on disk. Any agent that can read/write files can use it.

## Cursor (reference implementation)

**Install:** [SETUP.md](SETUP.md) — clone + agent checklist, or `install/install.ps1` / `install.sh`.

- Runtime: `~/.cursor/wiki/scripts/update_wiki.py`
- Data: `~/.cursor/context/`
- `sessionStart` hook → `update_wiki.py --all`
- `beforeSubmitPrompt` hook → synthesis mandate
- Rules in `.mdc` format

## Claude Code / Codex / Other IDEs

Implement the same loop:

```
on session_start:
    if not skipped:
        run ~/.cursor/wiki/scripts/update_wiki.py --all

on first_user_message:
    if wiki_state.pending_sessions non-empty:
        manifest = run update_wiki.py --manifest
        agent synthesizes Layer 2 + 3 using manifest
        run update_wiki.py --complete

on demand:
    user runs update_wiki.py --all or asks to update wiki
```

Point `CONTEXT_WIKI_DIR` at your wiki data directory if not using `~/.cursor/context/`.

## Query Pattern

1. Read `context/INDEX.md` for session catalog
2. Read relevant `sessions/` or `extracts/` file
3. For cross-session patterns, read `synthesis/` files

Do not preload the entire wiki into context — query on demand.

## Headless / CI

Layer 1 (`extract_context.py`) runs without an LLM. Layers 2+3 require an LLM — use your CI agent or manual review. This repo does not ship separate API-key synthesis scripts.
