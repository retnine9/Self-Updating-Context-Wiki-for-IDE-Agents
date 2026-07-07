#!/usr/bin/env bash
# Install context wiki into ~/.cursor/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURSOR_DIR="${HOME}/.cursor"
CONTEXT_DIR="${CURSOR_DIR}/context"

echo "Installing from: $REPO_ROOT"

mkdir -p "${CURSOR_DIR}/rules"
cp "${REPO_ROOT}/cursor/rules/"*.mdc "${CURSOR_DIR}/rules/"

mkdir -p "${CURSOR_DIR}/skills/lint-context"
cp "${REPO_ROOT}/skills/lint-context/SKILL.md" "${CURSOR_DIR}/skills/lint-context/"

mkdir -p "${CONTEXT_DIR}/sessions" "${CONTEXT_DIR}/extracts" "${CONTEXT_DIR}/synthesis"
for f in "${REPO_ROOT}/templates/synthesis/"*.md; do
  base=$(basename "$f")
  [[ -f "${CONTEXT_DIR}/synthesis/${base}" ]] || cp "$f" "${CONTEXT_DIR}/synthesis/${base}"
done

[[ -f "${CONTEXT_DIR}/wiki_config.json" ]] || cp "${REPO_ROOT}/templates/wiki_config.example.json" "${CONTEXT_DIR}/wiki_config.json"
[[ -f "${CONTEXT_DIR}/wiki_state.json" ]] || echo '{"last_extract":null,"last_synthesis":null,"pending_sessions":[]}' > "${CONTEXT_DIR}/wiki_state.json"
[[ -f "${CONTEXT_DIR}/INDEX.md" ]] || printf '# Session Index\n\n*No sessions yet.*\n' > "${CONTEXT_DIR}/INDEX.md"

HOOKS_FILE="${CURSOR_DIR}/hooks.json"
echo "Merge hooks manually — see docs/CURSOR_INTEGRATION.md"
echo "Repo hooks: ${REPO_ROOT}/hooks/"
echo "Done."
