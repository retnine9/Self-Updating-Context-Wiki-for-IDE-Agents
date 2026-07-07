# Agent Adapters

The context wiki is **tool-agnostic** at the data layer — markdown files on disk. Any agent that can read/write files can query it. The **automation layer** (auto-extract on session start, auto-drain synthesis on first message, one-command install) is per-platform and ships as adapters.

## Platform Status

| Capability | Cursor | Claude Code | Codex CLI |
|------------|:------:|:-----------:|:---------:|
| Query wiki (read markdown) | yes | yes | yes |
| Manual update (`update_wiki.py --all`) | yes | yes | yes |
| Auto Layer 1 (extract on session start) | yes | yes | yes |
| Auto Layer 2/3 drain (first-message synthesis) | yes | yes | yes |
| One-command install + doctor | yes | yes | yes |
| Cheap-model subagent synthesis | yes | yes | yes |

Run `doctor.py --platform <p>` after install to confirm your platform is wired correctly. See [PLATFORM_QUIRKS.md](PLATFORM_QUIRKS.md) for hook shapes, transcript paths, and known issues.

## Cursor (reference implementation)

**Install:** [SETUP.md](SETUP.md) — clone + agent checklist, or `install/install.ps1` / `install.sh`.

- Runtime: `~/.context-wiki/runtime/scripts/update_wiki.py` (legacy `~/.cursor/wiki/`)
- Data: `~/.context-wiki/data/` (legacy `~/.cursor/context/`)
- `sessionStart` hook → `update_wiki.py --all`
- `beforeSubmitPrompt` hook → `{"agent_message": "..."}` synthesis mandate
- Rules in `.mdc` format under `~/.cursor/rules/`
- Subagents via Task tool with `model=` slug (default `claude-4.5-haiku-thinking`)

## Claude Code

- Runtime + data: same neutral `~/.context-wiki/` home (shared with Cursor if both installed).
- `SessionStart` hook → `update_wiki.py --all`
- `UserPromptSubmit` hook → `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"..."}}`
- Hooks merged into `~/.claude/settings.json` under the top-level `hooks` key (nested `{matcher, hooks:[{type:"command",command,timeout}]}` shape).
- Transcripts: `~/.claude/projects/<encoded-cwd>/<uuid>.jsonl` (flat file, encoded cwd).
- Rules: `CLAUDE.md` snippet + subagent definition in `~/.claude/agents/wiki-synthesizer.md`.
- Cheap model: `Agent` tool with `model: claude-haiku-4-5` (full ID, not the `haiku` alias — avoids historical alias→404 failures).
- Raise `cleanupPeriodDays` to ≥90 in `~/.claude/settings.json` or transcripts are purged at 30 days before drain can fire.

## Codex CLI

- Runtime + data: same neutral `~/.context-wiki/` home.
- `SessionStart` hook → `update_wiki.py --all`
- `UserPromptSubmit` hook → `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"..."}}`
- Hooks merged into `~/.codex/hooks.json` (nested `{hooks:{Event:[{matcher,hooks:[{type:"command",command,timeout,commandWindows}]}}]}` shape). `matcher` is a regex. Windows installs emit `commandWindows` overrides.
- Transcripts: `transcript_path` from hook stdin JSON, or scan `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`. Format is officially unstable — parser is defensive and pinned to a CLI version range.
- Trust flow: after install, run `/hooks` once to trust the wiki hooks (changed hooks are re-trusted by hash).
- Rules: `AGENTS.md` snippet + `~/.codex/agents/wiki-synthesizer.toml` with `model = "gpt-5.4-mini"`.
- Windows: native support shipped 2026-03-04 (AppContainer sandbox, experimental); requires VC++ Redistributable or `codex.exe` silently fails with `0xC0000135`.

## Other IDEs

No adapter yet. Manual use works:

```
on session_start:
    if not skipped:
        run update_wiki.py --all

on first_user_message:
    if wiki_state.pending_sessions non-empty:
        manifest = run update_wiki.py --manifest
        agent synthesizes Layer 2 + 3 using manifest
        run update_wiki.py --complete

on demand:
    user runs update_wiki.py --all or asks to update wiki
```

Point `CONTEXT_WIKI_DIR` at your wiki data directory if not using the default `~/.context-wiki/data/`.

## Query Pattern

1. Read `INDEX.md` for session catalog
2. Read relevant `sessions/` or `extracts/` file
3. For cross-session patterns, read `synthesis/` files

Do not preload the entire wiki into context — query on demand.

## Headless / CI

Layer 1 (`extract_context.py`) runs without an LLM. Layers 2+3 require an LLM — use your CI agent or manual review. This repo does not ship separate API-key synthesis scripts.
