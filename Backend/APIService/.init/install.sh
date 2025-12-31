#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/sqa_cm-performance_tool-3731-4293/Backend/APIService"
cd "$WS"
# Require workspace venv; fail fast if missing or broken
if [ ! -x "$WS/.venv/bin/python" ]; then echo "workspace venv missing or broken; ensure env-1 succeeded" >&2; exit 20; fi
PYBIN="$WS/.venv/bin/python"
PIP_CMD=("$PYBIN" -m pip)
# Upgrade pip in venv (quiet)
"${PIP_CMD[@]}" install --upgrade pip -q
# Install deps from requirements.txt into the venv (non-interactive)
if [ -f "$WS/requirements.txt" ]; then
  "${PIP_CMD[@]}" install -q --no-input -r "$WS/requirements.txt"
else
  "${PIP_CMD[@]}" install -q --no-input fastapi uvicorn[standard] httpx requests python-dotenv pytest
fi
# After install, record venv-only freeze into requirements.lock (deterministic for this venv)
"${PIP_CMD[@]}" freeze > "$WS/requirements.lock"
# Print uvicorn and fastapi versions installed in venv (or not-installed)
"$PYBIN" - <<'PY'
import pkg_resources
for pkg in ('uvicorn','fastapi'):
    try:
        v=pkg_resources.get_distribution(pkg).version
        print(pkg+':'+v)
    except Exception:
        print(pkg+':not-installed')
PY
# Validate uvicorn import in chosen interpreter
if ! "$PYBIN" -c "import importlib,sys
try:
  importlib.import_module('uvicorn')
except Exception as e:
  sys.stderr.write('uvicorn import failed in venv: %s\n'%e); sys.exit(21)
"; then
  echo 'uvicorn installation failed in venv' >&2; exit 22
fi

# Success marker
echo "dependencies: install step completed; requirements.lock written at $WS/requirements.lock"
