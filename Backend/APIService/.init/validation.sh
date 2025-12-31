#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/sqa_cm-performance_tool-3731-4293/Backend/APIService"
cd "$WS"
export PORT=${PORT:-8000}
export APP_ENV=${APP_ENV:-development}
LOG=/tmp/apservice_uvicorn.log
# Build (import check)
if [ -x "$WS/.venv/bin/python" ]; then PYBIN="$WS/.venv/bin/python"; else PYBIN="python3"; fi
"$PYBIN" - <<'PY' || { echo "build/import check failed" >&2; exit 52; }
import importlib,sys
try:
    importlib.import_module('app.main')
except Exception as e:
    print('import check failed:', repr(e), file=sys.stderr)
    sys.exit(1)
print('import_ok')
PY
# Start server in background via start script
if [ -x "$WS/start_uvicorn.sh" ]; then
  "$WS/start_uvicorn.sh" >"$LOG" 2>&1 &
  PID=$!
else
  # fallback to venv/system uvicorn
  "$PYBIN" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" >"$LOG" 2>&1 &
  PID=$!
fi
trap 'kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true' EXIT INT TERM
# Wait for server readiness (up to 30s)
TIMEOUT=${TIMEOUT:-30}
READY=1
for i in $(seq 1 "$TIMEOUT"); do
  if curl --fail --silent --show-error --max-time 3 "http://127.0.0.1:$PORT/health" | "$PYBIN" -c "import sys,json
try:
 j=json.load(sys.stdin)
except Exception:
 sys.exit(1)
sys.exit(0 if j.get('status')=='ok' else 1)"; then
    READY=0; break
  fi
  sleep 1
  if ! kill -0 "$PID" 2>/dev/null; then echo "server process exited prematurely" >&2; exit 50; fi
done
if [ "$READY" -ne 0 ]; then echo "validation failed: /health not responding within timeout" >&2; kill "$PID" 2>/dev/null || true; exit 51; fi
# Evidence
echo "server_responding"
head -n 200 "$LOG" || true
# Clean shutdown
kill "$PID" || true
wait "$PID" 2>/dev/null || true
trap - EXIT INT TERM
