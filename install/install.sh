#!/usr/bin/env bash
# Optional shortcut — same steps as docs/SETUP.md
# Installs context wiki runtime to ~/.cursor/wiki/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLER="${REPO_ROOT}/scripts/install_wiki.py"

echo "Context Wiki install (optional shortcut — see docs/SETUP.md)"
echo "Source: ${REPO_ROOT}"

if [[ ! -f "${INSTALLER}" ]]; then
  echo "ERROR: Missing ${INSTALLER} — clone the full repository first." >&2
  exit 1
fi

PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    PYTHON="$cmd"
    break
  fi
done
if [[ -z "${PYTHON}" ]]; then
  echo "ERROR: Python 3 not found. Install Python 3 and retry." >&2
  exit 1
fi

echo "Using Python: ${PYTHON}"
"${PYTHON}" "${INSTALLER}" --source-repo "${REPO_ROOT}" --bash-hooks
exit $?
