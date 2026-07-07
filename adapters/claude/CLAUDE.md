# Context Wiki — Claude Code Integration

A self-updating Wikipedia on your project for AI agents. Session history is extracted, synthesized, and stored as lightweight markdown files any agent can query on demand.

## Three Operations

| Operation | What it does | How to trigger |
|-----------|-------------|----------------|
| **Ingest** | JSONL transcripts -> session markdown -> extracts -> wiki | Automatic on `SessionStart`; manual: `python ~/.context-wiki/runtime/scripts/update_wiki.py --all` |
| **Query** | Read INDEX.md, sessions, extracts, or synthesis files | On demand — ask the agent |
| **Lint** | Health-check synthesis files | Invoke the `lint-context` skill |

## File Locations

```
~/.context-wiki/data/
  INDEX.md              # Session catalog (read first)
  wiki_state.json       # last_extract, last_synthesis, pending_sessions
  sessions/             # Layer 1: full dialogue (tool noise stripped)
  extracts/             # Layer 2: ~400-word structured summaries
  synthesis/            # Layer 3: cross-session wiki (6 files)
    CAUSAL_MAP.md
    ERROR_REFERENCE.md
    OPEN_QUESTIONS.md
    RULES_DRAFT.md
    SKILLS_DRAFT.md
    DEVELOPMENT_HISTORY.md
```

Set `CONTEXT_WIKI_DIR` to override the default (`~/.context-wiki/data`).

## Drain Protocol (MANDATORY when pending sessions exist)

When a `UserPromptSubmit` hook injects a `MANDATORY CONTEXT WIKI DRAIN` message into `additionalContext`, complete synthesis BEFORE addressing the user's request:

1. Run `python ~/.context-wiki/runtime/scripts/update_wiki.py --manifest`
2. Layer 2: spawn one subagent per `layer2_batches` entry via the **Agent** tool with `model="claude-haiku-4-5"`. Each subagent writes every `extract_path` in its batch.
3. Layer 3: spawn one subagent (same model) to read new extracts and rewrite all six `layer3_files` per `layer3_instruction`.
4. Run `python ~/.context-wiki/runtime/scripts/update_wiki.py --complete`
5. Delete `.drain_required.json` if still present.

Use the full model ID `claude-haiku-4-5`, not the `haiku` alias — the alias has historical unresolved-alias 404 bugs. Do NOT run Layer 2/3 on the session's main model.

If the user said to skip the wiki update, run `--complete` and delete `.drain_required.json`.

## When to Consult Which File

| Situation | File |
|-----------|------|
| "Have we tried X before?" | INDEX.md -> session -> extract |
| Recurring bug | synthesis/ERROR_REFERENCE.md |
| Unresolved decision | synthesis/OPEN_QUESTIONS.md |
| Why does Y work this way? | synthesis/CAUSAL_MAP.md |

Do NOT preload wiki content into context unless actively using it.

## Source of Truth

Live file reads beat wiki content. The wiki is navigation and institutional memory — not proof of current code behavior.

## Decision Capture

When a session produces a significant architectural decision, a new bug pattern, or a resolved open question, extend the context base before the session ends:

- New bug pattern or resolved error -> append to `synthesis/ERROR_REFERENCE.md`
- New constraint discovered through failure -> append to `synthesis/RULES_DRAFT.md` (tag [DRAFT])
- Repeatable workflow that worked -> append to `synthesis/SKILLS_DRAFT.md` (tag [DRAFT])
- Resolved/open question -> update `synthesis/OPEN_QUESTIONS.md`
- Architectural decision -> append to `synthesis/DEVELOPMENT_HISTORY.md`

Then run `python ~/.context-wiki/runtime/scripts/update_wiki.py --complete`.
