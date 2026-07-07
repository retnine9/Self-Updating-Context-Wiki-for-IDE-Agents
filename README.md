# Self-Updating-Context-Wiki-for-IDE-Agents

Functions as a wikipedia on a repository or project for autonomous or directed AI agents. Works with Cursor, Claude Code, and Codex CLI. Lightweight MD files that allow any agent to reference anything that happened in the past.

## Platform Support

| Capability | Cursor | Claude Code | Codex CLI |
|------------|:------:|:-----------:|:---------:|
| Query wiki (read markdown) | yes | yes | yes |
| Manual update (`update_wiki.py --all`) | yes | yes | yes |
| Auto Layer 1 (extract on session start) | yes | yes (Phase 1) | yes (Phase 2) |
| Auto Layer 2/3 drain (first-message synthesis) | yes | yes (Phase 1) | yes (Phase 2) |
| One-command install + doctor | yes | yes (Phase 1) | yes (Phase 2) |
| Cheap-model subagent synthesis | yes | yes (Phase 1) | yes (Phase 2) |

The wiki data (markdown on disk) is portable to any tool that can read files. **Zero-config automation today is Cursor-only**; Claude Code and Codex CLI adapters are landing in Phases 1 and 2. Do not assume full auto on those platforms until the adapter for your platform ships. See [docs/PLATFORM_QUIRKS.md](docs/PLATFORM_QUIRKS.md) for per-platform hook shapes, transcript paths, and known issues.

## Setup

**Recommended:** Ask your agent:

```
Clone https://github.com/retnine9/Self-Updating-Context-Wiki-for-IDE-Agents
and follow docs/SETUP.md on this machine.
```

| Scenario | Path |
|----------|------|
| Cursor agent install | [docs/SETUP.md](docs/SETUP.md) |
| Claude Code install | [docs/SETUP.md](docs/SETUP.md) — Claude section (Phase 1) |
| Codex CLI install | [docs/SETUP.md](docs/SETUP.md) — Codex section (Phase 2) |
| Try without installing | [Examples mode](#quick-start-examples-mode) below |
| Optional script shortcut | `install/install.ps1` (Windows) or `install/install.sh` (macOS/Linux) |
| Per-platform quirks | [docs/PLATFORM_QUIRKS.md](docs/PLATFORM_QUIRKS.md) |
| Other IDEs | [docs/AGENT_ADAPTERS.md](docs/AGENT_ADAPTERS.md) |
| Problems | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

After install, verify with:

```bash
python ~/.context-wiki/runtime/scripts/doctor.py --platform cursor   # or claude / codex
```

## How It Works

| Layer | What | Runs on |
|-------|------|---------|
| 1 | JSONL → readable session markdown | Python (`update_wiki.py --extract`) |
| 2 | Session → 7-section extract | Task subagent (`synthesis_model`, default Haiku) |
| 3 | Extracts → cross-session wiki | Task subagent (`synthesis_model`) |

No API keys needed. Synthesis uses a cheap configured model, not your session model.

## Triggers

| When | What happens |
|------|----------------|
| **New session starts** | Scan transcripts, extract new sessions (skippable) |
| **First message** (if pending) | Agent synthesizes extracts + wiki before your request |
| **Manual** | `python ~/.cursor/wiki/scripts/update_wiki.py --all` or ask the agent |

**Skip one session:** touch `~/.context-wiki/data/.wiki_skip` (or the legacy `~/.cursor/context/.wiki_skip`) or set `"auto_update_on_session_start": false` in `wiki_config.json`.

## Quick Start (examples mode)

```powershell
git clone https://github.com/retnine9/Self-Updating-Context-Wiki-for-IDE-Agents.git
cd Self-Updating-Context-Wiki-for-IDE-Agents

$env:CONTEXT_WIKI_DIR = "$PWD\examples"
python scripts/doctor.py
python scripts/update_wiki.py --status
python scripts/update_wiki.py --manifest
```

The examples directory has 3 fictional sessions; one is pending synthesis (`c9d0e1f2`) to demonstrate the drain flow.

## Wiki Files

```
~/.context-wiki/data/
  INDEX.md
  sessions/       # full dialogue
  extracts/       # ~400-word summaries
  synthesis/
    CAUSAL_MAP.md
    ERROR_REFERENCE.md
    OPEN_QUESTIONS.md
    RULES_DRAFT.md
    SKILLS_DRAFT.md
    DEVELOPMENT_HISTORY.md
```

Runtime (scripts, hooks) lives in `~/.context-wiki/runtime/` — separate from wiki data, shared across Cursor / Claude Code / Codex CLI on the same machine. Existing Cursor users are auto-migrated from `~/.cursor/wiki` + `~/.cursor/context` on first run of the new installer; legacy paths remain as symlinks for back-compat. See [Architecture](docs/ARCHITECTURE.md).

## Documentation

- [Setup (agent checklist)](docs/SETUP.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Cursor integration](docs/CURSOR_INTEGRATION.md)
- [Per-platform quirks](docs/PLATFORM_QUIRKS.md)
- [Other agent adapters](docs/AGENT_ADAPTERS.md)

## License

MIT
