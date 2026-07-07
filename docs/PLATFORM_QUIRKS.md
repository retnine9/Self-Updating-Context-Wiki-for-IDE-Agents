# Platform Quirks Reference

Per-platform facts that drive the wiki adapters. Hook/config/schema items are sourced from official docs; transcript JSONL line shapes for Claude Code and Codex CLI are observed-stable but **not officially documented** — parsers are defensive and skip unknown line types.

## Cursor (reference — do not break)

| Item | Value |
|------|-------|
| Transcripts | `~/.cursor/projects/<slug>/agent-transcripts/<uuid>/<uuid>.jsonl` (subdir per session) |
| Subagents | `<uuid>/subagents/*.jsonl` |
| Hooks file | `~/.cursor/hooks.json` (flat) |
| Session start | `sessionStart` → `{"command": "...", "timeout": 120}` |
| Drain inject | `beforeSubmitPrompt` → stdout `{"agent_message": "..."}` |
| Rules | `~/.cursor/rules/*.mdc` |
| Skills | `~/.cursor/skills/<name>/SKILL.md` |
| Subagents | Task tool with `model=` slug |
| Cheap model default | `claude-4.5-haiku-thinking` |

JSONL line shape (Cursor):

```json
{
  "role": "user" | "assistant",
  "message": {
    "content": [
      {"type": "text", "text": "..."},
      {"type": "tool_use", "id": "...", "name": "...", "input": {...}},
      {"type": "tool_result", "tool_use_id": "...", "content": "..."}
    ]
  }
}
```

`content` may also be a plain string. Post-3.0 transcripts (mtime ≥ 2026-04-03) have `tool_use`/`tool_result` blocks stripped during extraction.

## Claude Code

| Item | Value |
|------|-------|
| Transcripts | `~/.claude/projects/<encoded-cwd>/<uuid>.jsonl` (flat file, no subdir) |
| Encoded cwd | `/Users/me/proj` → `-Users-me-proj` (`/` and `:` → `-`, leading `-` stripped) |
| Hooks file | `~/.claude/settings.json` (user) + `.claude/settings.json` (project). No separate user `hooks.json`. |
| Session start | `SessionStart` (matcher: `startup\|resume\|clear\|compact`) |
| Drain inject | `UserPromptSubmit` → `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"..."}}` |
| Rules | `CLAUDE.md` + `~/.claude/agents/*.md` (subagent definitions) |
| Subagents | `Agent` tool (renamed from `Task` in v2.1.x) with `model=` param; match both names when parsing |
| Cheap model default | `claude-haiku-4-5` (full ID — `haiku` alias has historical 404 bugs) |
| Transcript purge | `cleanupPeriodDays` default 30 — raise to ≥90 in `~/.claude/settings.json` or transcripts vanish before drain |
| Docs | [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks), [/settings](https://code.claude.com/docs/en/settings), [/subagents](https://code.claude.com/docs/en/subagents), [/model-config](https://code.claude.com/docs/en/model-config) |

Hooks config shape (top-level `hooks` key in settings.json):

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "startup|resume|clear|compact",
        "hooks": [{ "type": "command", "command": "...", "timeout": 60 }] }
    ],
    "UserPromptSubmit": [
      { "matcher": "*",
        "hooks": [{ "type": "command", "command": "...", "timeout": 60 }] }
    ]
  }
}
```

Handler `type` values documented: `command`, `prompt`, `http`, `mcp_tool` (v2.1.118+), `agent`. Default timeout 60s.

JSONL line shape (observed, undocumented — schema drifts between releases):

```json
{ "type": "user", "uuid": "...", "parentUuid": "...", "timestamp": "...",
  "sessionId": "...", "cwd": "...",
  "message": { "role": "user", "content": "plain string" | [content blocks] } }
```

```json
{ "type": "assistant", "uuid": "...", "timestamp": "...",
  "message": { "role": "assistant",
    "content": [
      {"type": "thinking", "thinking": "..."},
      {"type": "text", "text": "..."},
      {"type": "tool_use", "id": "toolu_...", "name": "Bash", "input": {...}}
    ],
    "usage": {...} } }
