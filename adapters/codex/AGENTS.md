# Context Wiki — Codex CLI Integration

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
```

Set `CONTEXT_WIKI_DIR` to override the default (`~/.context-wiki/data`).

## Hook Trust

Codex skips new or changed hooks until you trust them. After install, run `/hooks` once in the Codex CLI to review and trust the wiki hooks. Changed hooks are re-trusted by hash.

## Drain Protocol (MANDATORY when pending sessions exist)

When a `UserPromptSubmit` hook injects a `MANDATORY CONTEXT WIKI DRAIN` message into `additionalContext`, complete synthesis BEFORE addressing the user's request:

1. Run `python ~/.context-wiki/runtime/scripts/update_wiki.py --manifest`
2. Layer 2: spawn one native Codex subagent per `layer2_batches` entry with `model="gpt-5.4-mini"`. Each subagent writes every `extract_path` in its batch.
3. Layer 3: spawn one subagent (same model) to read new extracts and rewrite all six `layer3_files` per `layer3_instruction`.
4. Run `python ~/.context-wiki/runtime/scripts/update_wiki.py --complete`
5. Delete `.drain_required.json` if still present.

Do NOT run Layer 2/3 on the session's main model (e.g. gpt-5.5). Use `gpt-5.4-mini` — the official cheap/subagent model.

Note: Codex currently persists `additionalContext` into the rollout transcript (openai/codex#16933). The wiki's `.drain_injected` one-shot guard prevents re-injection loops.

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
