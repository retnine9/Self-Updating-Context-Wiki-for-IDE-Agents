---
name: lint-context
description: >-
  Health-check the 6 context wiki synthesis files. Checks stale open questions,
  resolved errors still active, orphan sessions, and draft rules/skills already
  installed. Outputs synthesis/LINT_REPORT.md. Use when the user says "lint context"
  or "check the wiki".
---

# Lint Context

Read all six files in `context/synthesis/`, plus `INDEX.md` and the extracts directory.

## Checks

1. **OPEN_QUESTIONS.md** — items marked open with resolution evidence in recent extracts
2. **ERROR_REFERENCE.md** — fixes confirmed in current codebase (Grep key symbols)
3. **RULES_DRAFT.md** — drafts that match installed `.mdc` rules → tag `[INSTALLED]`
4. **SKILLS_DRAFT.md** — drafts that match installed skills → tag `[INSTALLED]`
5. **Orphan sessions** — INDEX.md entries without matching extract files
6. **CAUSAL_MAP.md** — claims that contradict live code (when project is available)

## Output

Write `context/synthesis/LINT_REPORT.md` with `[FIXABLE]` vs `[HUMAN JUDGMENT]` items.

Do NOT re-synthesize. Do NOT call external APIs. Flag contradictions; do not silently fix without user approval.

Update `wiki_state.json` with `"last_lint": "<ISO timestamp>"` after running.
