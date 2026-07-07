# Platform Port Handoff — Multi-IDE Context Wiki

**Status:** Planning — not started  
**Created:** 2026-07-07  
**Context:** Session review of whether the repo is actually usable on Claude Code, Codex, etc. Conclusion: wiki **data** is portable; **automation** is Cursor-only today.

Use this document to open a planning session. Promote to a `.plan.md` when ready to implement.

---

## Goal

Make the context wiki honestly multi-platform:

1. **Tier A (must):** Claude Code and OpenAI Codex CLI get working auto-extract + auto-drain, comparable to Cursor.
2. **Tier B (should):** Per-platform install, doctor checks, and cheap-model synthesis guidance.
3. **Tier C (nice):** Shared wiki data across tools (`~/.context-wiki/` or configurable `CONTEXT_WIKI_DIR`).

Do **not** claim parity in README until Tier A passes verification for each platform.

---

## Verified Current State (2026-07-07)

Checked on disk in `Self-Updating-Context-Wiki-for-IDE-Agents` @ `main` (post agent-first + cheap synthesis commits).

| Artifact | Status | Notes |
|----------|--------|-------|
| `lib/paths.py` | Cursor-only | `TRANSCRIPTS_DIR` → `~/.cursor/projects/.../agent-transcripts` |
| `scripts/extract_context.py` | Cursor JSONL | Expects `{uuid}/{uuid}.jsonl`, `role` + `message.content[]` |
| `scripts/update_wiki.py` | Portable | Orchestrator; drain via `--drain-message` |
| `scripts/synthesize_manifest.py` | Portable | `synthesis_model` default `claude-4.5-haiku-thinking` |
| `scripts/install_wiki.py` | Cursor-only | Writes `~/.cursor/hooks.json`, `~/.cursor/wiki/` |
| `scripts/doctor.py` | Cursor-only | Checks `~/.cursor/hooks.json`, Cursor transcript dirs |
| `hooks/*` | Cursor-shaped | `sessionStart` / `beforeSubmitPrompt`; PS1 + sh |
| `cursor/rules/*.mdc` | Cursor-only | `.mdc` format |
| `docs/AGENT_ADAPTERS.md` | Aspirational | 15-line pseudo-loop; no real adapters |
| `examples/` | Portable | Manual `CONTEXT_WIKI_DIR=./examples` works on any OS |

**Already works everywhere (no port needed):**

- Query: `INDEX.md` → `sessions/` → `extracts/` → `synthesis/`
- Manual: `update_wiki.py --all | --manifest | --complete`
- Examples mode for demos

---

## The Gap (why README oversells)

README says "Cursor, Claude Code, Codex, etc." That is true for **markdown on disk**, false for **zero-config install**.

```
                    Cursor    Claude Code    Codex CLI
─────────────────────────────────────────────────────
Query wiki            ✅          ✅            ✅
Manual update         ✅          ✅            ✅
Auto Layer 1          ✅          ❌            ❌
Auto Layer 2/3 drain  ✅          ❌            ❌
install_wiki.py       ✅          ❌            ❌
doctor.py pass        ✅          ❌            ❌
Cheap model subagents ✅*         ❌*           ❌*

* Cursor: Task tool + synthesis_model in config; enforced by rules only
```

---

## Platform Quirks Reference

### Cursor (reference — do not break)

| Item | Value |
|------|-------|
| Transcripts | `~/.cursor/projects/<slug>/agent-transcripts/<uuid>/<uuid>.jsonl` |
| Hooks file | `~/.cursor/hooks.json` |
| Session start | `sessionStart` |
| Drain inject | `beforeSubmitPrompt` → `{"agent_message": "..."}` |
| Rules | `~/.cursor/rules/*.mdc` |
| Subagents | Task tool with `model=` slug |

### Claude Code

| Item | Value |
|------|-------|
| Transcripts | `~/.claude/projects/<encoded-cwd>/<uuid>.jsonl` (flat file, not subdir) |
| Hooks file | `~/.claude/settings.json` or `.claude/settings.json` |
| Session start | `SessionStart` |
| Drain inject | `UserPromptSubmit` → `hookSpecificOutput.additionalContext` (NOT `agent_message`) |
| Rules | `CLAUDE.md`, `.claude/rules/`, skills in component frontmatter |
| Docs | [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) |

**Known quirks:**

