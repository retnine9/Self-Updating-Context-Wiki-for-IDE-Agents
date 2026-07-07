#!/usr/bin/env bash
# inject-wiki-drain.sh -- beforeSubmitPrompt: synthesis mandate (one-shot)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_HOME="${WIKI_HOME:-$HOME/.cursor/wiki}"
ENV_FILE="$WIKI_HOME/wiki.env"
CONTEXT_DIR="${CONTEXT_WIKI_DIR:-$HOME/.cursor/context}"
DRAIN_FILE="$CONTEXT_DIR/.drain_required.json"
INJECTED_FILE="$CONTEXT_DIR/.drain_injected"

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

if [[ ! -f "$DRAIN_FILE" ]] || [[ -f "$INJECTED_FILE" ]]; then
  echo "{}"
  exit 0
fi

COUNT=$("$PYTHON" -c "import json; print(json.load(open('$DRAIN_FILE'))['count'])" 2>/dev/null || echo "0")
touch "$INJECTED_FILE"

MSG="MANDATORY CONTEXT WIKI DRAIN: ${COUNT} session(s) need synthesis before addressing the user request. Run: python $WIKI_HOME/scripts/update_wiki.py --manifest then complete Layer 2+3 and run --complete."

"$PYTHON" -c "import json; print(json.dumps({'agent_message': '''$MSG'''}))"
