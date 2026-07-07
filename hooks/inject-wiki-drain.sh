#!/usr/bin/env bash
# inject-wiki-drain.sh -- beforeSubmitPrompt: synthesis mandate (one-shot)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTEXT_DIR="${CONTEXT_WIKI_DIR:-$HOME/.cursor/context}"
DRAIN_FILE="$CONTEXT_DIR/.drain_required.json"
INJECTED_FILE="$CONTEXT_DIR/.drain_injected"

if [[ ! -f "$DRAIN_FILE" ]] || [[ -f "$INJECTED_FILE" ]]; then
  echo "{}"
  exit 0
fi

COUNT=$(python3 -c "import json; print(json.load(open('$DRAIN_FILE'))['count'])" 2>/dev/null || echo "0")
touch "$INJECTED_FILE"

MSG="MANDATORY CONTEXT WIKI DRAIN: ${COUNT} session(s) need synthesis before addressing the user request. Run: python $REPO_ROOT/scripts/update_wiki.py --manifest then complete Layer 2+3 and run --complete."

python3 -c "import json; print(json.dumps({'agent_message': '''$MSG'''}))"
