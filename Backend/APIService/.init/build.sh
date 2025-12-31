#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/sqa_cm-performance_tool-3731-4293/Backend/APIService"
cd "$WS"
# Validate imports using workspace venv python when available
PYBIN="python3"
if [ -x "$WS/.venv/bin/python" ]; then PYBIN="$WS/.venv/bin/python"; fi
# Simple import check: try importing the app module
# Adjust module path if app lives under app/main.py -> module app.main
"$PYBIN" - <<'PY'
import importlib,sys
try:
    importlib.import_module('app.main')
except Exception as e:
    print('import check failed:', repr(e), file=sys.stderr)
    sys.exit(2)
print('import_ok')
PY
