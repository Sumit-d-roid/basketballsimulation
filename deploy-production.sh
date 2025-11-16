#!/bin/bash

# Basketball Simulation - Production Deployment Script
# Usage: ./deploy-production.sh [mode]
# Modes: vps, docker, local

set -e

MODE=${1:-local}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🏀 Basketball Simulation Deployment"
echo "===================================="
echo "Mode: $MODE"
echo ""

case $MODE in
  local)
    echo "📦 Setting up LOCAL development environment..."
    
    # Backend setup
    echo "🔧 Setting up backend..."
    cd "$SCRIPT_DIR/backend"
    
    if [ ! -d "venv" ]; then
      echo "Creating Python virtual environment..."
      python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -q -r requirements.txt
    
    # Check if database exists
    if [ ! -f "basketball_sim.db" ]; then
      echo "🗄️  Initializing database..."
      python seed_data.py
      python add_free_agents.py
    else
      echo "✓ Database already exists"
    fi
    
    # Frontend setup
    echo "🔧 Setting up frontend..."
    cd "$SCRIPT_DIR/frontend"
    
    if [ ! -d "node_modules" ]; then
      echo "Installing npm dependencies..."
      npm install
    else
      echo "✓ Node modules already installed"
    fi
    
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "🚀 Starting servers..."
    echo ""
    echo "Backend: http://localhost:5000"
    echo "Frontend: http://localhost:3000"
    echo ""
    echo "Press Ctrl+C to stop both servers"
    echo ""
    
    # Start backend in background
    cd "$SCRIPT_DIR/backend"
    source venv/bin/activate
    python app.py &
    BACKEND_PID=$!
    
    # Wait for backend to start
    sleep 3
    
    # Start frontend
    cd "$SCRIPT_DIR/frontend"
    npm start
    
    # Cleanup on exit
    kill $BACKEND_PID 2>/dev/null || true
    ;;
    
  vps)
    echo "🌐 Setting up VPS production environment..."
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
      echo "⚠️  Don't run as root. Run as your normal user."
      exit 1
    fi
    
    # Install system dependencies
    echo "📦 Installing system dependencies..."
    sudo apt update
    sudo apt install -y python3-pip python3-venv nginx
    
    # Backend setup
    echo "🔧 Setting up backend..."
    cd "$SCRIPT_DIR/backend"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install gunicorn
    
    # Initialize database
    if [ ! -f "basketball_sim.db" ]; then
      echo "🗄️  Initializing database..."
      python seed_data.py
      python add_free_agents.py
    fi
    
    # Frontend build
    echo "🔧 Building frontend..."
    cd "$SCRIPT_DIR/frontend"
    npm install
    npm run build
    
    # Create systemd service
    echo "📝 Creating systemd service..."
    sudo tee /etc/systemd/system/basketball-backend.service > /dev/null <<EOF
[Unit]
Description=Basketball Simulation Backend
After=network.target

[Service]
User=$USER
WorkingDirectory=$SCRIPT_DIR/backend
Environment="PATH=$SCRIPT_DIR/backend/venv/bin"
ExecStart=$SCRIPT_DIR/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    
    # Create nginx config
    echo "📝 Creating nginx config..."
    sudo tee /etc/nginx/sites-available/basketball > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        root $SCRIPT_DIR/frontend/build;
        try_files \$uri /index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/basketball /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    
    # Start services
    echo "🚀 Starting services..."
    sudo systemctl daemon-reload
    sudo systemctl enable basketball-backend
    sudo systemctl start basketball-backend
    sudo systemctl restart nginx
    
    # Get server IP
    SERVER_IP=$(curl -s ifconfig.me || echo "your-server-ip")
    
    echo ""
    echo "✅ VPS deployment complete!"
    echo ""
    echo "🌐 Your app is live at: http://$SERVER_IP"
    echo ""
    echo "📊 Check status:"
    echo "  Backend: sudo systemctl status basketball-backend"
    echo "  Nginx: sudo systemctl status nginx"
    echo ""
    echo "📝 Logs:"
    echo "  Backend: sudo journalctl -u basketball-backend -f"
    echo "  Nginx: sudo tail -f /var/log/nginx/access.log"
    echo ""
    ;;
    
  docker)
    echo "🐳 Setting up Docker deployment..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
      echo "❌ Docker not found. Install Docker first:"
      echo "   https://docs.docker.com/get-docker/"
      exit 1
    fi
    
    # Create Dockerfiles if they don't exist
    if [ ! -f "$SCRIPT_DIR/Dockerfile.backend" ]; then
      echo "📝 Creating Dockerfile.backend..."
      cat > "$SCRIPT_DIR/Dockerfile.backend" <<'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY backend/ .
RUN if [ ! -f basketball_sim.db ]; then python seed_data.py && python add_free_agents.py; fi
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
EOF
    fi
    
    if [ ! -f "$SCRIPT_DIR/Dockerfile.frontend" ]; then
      echo "📝 Creating Dockerfile.frontend..."
      cat > "$SCRIPT_DIR/Dockerfile.frontend" <<'EOF'
FROM node:18 AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY docker-nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
EOF
    fi
    
    # Create nginx config for Docker
    cat > "$SCRIPT_DIR/docker-nginx.conf" <<'EOF'
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
    
    # Create docker-compose.yml
    if [ ! -f "$SCRIPT_DIR/docker-compose.yml" ]; then
      echo "📝 Creating docker-compose.yml..."
      cat > "$SCRIPT_DIR/docker-compose.yml" <<'EOF'
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "5000:5000"
    volumes:
      - ./backend/basketball_sim.db:/app/basketball_sim.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/runs"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
EOF
    fi
    
    # Build and start
    echo "🔨 Building Docker images..."
    docker-compose build
    
    echo "🚀 Starting containers..."
    docker-compose up -d
    
    echo ""
    echo "✅ Docker deployment complete!"
    echo ""
    echo "🌐 Your app is running at: http://localhost"
    echo ""
    echo "📊 Useful commands:"
    echo "  View logs: docker-compose logs -f"
    echo "  Stop: docker-compose down"
    echo "  Restart: docker-compose restart"
    echo "  Status: docker-compose ps"
    echo ""
    ;;
    
  *)
    echo "❌ Unknown mode: $MODE"
    echo ""
    echo "Usage: $0 [mode]"
    echo "Modes:"
    echo "  local  - Local development (default)"
    echo "  vps    - VPS/Server production deployment"
    echo "  docker - Docker containerized deployment"
    exit 1
    ;;
esac
