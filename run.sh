#!/usr/bin/env bash
set -euo pipefail

echo "🏀 Starting Basketball Simulation (one-command)"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# 1) Python venv and dependencies
echo "→ Preparing backend environment"
cd "$BACKEND_DIR"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

# 2) Initialize DB data (idempotent)
echo "→ Seeding database"
python seed_data.py >/dev/null 2>&1 || true

# 3) Frontend install + build
echo "→ Building frontend"
cd "$FRONTEND_DIR"
if [ ! -d node_modules ]; then
  npm install --legacy-peer-deps
fi
npm run build --silent

# 4) Start backend server (serves built UI at /)
echo "→ Launching backend on http://localhost:5000"
cd "$BACKEND_DIR"
echo "→ Ensuring port 5000 is free"
(lsof -ti:5000 | xargs -r kill -9) 2>/dev/null || true
export FLASK_DEBUG=0
export HOST=0.0.0.0
export PORT=5000
exec python app.py
