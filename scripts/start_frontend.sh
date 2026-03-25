#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../frontend"
if [ ! -d node_modules ]; then
  npm install
fi
if [ ! -f .env.local ]; then
  cp .env.example .env.local
fi
npm run dev -- --hostname 127.0.0.1 --port 3001
