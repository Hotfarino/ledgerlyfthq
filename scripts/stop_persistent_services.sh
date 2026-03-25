#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

pkill -f "${BACKEND_DIR}/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000" 2>/dev/null || true
pkill -f "${FRONTEND_DIR}/node_modules/.bin/next start --hostname 127.0.0.1 --port 3001" 2>/dev/null || true

echo "Requested stop for persistent backend/frontend services."
