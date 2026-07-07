# Setup — Agent Checklist

Primary install path: **clone this repo and follow these steps**. No opaque scripts required.

Optional shortcut (same steps): `install/install.ps1` (Windows) or `install/install.sh` (macOS/Linux).

---

## User prompt (copy-paste)

> Clone https://github.com/retnine9/Self-Updating-Context-Wiki-for-IDE-Agents and follow docs/SETUP.md to install the context wiki on this machine. Run doctor.py when finished and report results.

---

## Prerequisites

- [Cursor](https://cursor.com) with hooks enabled
- Python 3.8+ (for Layer 1 extraction — no API keys)

---

## Steps

### 1. Clone to a stable path

```powershell
# Windows
git clone https://github.com/retnine9/Self-Updating-Context-Wiki-for-IDE-Agents.git $env:USERPROFILE\tools\context-wiki
```

```bash
# macOS / Linux
git clone https://github.com/retnine9/Self-Updating-Context-Wiki-for-IDE-Agents.git ~/tools/context-wiki
```

**Verify:** `ls <clone>/scripts/update_wiki.py` exists.

---

### 2. Find Python

From the clone directory:

```bash
python scripts/find_python.py
python scripts/find_python.py --write-env
```

This writes `~/.cursor/wiki/wiki.env` with `WIKI_PYTHON`, `WIKI_HOME`, and `CONTEXT_WIKI_DIR`.

**Verify:** `~/.cursor/wiki/wiki.env` exists and `WIKI_PYTHON` runs `python -c "import sys; print(sys.version_info.major)"` → `3`.

If Python is not on PATH (common on Windows), use the full path:

```
WIKI_PYTHON=C:\Users\you\AppData\Local\Python\pythoncore-3.14-64\python.exe
```

---

### 3. Copy runtime to `~/.cursor/wiki/`

Copy these directories from the clone into `~/.cursor/wiki/`:

- `lib/`
- `scripts/`
- `hooks/`

Overwrite on re-install. **Preserve** existing `~/.cursor/wiki/wiki.env` if present.

**Or run the installer:**

```bash
python scripts/install_wiki.py --source-repo <clone-path>
```

**Verify:** `~/.cursor/wiki/scripts/update_wiki.py` exists.

---

### 4. Copy rules

Copy `cursor/rules/*.mdc` → `~/.cursor/rules/`

Do **not** delete other rules.

**Verify:** these three files exist:

- `~/.cursor/rules/context-wiki.mdc`
- `~/.cursor/rules/context-wiki-drain.mdc`
- `~/.cursor/rules/decision-capture.mdc`

---

### 5. Copy skills

Copy to `~/.cursor/skills/`:

- `skills/lint-context/` → `~/.cursor/skills/lint-context/`
- `skills/setup-context-wiki/` → `~/.cursor/skills/setup-context-wiki/`

**Verify:** `~/.cursor/skills/lint-context/SKILL.md` exists.

---

### 6. Initialize context data (only if missing)

Create `~/.cursor/context/` with:

```
sessions/
extracts/
synthesis/
```

If `synthesis/` is empty, copy templates from `templates/synthesis/*.md`.

If missing, also create:

- `wiki_config.json` from `templates/wiki_config.example.json`
- `wiki_state.json` as `{"last_extract":null,"last_synthesis":null,"pending_sessions":[]}`
- `INDEX.md` with a header

**Never delete or overwrite existing `sessions/` or `synthesis/` content on re-install.**

**Verify:** `~/.cursor/context/sessions/` is writable.

---

### 7. Merge hooks (append, do not replace)

Edit `~/.cursor/hooks.json`. **Append** wiki hook entries; do not remove existing hooks.

**Windows** — use absolute paths to `~/.cursor/wiki/hooks/`:

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{
      "command": "powershell -ExecutionPolicy Bypass -File C:\\Users\\YOU\\.cursor\\wiki\\hooks\\wiki-on-start.ps1",
      "timeout": 120
    }],
    "beforeSubmitPrompt": [{
      "command": "powershell -ExecutionPolicy Bypass -File C:\\Users\\YOU\\.cursor\\wiki\\hooks\\inject-wiki-drain.ps1",
      "matcher": "UserPromptSubmit",
      "timeout": 15
    }]
  }
}
```

**macOS / Linux** — use bash hooks:

```json
"sessionStart": [{
  "command": "bash /Users/YOU/.cursor/wiki/hooks/wiki-on-start.sh",
  "timeout": 120
}]
```

If wiki hooks already exist, update their paths only — do not wipe other entries in `sessionStart` or `beforeSubmitPrompt`.

**Verify:** hook commands point at `~/.cursor/wiki/hooks/`, not the clone path.

---

### 8. Write `install.json`

Create `~/.cursor/wiki/install.json`:

```json
{
  "version": 1,
  "installed_at": "2026-07-07T00:00:00Z",
  "source_repo": "/path/to/clone",
  "wiki_home": "/Users/you/.cursor/wiki"
}
```

`install_wiki.py` writes this automatically.

---

### 9. Run doctor

```bash
python ~/.cursor/wiki/scripts/doctor.py
```

Exit codes:

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | Warnings only (e.g. no transcripts yet) |
| 2 | Failures — fix before declaring done |

Agents: use `python ~/.cursor/wiki/scripts/doctor.py --json` for structured output.

**Verify:** exit code 0 or 1 (warnings OK for new users).

---

### 10. Restart Cursor

Start a new Cursor session. Check the **Hooks** output channel for `sessionStart` activity.

---

## Layout after install

```
~/.cursor/
  wiki/                 # runtime (survives clone deletion)
    lib/
    scripts/
    hooks/
    wiki.env
    install.json
  context/              # data (your wiki)
    sessions/
    extracts/
    synthesis/
    wiki_state.json
  rules/
  skills/
  hooks.json
```

---

## Re-install / update

1. `git pull` in the clone
2. Re-run step 3 (copy runtime) or `python scripts/install_wiki.py --source-repo <clone>`
3. Run doctor again

Existing sessions and synthesis are preserved.

---

## Advanced (out of scope)

Project-level install (`.context-wiki/` inside a repo) is not supported in this release. Use `CONTEXT_WIKI_DIR` to point at a custom data directory.

---

## Examples mode (no install)

```powershell
$env:CONTEXT_WIKI_DIR = "$PWD\examples"
python scripts/doctor.py
python scripts/update_wiki.py --status
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
