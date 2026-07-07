#!/usr/bin/env bash
# wiki-on-start.sh -- sessionStart: extract + prepare
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_HOME="${WIKI_HOME:-$HOME/.cursor/wiki}"
ENV_FILE="$WIKI_HOME/wiki.env"
CONTEXT_DIR="${CONTEXT_WIKI_DIR:-$HOME/.cursor/context}"
SKIP_FILE="$CONTEXT_DIR/.wiki_skip"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ ! -f "$WIKI_HOME/install.json" ]]; then
  WIKI_HOME="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

PYTHON="${WIKI_PYTHON:-python3}"
if ! command -v "$PYTHON" &>/dev/null && command -v python3 &>/dev/null; then
  PYTHON="python3"
fi

log() { echo "[$(date -Iseconds)] hook: $*" >> "$CONTEXT_DIR/wiki.log" 2>/dev/null || true; }

if [[ -f "$SKIP_FILE" ]]; then
  log "sessionStart skipped (.wiki_skip)"
  rm -f "$SKIP_FILE"
  echo "{}"
  exit 0
fi

export CONTEXT_WIKI_DIR="$CONTEXT_DIR"
export WIKI_HOME="$WIKI_HOME"
log "sessionStart: update_wiki.py --all (wiki=$WIKI_HOME)"
"$PYTHON" "$WIKI_HOME/scripts/update_wiki.py" --all 2>&1 | while read -r line; do log "$line"; done || true

echo "{}"
