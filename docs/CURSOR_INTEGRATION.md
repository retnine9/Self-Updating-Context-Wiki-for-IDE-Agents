# Cursor Integration

## Quick Install

1. Clone this repo anywhere (e.g. `~/Self-Updating-Context-Wiki-for-IDE-Agents`).
2. Run `install/install.ps1` (Windows) or `install/install.sh` (macOS/Linux).
3. Restart Cursor.

The install script:
- Copies rules to `~/.cursor/rules/`
- Copies the lint skill to `~/.cursor/skills/lint-context/`
- Merges hook entries into `~/.cursor/hooks.json` with absolute paths to this repo
- Creates `~/.cursor/context/` from templates if missing

## Manual Install

### Hooks

Merge into `~/.cursor/hooks.json` (adjust `REPO` path):

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{
      "command": "powershell -ExecutionPolicy Bypass -File REPO/hooks/wiki-on-start.ps1",
      "timeout": 120
    }],
    "beforeSubmitPrompt": [{
      "command": "powershell -ExecutionPolicy Bypass -File REPO/hooks/inject-wiki-drain.ps1",
      "matcher": "UserPromptSubmit",
      "timeout": 15
    }]
  }
}
```

### Rules

Copy `cursor/rules/*.mdc` to `~/.cursor/rules/`.

### Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `CONTEXT_WIKI_DIR` | `~/.cursor/context` | Wiki data directory |
| `CURSOR_PROJECT_SLUG` | auto-detect | Transcript source project |
| `TRANSCRIPTS_DIR` | auto-detect | Override transcript path |
| `WIKI_PYTHON` | `python` | Python executable for hooks |

## Skip Wiki Update for One Session

```powershell
New-Item ~/.cursor/context/.wiki_skip
```

Or set `"auto_update_on_session_start": false` in `~/.cursor/context/wiki_config.json`.

## Verify

```powershell
$env:CONTEXT_WIKI_DIR = "$HOME\.cursor\context"
python path\to\repo\scripts\update_wiki.py --status
```

Check Cursor **Hooks** output channel after starting a new session.
