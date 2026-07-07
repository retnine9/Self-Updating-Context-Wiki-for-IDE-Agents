# Self-Updating-Context-Wiki-for-IDE-Agents

Functions as a wikipedia on a repository or project for autonomous or directed AI agents. Designed to be used with tools such as Cursor, Claude Code, Codex, etc. Automatically reads new session extracts, synthesizes with an LLM, and appends findings to the wiki. Separated into sections and timelines. Lightweight MD files that allow any agent to reference anything that happened in the past.

## Setup

**Recommended:** Ask your agent:

```
Clone https://github.com/retnine9/Self-Updating-Context-Wiki-for-IDE-Agents
and follow docs/SETUP.md on this machine.
```

| Scenario | Path |
|----------|------|
| Cursor agent install | [docs/SETUP.md](docs/SETUP.md) |
| Try without installing | [Examples mode](#quick-start-examples-mode) below |
| Optional script shortcut | `install/install.ps1` (Windows) or `install/install.sh` (macOS/Linux) |
| Other IDEs | [docs/AGENT_ADAPTERS.md](docs/AGENT_ADAPTERS.md) |
| Problems | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

After install, verify with:

```bash
python ~/.cursor/wiki/scripts/doctor.py
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

**Skip one session:** touch `~/.cursor/context/.wiki_skip` or set `"auto_update_on_session_start": false` in `wiki_config.json`.

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
~/.cursor/context/
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

Runtime (scripts, hooks) lives in `~/.cursor/wiki/` — separate from wiki data. See [Architecture](docs/ARCHITECTURE.md).

## Documentation

- [Setup (agent checklist)](docs/SETUP.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Cursor integration](docs/CURSOR_INTEGRATION.md)
- [Other agent adapters](docs/AGENT_ADAPTERS.md)

## License

MIT
