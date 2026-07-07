# Self-Updating-Context-Wiki-for-IDE-Agents

Functions as a wikipedia on a repository or project for autonomous or directed AI agents. Designed to be used with tools such as Cursor, Claude Code, Codex, etc. Automatically reads new session extracts, synthesizes with an LLM, and appends findings to the wiki. Separated into sections and timelines. Lightweight MD files that allow any agent to reference anything that happened in the past.

## How It Works

| Layer | What | Runs on |
|-------|------|---------|
| 1 | JSONL → readable session markdown | Python (`update_wiki.py --extract`) |
| 2 | Session → 7-section extract | Agent LLM |
| 3 | Extracts → cross-session wiki | Agent LLM |

No API keys needed.

## Triggers

| When | What happens |
|------|----------------|
| **New session starts** | Scan transcripts, extract new sessions (skippable) |
| **First message** (if pending) | Agent synthesizes extracts + wiki before your request |
| **Manual** | `python scripts/update_wiki.py --all` or ask the agent |

**Skip one session:** touch `context/.wiki_skip` or set `"auto_update_on_session_start": false` in `wiki_config.json`.

## Quick Start (examples mode)

```powershell
git clone https://github.com/retnine9/Self-Updating-Context-Wiki-for-IDE-Agents.git
cd Self-Updating-Context-Wiki-for-IDE-Agents

$env:CONTEXT_WIKI_DIR = "$PWD\examples"
python scripts/update_wiki.py --status
python scripts/update_wiki.py --manifest
```

The examples directory has 3 fictional sessions; one is pending synthesis (`c9d0e1f2`) to demonstrate the drain flow.

## Install (Cursor)

```powershell
.\install\install.ps1
```

See [docs/CURSOR_INTEGRATION.md](docs/CURSOR_INTEGRATION.md) for manual setup.

## Wiki Files

```
context/
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

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Cursor integration](docs/CURSOR_INTEGRATION.md)
- [Other agent adapters](docs/AGENT_ADAPTERS.md)

## License

MIT
