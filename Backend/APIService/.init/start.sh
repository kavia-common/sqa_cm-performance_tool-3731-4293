#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/sqa_cm-performance_tool-3731-4293/Backend/APIService"
cd "$WS"
export PORT=${PORT:-8000}
export APP_ENV=${APP_ENV:-development}
LOG=${LOG:-/tmp/apservice_uvicorn.log}
# Prefer venv python if present
if [ -x "$WS/.venv/bin/python" ]; then
  VBIN="$WS/.venv/bin/python"
else
  VBIN="python3"
fi
# If start_uvicorn.sh exists, use it; otherwise run uvicorn directly
if [ -x "$WS/start_uvicorn.sh" ]; then
  "$WS/start_uvicorn.sh" >"$LOG" 2>&1 &
  echo $! > /tmp/apservice_uvicorn.pid
else
  # fallback: attempt to run uvicorn module pointing to app.main:app
  "$VBIN" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" >"$LOG" 2>&1 &
  echo $! > /tmp/apservice_uvicorn.pid
fi
sleep 0.2
# report pid
cat /tmp/apservice_uvicorn.pid
