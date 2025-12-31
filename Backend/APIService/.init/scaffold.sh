#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/sqa_cm-performance_tool-3731-4293/Backend/APIService"
cd "$WS"
# Create a minimal .env.example if missing. Do NOT write real secrets in automation.
if [ ! -f "$WS/.env.example" ]; then
  cat > "$WS/.env.example" <<'ENV'
# Example environment (do NOT commit real secrets)
# Use .env for local overrides; prefer CI/CD secret stores for pipelines.
# Automation-friendly secure defaults:
# - Use empty/default non-sensitive values here.
# - For secrets, set them via the environment or a secure vault.
# - When creating a local .env with secrets, restrict permissions:
#     chmod 600 .env
# - Avoid checking .env into VCS. Add ".env" to .gitignore.

APP_ENV=development
HOST=0.0.0.0
PORT=8000
# Example non-secret placeholders:
DATABASE_URL=sqlite:///./data.db
# SECRET_KEY should be set in the environment or vault; do not store here:
# SECRET_KEY=
ENV
fi
# Do not create a .env with secrets in automation; instruct the operator instead.
# Ensure .env is gitignored - append if not present
if [ -f ".gitignore" ] && ! grep -q "^\.env$" .gitignore; then
  printf "%s\n" "# Local environment variables (do not commit)" ".env" >> .gitignore
fi
# Informational output (minimal)
printf "Created/verified: %s/.env.example\n" "$WS"
