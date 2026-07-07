---
name: setup-context-wiki
description: >-
  Install the self-updating context wiki for Cursor. Clone the repo and follow
  docs/SETUP.md: copy runtime to ~/.cursor/wiki/, merge hooks, init context,
  run doctor.py. Use when the user asks to set up, install, or configure the
  context wiki.
---

# Setup Context Wiki

Follow [docs/SETUP.md](../../docs/SETUP.md) in the cloned repository. Summary for agents:

## Quick path

```bash
git clone https://github.com/retnine9/Self-Updating-Context-Wiki-for-IDE-Agents.git ~/tools/context-wiki
cd ~/tools/context-wiki
python scripts/install_wiki.py --source-repo .
```

On macOS/Linux add `--bash-hooks` if not using PowerShell hooks.

## Manual steps (if installer unavailable)

1. **Find Python** — `python scripts/find_python.py --write-env`
2. **Copy runtime** — `lib/`, `scripts/`, `hooks/` → `~/.cursor/wiki/`
3. **Copy rules** — `cursor/rules/*.mdc` → `~/.cursor/rules/`
4. **Copy skills** — `lint-context/`, `setup-context-wiki/` → `~/.cursor/skills/`
5. **Init context** — create `~/.cursor/context/{sessions,extracts,synthesis}` only if missing; never wipe existing sessions
6. **Merge hooks** — append wiki entries to `~/.cursor/hooks.json` with absolute paths to `~/.cursor/wiki/hooks/`
7. **Write install.json** — version, timestamp, source_repo path
8. **Run doctor** — `python ~/.cursor/wiki/scripts/doctor.py` must exit 0 or 1
9. **Tell user** to restart Cursor

## Verification

```bash
python ~/.cursor/wiki/scripts/doctor.py --json
```

Report each check status. Exit code 2 = failures remain.

## Constraints

- Hooks must point at `~/.cursor/wiki/`, not the clone path
- Append hooks — never replace entire `sessionStart` / `beforeSubmitPrompt` arrays
- Preserve existing `~/.cursor/context/sessions/` and `synthesis/` on re-install

## Troubleshooting

See [docs/TROUBLESHOOTING.md](../../docs/TROUBLESHOOTING.md).
