#!/bin/bash
set -e

# Railway deployment start script

echo "🏀 Basketball Simulation - Railway Deployment"
echo "=============================================="

cd backend

# Check if database exists
if [ ! -f "basketball_sim.db" ]; then
    echo "📦 Initializing database..."
    python seed_data.py
    python add_free_agents.py
else
    echo "✓ Database already exists"
fi

# Build frontend if not already built
if [ ! -d "../frontend/build" ]; then
    echo "🔧 Building frontend..."
    cd ../frontend
    npm install
    npm run build
    cd ../backend
else
    echo "✓ Frontend already built"
fi

echo "🚀 Starting backend server..."
exec gunicorn -w 4 -b 0.0.0.0:$PORT app:app
