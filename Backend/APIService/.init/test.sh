#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/sqa_cm-performance_tool-3731-4293/Backend/APIService"
cd "$WS"
PYBIN="python3"
if [ -x "$WS/.venv/bin/python" ]; then PYBIN="$WS/.venv/bin/python"; fi
# run pytest if available
if command -v pytest >/dev/null 2>&1; then
  "$PYBIN" -m pytest -q
else
  echo 'pytest not found, skipping' >&2
  exit 3
fi