```

`tool_result` blocks arrive in a later `type: "user"` row with matching `tool_use_id`. Other top-level `type` values seen (`summary`, `system`, `tool-use-status`, telemetry) are skipped by the parser. ~10,000 char cap on injected `additionalContext`; over that, Claude Code writes the full text to a session file and passes the path + a short preview.

## Codex CLI

| Item | Value |
|------|-------|
| Transcripts | `transcript_path` from hook stdin JSON; files at `~/.codex/sessions/YYYY/MM/DD/rollout-<iso>-<uuid>.jsonl` |
| Hooks file | `~/.codex/hooks.json` (and `config.toml` `[[hooks.Event]]` tables) |
| Session start | `SessionStart` (matcher: regex; `*`/`""`/omitted = all) |
| Drain inject | `UserPromptSubmit` → `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"..."}}` |
| Rules | `AGENTS.md` + `~/.codex/agents/*.toml` |
| Subagents | Native subagents via `~/.codex/agents/*.toml` with `model = "..."` |
| Cheap model default | `gpt-5.4-mini` (official cheap/subagent slug) |
| Trust flow | New/changed hooks skipped until user runs `/hooks` once. Trust keyed on hook hash. |
| Parallelism | Hooks for the same event run concurrently — no ordering guarantee. deny-wins, continue:false-wins. |
| Timeout | Default 600s (not 60 like Claude) |
| Windows | Native support shipped 2026-03-04 (AppContainer sandbox, experimental). Needs VC++ Redistributable. Use `commandWindows` overrides. |
| Docs | [developers.openai.com/codex/hooks](https://developers.openai.com/codex/hooks), [/concepts/subagents](https://developers.openai.com/codex/concepts/subagents), [/models](https://developers.openai.com/codex/models), [/windows](https://developers.openai.com/codex/windows#troubleshooting-and-faq) |

Hooks config shape (nested):

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "startup|resume",
        "hooks": [{ "type": "command", "command": "...", "statusMessage": "Loading wiki" }] }
    ],
    "UserPromptSubmit": [
      { "hooks": [{ "type": "command", "command": "...", "commandWindows": "..." }] }
    ]
  }
}
```

Only `type: "command"` runs today; `prompt` and `agent` handler types are parsed but skipped. Hook stdin JSON includes `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, and (turn-scoped) `turn_id` + `permission_mode`.

JSONL line shape (observed, officially unstable — OpenAI states the transcript format is not a stable interface):

```json
{ "timestamp": "...", "type": "...", "payload": {...} }
```

Core `type` values: `session_meta`, `turn_context`, `config_snapshot`, `input_item`, `response_item`, `event_msg`. A model tool call is `response_item` with `payload.type == "function_call"` (args are a stringified JSON in `arguments`); paired by `call_id` to a later `function_call_output`. Assistant text is `response_item` `payload.type == "message"`, `role == "assistant"`, `content` array of `{type:"output_text", text}`. Subagents are separate rollout files with `parent_thread_id` in their `session_meta`.

Known issue (openai/codex#16933, open): `additionalContext` is currently persisted into the rollout as a developer message rather than being model-visible-only. The wiki's `.drain_injected` one-shot guard prevents re-injection loops while this remains unfixed.

## Shared default home (all platforms)

| Path | Purpose |
|------|---------|
| `~/.context-wiki/runtime/` | scripts, hooks, lib, install.json, wiki.env |
| `~/.context-wiki/data/` | sessions/, extracts/, synthesis/, INDEX.md, wiki_state.json, wiki.log |

Env overrides (any platform): `WIKI_HOME` (runtime), `CONTEXT_WIKI_DIR` (data), `WIKI_PLATFORM` (force `cursor`/`claude`/`codex`), `WIKI_PROJECT_CWD` (pin project for transcript discovery), `WIKI_PYTHON` (Python for hooks). Existing Cursor users are auto-migrated from `~/.cursor/wiki` + `~/.cursor/context` on first run of the new installer; legacy paths become symlinks for back-compat.
