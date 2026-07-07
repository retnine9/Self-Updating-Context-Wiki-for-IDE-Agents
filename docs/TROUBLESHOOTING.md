# Troubleshooting

Run doctor first:

```bash
python ~/.context-wiki/runtime/scripts/doctor.py --platform cursor
```

For agents: `python ~/.context-wiki/runtime/scripts/doctor.py --json`

Exit codes: **0** pass, **1** warnings, **2** failures.

---

## Symptom → fix

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Hooks never fire | `hooks.json` missing wiki entries | [SETUP.md step 7](SETUP.md#7-merge-hooks-append-do-not-replace) |
| Hooks fire but nothing happens | Python not found | [SETUP.md step 2](SETUP.md#2-find-python) — set `WIKI_PYTHON` in `wiki.env` |
| `python` not recognized (Windows) | Python not on PATH | Use full path in `wiki.env` or install from python.org |
| Works until clone deleted | Hooks point at clone path | Re-install: runtime must live in `~/.context-wiki/runtime/` |
| 0 sessions extracted | No transcripts yet | Normal for new users; run a session first |
| 0 sessions extracted (existing user) | Wrong transcript path | Set `WIKI_PROJECT_CWD`, `CURSOR_PROJECT_SLUG`, or `TRANSCRIPTS_DIR` in env |
| Synthesis never runs | Pending queue empty | Check `wiki_state.json` → `pending_sessions` |
| Synthesis skipped | `.wiki_skip` exists | Delete `~/.context-wiki/data/.wiki_skip` |
| Synthesis skipped | Config disabled | Set `"auto_update_on_session_start": true` in `wiki_config.json` |
| Doctor fails `wiki_runtime` | Runtime not copied | [SETUP.md step 3](SETUP.md#3-copy-runtime-to-cursorwiki) |
| Doctor fails `rules` | Rules not copied | [SETUP.md step 4](SETUP.md#4-copy-rules) |
| Doctor fails `context_dir` | Dirs missing | [SETUP.md step 6](SETUP.md#6-initialize-context-data-only-if-missing) |
| Re-install wiped sessions | Used wrong install script | Never delete `sessions/`; use SETUP or `install_wiki.py` |
| Other hooks disappeared | Old install replaced arrays | Re-merge hooks manually; new install **appends** only |

---

## Doctor check reference

| Check | Pass | Warn | Fail |
|-------|------|------|------|
| `python` | Python 3 found | — | No Python |
| `wiki_runtime` | `~/.context-wiki/runtime/scripts/update_wiki.py` | Dev mode from clone | Missing runtime |
| `context_dir` | Writable + subdirs | — | Missing / not writable |
| `transcripts` | Found JSONL | New user, none yet | — |
| `hooks` | Wiki hooks configured | — | Missing entries |
| `rules` | 3 `.mdc` files | — | Missing rules |
| `wiki_state` | Readable | Not created yet | Corrupt JSON |
| `log` | Recent entries | No log yet | — |

---

## Logs

- Hook activity: `~/.context-wiki/data/wiki.log` (legacy: `~/.cursor/context/wiki.log`)
- Cursor: **Hooks** output channel (View → Output → Hooks)

---

## Manual test

```bash
export CONTEXT_WIKI_DIR=~/.context-wiki/data   # or $env:CONTEXT_WIKI_DIR on Windows
python ~/.context-wiki/runtime/scripts/update_wiki.py --status
python ~/.context-wiki/runtime/scripts/update_wiki.py --all
```

---

## Still stuck?

1. Re-run full install: `python <clone>/scripts/install_wiki.py --source-repo <clone>`
2. Run doctor with `--json` and share output
3. Open an issue with doctor JSON (redact paths if needed)
