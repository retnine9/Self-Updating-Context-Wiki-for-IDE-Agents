#!/usr/bin/env bash
# wiki-on-start.sh -- sessionStart: extract + prepare
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTEXT_DIR="${CONTEXT_WIKI_DIR:-$HOME/.cursor/context}"
SKIP_FILE="$CONTEXT_DIR/.wiki_skip"
PYTHON="${WIKI_PYTHON:-python3}"

log() { echo "[$(date -Iseconds)] hook: $*" >> "$CONTEXT_DIR/wiki.log" 2>/dev/null || true; }

if [[ -f "$SKIP_FILE" ]]; then
  log "sessionStart skipped (.wiki_skip)"
  rm -f "$SKIP_FILE"
  echo "{}"
  exit 0
fi

export CONTEXT_WIKI_DIR="$CONTEXT_DIR"
log "sessionStart: update_wiki.py --all"
"$PYTHON" "$REPO_ROOT/scripts/update_wiki.py" --all 2>&1 | while read -r line; do log "$line"; done || true

echo "{}"
