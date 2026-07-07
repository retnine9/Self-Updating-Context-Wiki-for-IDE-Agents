# Architecture

## Problem

IDE agents start each session with no memory of prior work. The context wiki is a self-updating project Wikipedia built from agent session transcripts.

## Runtime vs data

| Location | Contents |
|----------|----------|
| `~/.cursor/wiki/` | Runtime: `lib/`, `scripts/`, `hooks/`, `wiki.env`, `install.json` |
| `~/.cursor/context/` | Data: sessions, extracts, synthesis, `wiki_state.json` |

Hooks call scripts in `~/.cursor/wiki/` so the wiki keeps working after the git clone is moved or deleted. Re-install from clone updates runtime only; existing sessions are preserved.

## Three Layers

```
agent-transcripts/*.jsonl
        │
        ▼  Layer 1 (Python, no LLM)
   sessions/*.md  +  INDEX.md
        │
        ▼  Layer 2 (agent LLM)
   extracts/*_extract.md
        │
        ▼  Layer 3 (agent LLM)
   synthesis/*.md  (6 wiki files)
```

| Layer | Input | Output | Who runs it |
|-------|-------|--------|-------------|
| 1 | JSONL transcripts | Session markdown | `update_wiki.py --extract` (hook or manual) |
| 2 | Session markdown | Structured extract (~400 words) | Agent LLM via `--manifest` |
| 3 | New extracts | Updated wiki files | Agent LLM inline |

## Triggers

1. **sessionStart hook** — `update_wiki.py --all` (extract + prepare). Skippable via `.wiki_skip` or config.
2. **First user message** — if pending work exists, hook injects synthesis mandate before the agent handles the request.
3. **Manual** — `update_wiki.py --all` or "update the context wiki".

## State Files

| File | Purpose |
|------|---------|
| `wiki_state.json` | `last_extract`, `last_synthesis`, `pending_sessions` |
| `wiki_config.json` | `auto_update_on_session_start`, `batch_size` |
| `.drain_required.json` | Written by `--prepare` when synthesis is pending |
| `.wiki_skip` | Skip auto-update for one session |

## Synthesis Files

- `CAUSAL_MAP.md` — linked problems and root causes
- `ERROR_REFERENCE.md` — error signatures and fixes
- `OPEN_QUESTIONS.md` — unresolved items
- `RULES_DRAFT.md` — constraints not yet installed as rules
- `SKILLS_DRAFT.md` — workflows not yet installed as skills
- `DEVELOPMENT_HISTORY.md` — major architectural timeline

## Design Principles

- **No API keys needed.**
- **No stop hook** — sessionStart scans for new transcripts; more reliable than end-of-session hooks.
- **Live code wins** — wiki is institutional memory, not proof of current behavior.
