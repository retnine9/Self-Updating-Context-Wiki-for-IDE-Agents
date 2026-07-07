# Setup — Per-Platform Install

The context wiki installs on **Cursor**, **Claude Code**, and **Codex CLI**. All platforms share a neutral home:

```
~/.context-wiki/
  runtime/    # scripts, hooks, lib, install.json, wiki.env
  data/       # sessions/, extracts/, synthesis/, INDEX.md, wiki_state.json
```

Set the same `~/.context-wiki/data` on every platform on a machine to share one wiki across Cursor + Claude + Codex.

---

## User prompt (copy-paste)

> Clone https://github.com/retnine9/Self-Updating-Context-Wiki-for-IDE-Agents and follow docs/SETUP.md to install the context wiki on this machine. Auto-detect the platform (Cursor / Claude Code / Codex CLI), run install_wiki.py, then run doctor.py and report results.

---

## Prerequisites

- Python 3.8+ (Layer 1 extraction — no API keys)
- One of: Cursor (hooks enabled), Claude Code, or Codex CLI

---

## One-command install (all platforms)

From the clone directory:

```bash
python scripts/install_wiki.py --source-repo <clone-path>
# or force a platform:
python scripts/install_wiki.py --platform claude
python scripts/install_wiki.py --platform codex
python scripts/install_wiki.py --platform cursor
```

Auto-detect order: `WIKI_PLATFORM` env → `~/.cursor/projects` exists (Cursor) → `~/.claude/projects` exists (Claude) → `~/.codex/sessions` exists (Codex) → Cursor.

The installer:
1. Migrates a legacy `~/.cursor/wiki` + `~/.cursor/context` into `~/.context-wiki/{runtime,data}` (leaves back-compat symlinks/junctions; re-points `~/.cursor/hooks.json`).
2. Copies `lib/`, `scripts/`, `hooks/` to `~/.context-wiki/runtime/`.
3. Copies rules / subagent definitions / `CLAUDE.md` or `AGENTS.md` snippet to the platform's rules dir.
4. Initializes `~/.context-wiki/data/` (sessions/extracts/synthesis + templates).
5. Merges wiki hooks into the platform's hook config (append-only — preserves existing hooks).
6. Writes `~/.context-wiki/runtime/wiki.env` (`WIKI_PYTHON`, `WIKI_PLATFORM`, `WIKI_HOME`, `CONTEXT_WIKI_DIR`).
7. Runs `doctor.py --platform <p>`.

**Verify:** doctor exits 0 (warnings OK for new users with no sessions yet).

```bash
python ~/.context-wiki/runtime/scripts/doctor.py --platform <cursor|claude|codex>
```

---

## Platform-specific notes

### Cursor

- Hook config: `~/.cursor/hooks.json` (flat `sessionStart` + `beforeSubmitPrompt`).
- Drain envelope: `{"agent_message": "..."}`.
- Rules: `~/.cursor/rules/*.mdc`. Skills: `~/.cursor/skills/`.
- After install, restart Cursor and check the **Hooks** output channel for `sessionStart` activity.

### Claude Code

- Hook config: `~/.claude/settings.json` under top-level `hooks` (nested `{matcher, hooks:[{type:"command",command,timeout}]}`).
- Drain envelope: `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"..."}}`.
- Rules: `~/.claude/agents/wiki-synthesizer.md` (subagent definition, `model: claude-haiku-4-5`) + `~/.claude/CLAUDE.md` snippet.
- The installer raises `cleanupPeriodDays` to 90 in `~/.claude/settings.json` (default 30 purges transcripts before drain can fire).
- Drain synthesis uses the **Agent** tool (renamed from Task in v2.1.x) with `model="claude-haiku-4-5"` (full ID, not the `haiku` alias — the alias has historical 404 bugs).

### Codex CLI

- Hook config: `~/.codex/hooks.json` (nested `{hooks:{Event:[{matcher,hooks:[...]}]}}`).
- Drain envelope: `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"..."}}`.
- Rules: `~/.codex/agents/wiki-synthesizer.toml` (`model = "gpt-5.4-mini"`) + `~/.codex/AGENTS.md` snippet.
- **Hook trust flow (required):** after install, run `/hooks` once in the Codex CLI to trust the wiki hooks. Changed hooks are re-trusted by hash.
- Windows: native support shipped 2026-03-04 (AppContainer sandbox, experimental). The installer emits `commandWindows` overrides on Windows. If `codex.exe` fails to launch with `0xC0000135`, install the VC++ Redistributable.

---

## Manual steps (if not using the installer)

Clone to a stable path, then:

1. **Find Python:** `python scripts/find_python.py --write-env`
2. **Copy runtime:** `lib/`, `scripts/`, `hooks/` → `~/.context-wiki/runtime/`
3. **Copy rules** to the platform's rules dir (see above).
4. **Init data:** create `~/.context-wiki/data/{sessions,extracts,synthesis}`; copy `templates/synthesis/*.md` if empty; copy `templates/wiki_config.example.json` → `wiki_config.json`; create `wiki_state.json` (`{"last_extract":null,"last_synthesis":null,"pending_sessions":[]}`) and `INDEX.md`.
5. **Merge hooks** into the platform's hook config (append — do not wipe existing entries). See [PLATFORM_QUIRKS.md](PLATFORM_QUIRKS.md) for exact JSON shapes.
6. **Write** `~/.context-wiki/runtime/install.json` and `wiki.env`.
7. **Run doctor.**

**Never delete or overwrite existing `sessions/` or `synthesis/` content on re-install.**

---

## Re-install / update

1. `git pull` in the clone.
2. Re-run `python scripts/install_wiki.py --source-repo <clone>` (or `--platform <p>`).
3. Run doctor again.

Existing sessions and synthesis are preserved. Re-install re-points hook paths but does not wipe other hooks.

---

## Migrating an existing Cursor install

If you already have `~/.cursor/wiki` + `~/.cursor/context` from a prior install:

```bash
python scripts/migrate_to_neutral_home.py --dry-run   # preview
python scripts/migrate_to_neutral_home.py             # move + link + re-point hooks
```

Moves both dirs into `~/.context-wiki/{runtime,data}`, leaves back-compat symlinks/junctions at the old locations, and re-points `~/.cursor/hooks.json` wiki hook commands at the neutral runtime. Idempotent.

---

## Layout after install

```
~/.context-wiki/
  runtime/              # survives clone deletion
    lib/
    scripts/
    hooks/
    wiki.env
    install.json
  data/                 # your wiki
    sessions/
    extracts/
    synthesis/
    wiki_state.json
    INDEX.md

~/.cursor/   (Cursor only)
  rules/                # .mdc rules
  skills/               # skills
  hooks.json            # points at ~/.context-wiki/runtime/hooks
~/.claude/   (Claude only)
  settings.json         # hooks + cleanupPeriodDays=90
  agents/wiki-synthesizer.md
  CLAUDE.md
~/.codex/    (Codex only)
  hooks.json
  agents/wiki-synthesizer.toml
  AGENTS.md
```

---

## Examples mode (no install)

```powershell
$env:CONTEXT_WIKI_DIR = "$PWD\examples"
python scripts/doctor.py
python scripts/update_wiki.py --status
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) and [PLATFORM_QUIRKS.md](PLATFORM_QUIRKS.md).
