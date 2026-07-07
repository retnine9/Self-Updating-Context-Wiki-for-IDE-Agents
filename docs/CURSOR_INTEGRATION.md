# Cursor Integration

## Primary install

Follow [SETUP.md](SETUP.md) — clone the repo and have your agent run the checklist, or use the optional install script:

```powershell
.\install\install.ps1
```

```bash
./install/install.sh
```

Both scripts call `scripts/install_wiki.py`, which:

- Copies runtime to `~/.cursor/wiki/` (survives clone deletion)
- Copies rules and skills
- Initializes `~/.cursor/context/` only if missing
- **Appends** wiki hooks (does not replace other hooks)
- Writes `wiki.env` and `install.json`
- Runs `doctor.py`

Restart Cursor after install.

## Verify

```bash
python ~/.cursor/wiki/scripts/doctor.py
python ~/.cursor/wiki/scripts/update_wiki.py --status
```

Check Cursor **Hooks** output channel after starting a new session.

## Manual install (fallback)

If you cannot run `install_wiki.py`, follow [SETUP.md](SETUP.md) steps manually.

### Hooks

Merge into `~/.cursor/hooks.json` — **append** entries, use absolute paths to `~/.cursor/wiki/hooks/`:

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{
      "command": "powershell -ExecutionPolicy Bypass -File ~/.cursor/wiki/hooks/wiki-on-start.ps1",
      "timeout": 120
    }],
    "beforeSubmitPrompt": [{
      "command": "powershell -ExecutionPolicy Bypass -File ~/.cursor/wiki/hooks/inject-wiki-drain.ps1",
      "matcher": "UserPromptSubmit",
      "timeout": 15
    }]
  }
}
```

On macOS/Linux, use `bash ~/.cursor/wiki/hooks/wiki-on-start.sh` instead.

### Rules

Copy `cursor/rules/*.mdc` to `~/.cursor/rules/`.

### Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `WIKI_HOME` | `~/.cursor/wiki` | Runtime (scripts, hooks) |
| `CONTEXT_WIKI_DIR` | `~/.cursor/context` | Wiki data directory |
| `WIKI_PYTHON` | auto-detect | Python for hooks (see `wiki.env`) |
| `synthesis_model` in `wiki_config.json` | `claude-4.5-haiku-thinking` | Model for Layer 2+3 subagents (e.g. `composer-2.5-fast`) |
| `CURSOR_PROJECT_SLUG` | auto-detect | Transcript source project |
| `TRANSCRIPTS_DIR` | auto-detect | Override transcript path |

## Skip Wiki Update for One Session

```powershell
New-Item ~/.cursor/context/.wiki_skip
```

Or set `"auto_update_on_session_start": false` in `~/.cursor/context/wiki_config.json`.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
