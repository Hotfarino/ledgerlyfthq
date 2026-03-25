#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

is_listening() {
  local port="$1"
  lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
}

start_backend() {
  if is_listening 8000; then
    echo "Backend already running on 8000"
    return
  fi

  (
    cd "${BACKEND_DIR}"
    if [[ ! -d .venv ]]; then
      python3 -m venv .venv
    fi
    source .venv/bin/activate
    pip install -r requirements.txt >/tmp/ledgerlyfthq_backend_pip.log 2>&1
    nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 >/tmp/ledgerlyfthq_backend.log 2>/tmp/ledgerlyfthq_backend.error.log &
  )

  sleep 1
  if is_listening 8000; then
    echo "Backend started on 8000"
  else
    echo "Backend did not start (check /tmp/ledgerlyfthq_backend.error.log)"
  fi
}

start_frontend() {
  if is_listening 3001; then
    echo "Frontend already running on 3001"
    return
  fi

  (
    cd "${FRONTEND_DIR}"
    npm install >/tmp/ledgerlyfthq_frontend_npm_install.log 2>&1
    if [[ ! -f .next/BUILD_ID ]]; then
      npm run build >/tmp/ledgerlyfthq_frontend_build.log 2>&1
    fi
    nohup npm run start -- --hostname 127.0.0.1 --port 3001 >/tmp/ledgerlyfthq_frontend.log 2>/tmp/ledgerlyfthq_frontend.error.log &
  )

  sleep 1
  if is_listening 3001; then
    echo "Frontend started on 3001"
  else
    echo "Frontend did not start (check /tmp/ledgerlyfthq_frontend.error.log)"
  fi
}

start_backend
start_frontend

echo
curl -sS http://127.0.0.1:8000/health || true
echo
curl -sS -o /dev/null -w "Frontend HTTP %{http_code}\n" http://127.0.0.1:3001/dashboard || true