- JSONL schema is typed lines (`user`, `assistant`, `tool_use`, …) — **not** Cursor's `role`/`message` shape. Schema unofficial ([#53516](https://github.com/anthropics/claude-code/issues/53516)).
- `transcript_path` in hooks can be wrong in git worktrees ([#44450](https://github.com/anthropics/claude-code/issues/44450)).
- Default 30-day transcript purge unless `cleanupPeriodDays` raised in `~/.claude/settings.json`.
- Project path encoding: `/Users/me/proj` → `-Users-me-proj`.

### OpenAI Codex CLI

| Item | Value |
|------|-------|
| Transcripts | Via `transcript_path` in hook stdin JSON (path varies) |
| Hooks file | `~/.codex/hooks.json` or `.codex/hooks.json` |
| Session start | `SessionStart` |
| Drain inject | `UserPromptSubmit` → `additionalContext` in JSON stdout |
| Rules | `AGENTS.md`, project instructions |
| Docs | [developers.openai.com/codex/hooks](https://developers.openai.com/codex/hooks) |

**Known quirks:**

- `hooks.json` shape is nested: `{ "hooks": { "SessionStart": [{ "hooks": [{ "type": "command", "command": "..." }] }] } } }` — not Cursor's flat `{ "command": "..." }`.
- Hooks require trust review (`/hooks` in CLI) before first run.
- Hooks run **in parallel** — no ordering guarantee.
- Windows support has been experimental / limited in early releases — verify before promising.
- `SessionStart` stdout / JSON adds developer context (similar to Claude).

---

## Proposed Architecture

### 1. Platform abstraction layer

```
lib/
  paths.py              # shared: CONTEXT_DIR, WIKI_HOME
  platform/
    __init__.py         # get_platform() from WIKI_PLATFORM env or auto-detect
    base.py             # Protocol: resolve_transcripts_dir, hook_paths, drain_output_format
    cursor.py           # current behavior
    claude.py           # ~/.claude paths + encoded cwd
    codex.py            # ~/.codex paths
```

### 2. Transcript adapters (Layer 1)

```
lib/transcripts/
  cursor.py             # move existing parse_jsonl logic
  claude.py             # parse Claude JSONL line types → unified turns[]
  codex.py              # parse Codex JSONL → unified turns[]
```

Unified turn shape (internal):

```python
{"role": "user" | "assistant", "text": str}
```

`extract_context.py` becomes adapter-agnostic: discover sessions via platform, parse via adapter, write same `sessions/*.md`.

### 3. Hook wrappers per platform

Keep thin shell scripts in `hooks/` but add platform-specific drain output:

| Platform | Session start script | Drain script | Output format |
|----------|---------------------|--------------|---------------|
| Cursor | `wiki-on-start.ps1/.sh` | `inject-wiki-drain.ps1/.sh` | `{"agent_message": "..."}` |
| Claude | `wiki-on-start-claude.sh` | `inject-wiki-drain-claude.sh` | `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}` |
| Codex | `wiki-on-start-codex.sh` | `inject-wiki-drain-codex.sh` | `{"hookEventName": "UserPromptSubmit", "additionalContext": "..."}` |

Alternative: single `inject-wiki-drain.py` that prints correct JSON for `WIKI_PLATFORM` — reduces duplication.

### 4. Install + doctor

- `install_wiki.py --platform cursor|claude|codex` (auto-detect default)
- Merge hooks into correct config file with correct JSON shape
- `doctor.py --platform` checks the right paths and hook events
- Optional: neutral runtime home `~/.context-wiki/runtime/` instead of `~/.cursor/wiki/` (breaking change — defer to Phase 3 or keep `~/.cursor/wiki/` as legacy alias)

### 5. Rules / instructions per platform

| Platform | Ship as |
|----------|---------|
| Cursor | `cursor/rules/*.mdc` (existing) |
| Claude Code | `adapters/claude/CLAUDE.md` snippet + `adapters/claude/rules/` |
| Codex | `adapters/codex/AGENTS.md` snippet |

Install copies the right files; do not assume `.mdc` loads elsewhere.

### 6. Cheap synthesis model per platform

| Platform | Suggested default | Config key |
|----------|-------------------|------------|
| Cursor | `claude-4.5-haiku-thinking` | `synthesis_model` (exists) |
| Claude Code | `claude-haiku-4-5` or cheapest available | same key; document Claude subagent invocation |
| Codex | TBD — check Codex model slugs | same key |

Drain instructions must name the platform-specific subagent mechanism (Task tool vs Claude agent vs Codex equivalent).

---

## Phased Plan

### Phase 0 — Honesty pass (small, do first)

- [ ] Update `README.md` and `AGENT_ADAPTERS.md`: "full auto on Cursor; manual + query elsewhere until adapters land"
- [ ] Add `docs/PLATFORM_QUIRKS.md` (user-facing summary of this handoff's quirks table)
- [ ] Add doctor warning when `WIKI_PLATFORM` unset and non-Cursor transcripts detected

**Verify:** README matches reality; no false "works on Codex" claims.

### Phase 1 — Claude Code adapter (highest demand)

- [ ] Sample 3–5 real `~/.claude/projects/**/*.jsonl` files; document line types empirically
- [ ] Implement `lib/transcripts/claude.py` parser
- [ ] `WIKI_PLATFORM=claude` + `TRANSCRIPTS_DIR` override in `paths.py`
- [ ] Claude hook install: `SessionStart` + `UserPromptSubmit` in `settings.json`
- [ ] Drain JSON emitter for `additionalContext`
- [ ] `install_wiki.py --platform claude`
- [ ] Doctor checks for Claude paths
- [ ] Manual test on real Claude Code session

**Verify:**

- [ ] New Claude session → session markdown appears in wiki
- [ ] Second session → drain fires with correct inject format
- [ ] Haiku (or configured model) subagent writes extract
- [ ] `doctor.py` exit 0 on Claude-only machine

### Phase 2 — Codex CLI adapter

- [ ] Sample Codex `transcript_path` JSONL; implement parser
- [ ] Codex nested `hooks.json` merge in install
- [ ] Hook trust flow documented in SETUP (user runs `/hooks` once)
- [ ] `install_wiki.py --platform codex`
- [ ] Doctor + manual test on macOS/Linux

**Verify:** Same checklist as Phase 1 on Codex.

### Phase 3 — Unified data home (optional)

- [ ] Default `CONTEXT_WIKI_DIR=~/.context-wiki/data` (or keep `~/.cursor/context` as default for back compat)
- [ ] Runtime at `~/.context-wiki/runtime/` — all platforms share one wiki
- [ ] Migration note for existing Cursor users

### Phase 4 — CI / regression

- [ ] Fixture JSONL per platform in `tests/fixtures/transcripts/`
- [ ] Parser unit tests (no LLM)
- [ ] Golden `sessions/*.md` outputs

---

## Open Questions (resolve in planning session)

1. **Runtime home:** Keep `~/.cursor/wiki/` for all platforms (weird on Claude-only) or neutral `~/.context-wiki/`?
2. **Shared wiki across tools:** One `CONTEXT_WIKI_DIR` for Cursor + Claude + Codex on same machine? (Probably yes — same project memory.)
3. **Claude JSONL stability:** Pin to observed schema vs depend on Anthropic documenting it?
4. **Codex on Windows:** Support now or document macOS/Linux only for Codex adapter?
5. **Headless synthesis:** Re-introduce optional API-key path (`optional/headless/`) for CI without IDE subagents?
6. **synthesis_model on Claude Code:** Does Task/subagent API accept the same slugs as Cursor's Task tool?

---

## Out of Scope (this port)

- VS Code / Windsurf / generic IDE plugins (unless they expose JSONL + hooks)
- Project-scoped `.context-wiki/` inside repos (mentioned as future in SETUP.md)
- Rewriting Layer 2/3 to non-agent API calls (unless optional headless returns)
- Graphify / codebase-memory integration

---

## Verification Matrix (sign-off gate)

Before marking platform "supported":

| Check | Cursor | Claude | Codex |
|-------|--------|--------|-------|
| `install_wiki.py --platform X` completes | ✅ today | | |
| `doctor.py` exit 0 | ✅ today | | |
| Layer 1 after 1 session | ✅ today | | |
| Drain on session 2 first message | ✅ today | | |
| Cheap model subagent synthesis | ✅ tested | | |
| Hooks survive runtime path move | ✅ today | | |
| README tier label accurate | | | |

---

## Suggested First Planning Prompt

Copy into next session:

> Read `docs/PLATFORM_PORT_HANDOFF.md` in Self-Updating-Context-Wiki-for-IDE-Agents. Resolve the open questions (runtime home, shared wiki, Claude schema approach). Produce an implementation plan for Phase 0 + Phase 1 (Claude Code adapter) with file-level tasks. Do not implement until plan is approved.

---

## Related Files

- `docs/AGENT_ADAPTERS.md` — needs rewrite after Phase 0
- `docs/SETUP.md` — Cursor-only today; add per-platform sections
- `lib/paths.py` — primary coupling point
- `scripts/extract_context.py` — parser coupling
- `scripts/install_wiki.py` — hook merge coupling
- `hooks/inject-wiki-drain.ps1` — uses `--drain-message` (Cursor format only)

---

## Session Provenance

Findings from 2026-07-07 session: portability review, cheap synthesis model (`synthesis_model`), end-to-end Haiku test on `examples/`, first-run / model-selection UX discussion.
