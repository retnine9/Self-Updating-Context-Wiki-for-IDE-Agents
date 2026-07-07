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

- Copies runtime to `~/.context-wiki/runtime/` (survives clone deletion)
- Migrates legacy `~/.cursor/wiki` + `~/.cursor/context` if present (leaves back-compat symlinks)
- Copies rules and skills
- Initializes `~/.context-wiki/data/` only if missing
- **Appends** wiki hooks (does not replace other hooks)
- Writes `wiki.env` and `install.json`
- Runs `doctor.py`

Restart Cursor after install.

## Verify

```bash
python ~/.context-wiki/runtime/scripts/doctor.py --platform cursor
python ~/.context-wiki/runtime/scripts/update_wiki.py --status
```

Check Cursor **Hooks** output channel after starting a new session.

## Manual install (fallback)

If you cannot run `install_wiki.py`, follow [SETUP.md](SETUP.md) steps manually.

### Hooks

Merge into `~/.cursor/hooks.json` — **append** entries, use absolute paths to `~/.context-wiki/runtime/hooks/` (or legacy `~/.cursor/wiki/hooks/` after migration):

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{
      "command": "python ~/.context-wiki/runtime/hooks/wiki_on_start.py",
      "timeout": 120
    }],
    "beforeSubmitPrompt": [{
      "command": "python ~/.context-wiki/runtime/hooks/inject_wiki_drain.py",
      "matcher": "UserPromptSubmit",
      "timeout": 15
    }]
  }
}
```

On Windows, the installer may use PowerShell wrappers (`wiki-on-start.ps1`, `inject-wiki-drain.ps1`) instead. On macOS/Linux, `.sh` wrappers are equivalent.

### Rules

Copy `cursor/rules/*.mdc` to `~/.cursor/rules/`.

### Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `WIKI_HOME` | `~/.context-wiki/runtime` | Runtime (scripts, hooks) |
| `CONTEXT_WIKI_DIR` | `~/.context-wiki/data` | Wiki data directory |
| `WIKI_PYTHON` | auto-detect | Python for hooks (see `wiki.env`) |
| `synthesis_model` in `wiki_config.json` | `claude-4.5-haiku-thinking` | Model for Layer 2+3 subagents (e.g. `composer-2.5-fast`) |
| `CURSOR_PROJECT_SLUG` | auto-detect | Transcript source project |
| `TRANSCRIPTS_DIR` | auto-detect | Override transcript path |

## Skip Wiki Update for One Session

```powershell
New-Item ~/.context-wiki/data/.wiki_skip
```

Or set `"auto_update_on_session_start": false` in `~/.context-wiki/data/wiki_config.json`.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
