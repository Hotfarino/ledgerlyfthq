#!/usr/bin/env bash
set -euo pipefail

echo "Frontend (3001):"
lsof -nP -iTCP:3001 -sTCP:LISTEN || echo "not running"

echo
echo "Backend (8000):"
lsof -nP -iTCP:8000 -sTCP:LISTEN || echo "not running"

echo
echo "Health:"
curl -sS http://127.0.0.1:8000/health || true
echo
curl -sS -o /dev/null -w "Frontend HTTP %{http_code}\n" http://127.0.0.1:3001/dashboard || true
