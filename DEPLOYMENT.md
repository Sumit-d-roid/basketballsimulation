# Basketball Tournament Simulator - Deployment Guide

## 🏀 Quick Start (Local Development)

Your app is **ready to use right now**! Both servers are running:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5000

### Starting the App

Use the convenient startup script:
```bash
./run.sh
```

Or start manually:
```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend  
cd frontend
npm start
```

## 🎮 How to Use Your App

1. **View Tournament Bracket**: Opens automatically at http://localhost:3000
2. **Play Your Pickup Game**: Go play a real quarter (12 minutes)
3. **Input Scores**: Enter the actual final score from your quarter (e.g., Team A: 28, Team B: 25)
4. **Watch the Magic**: System extrapolates to a full 48-minute game with realistic NBA variance
5. **Advance the Series**: Best-of-7 format, keep inputting quarter scores until a team wins 4 games
6. **Crown a Champion**: Complete all 5 rounds to see who wins the NBA title!

## 📊 Current Database Status

- ✅ **33 Teams**: 32 NBA teams + 1 Free Agent pool
- ✅ **400 Players**: Full NBA rosters + 80 free agents (legends, current FAs, international stars)
- ✅ **Active Tournament**: Season 2025 bracket initialized
- ✅ **Features**: Game extrapolation, play-by-play, stats tracking, free agent system

## 🚀 Production Deployment Options

### Option 1: Simple VPS Deployment (Recommended for Personal Use)

**Requirements:**
- Ubuntu 20.04+ VPS (DigitalOcean, Linode, AWS EC2)
- Domain name (optional but recommended)
- 1GB RAM minimum

**Steps:**

1. **Clone Your Repo on VPS**
```bash
git clone https://github.com/Sumit-d-roid/basketballsimulation.git
cd basketballsimulation
```

2. **Setup Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Initialize database
python seed_data.py
python add_free_agents.py
```

3. **Build Frontend**
```bash
cd ../frontend
npm install
npm run build
```

4. **Install Nginx**
```bash
sudo apt update
sudo apt install nginx
```

5. **Create Nginx Config** (`/etc/nginx/sites-available/basketball`)
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your VPS IP

    # Frontend (React build)
    location / {
        root /path/to/basketballsimulation/frontend/build;
        try_files $uri /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

6. **Enable Site**
```bash
sudo ln -s /etc/nginx/sites-available/basketball /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

7. **Create Systemd Service for Backend** (`/etc/systemd/system/basketball-backend.service`)
```ini
[Unit]
Description=Basketball Simulation Backend
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/basketballsimulation/backend
Environment="PATH=/path/to/basketballsimulation/backend/venv/bin"
ExecStart=/path/to/basketballsimulation/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

8. **Start Backend Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable basketball-backend
sudo systemctl start basketball-backend
```

**Your app is now live!** Visit your domain/IP address.

### Option 2: Docker Deployment

**Create `Dockerfile.backend`:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY backend/ .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

**Create `Dockerfile.frontend`:**
```dockerfile
FROM node:18 AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**Create `docker-compose.yml`:**
```yaml
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

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

**Deploy:**
```bash
docker-compose up -d
```

### Option 3: Cloud Platform Deployment

#### Railway.app (Easiest - 5 minutes)
1. Push to GitHub
2. Connect Railway to your repo
3. Add two services: backend (Python) and frontend (Node.js)
4. Set environment variables
5. Deploy! Railway gives you URLs automatically

#### Heroku
1. Create two apps: `basketball-sim-api` and `basketball-sim-web`
2. Backend: 
   ```bash
   heroku git:remote -a basketball-sim-api
   git subtree push --prefix backend heroku main
   ```
3. Frontend:
   ```bash
   heroku git:remote -a basketball-sim-web
   heroku buildpacks:set mars/create-react-app
   git subtree push --prefix frontend heroku main
   ```

#### Vercel (Frontend) + Render (Backend)
- **Vercel**: Connect GitHub repo, auto-deploys frontend
- **Render**: Create Web Service for backend, auto-deploys from GitHub

## 🔧 Environment Variables for Production

Create `.env` file in backend directory:
```env
FLASK_ENV=production
DATABASE_URL=sqlite:///basketball_sim.db
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://your-frontend-domain.com
```

Update `app.py` CORS config:
```python
CORS(app, origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','))
```

## 🔒 Security Checklist

- [ ] Set `DEBUG = False` in production
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS (Let's Encrypt with certbot)
- [ ] Set up database backups (use `/api/backup/download-db` endpoint)
- [ ] Configure firewall (UFW on Ubuntu)
- [ ] Use strong SECRET_KEY for Flask sessions

## 📦 Database Backup

Your app has built-in backup endpoints:

```bash
# Export JSON backup
curl http://localhost:5000/api/backup/export -o backup.json

# Download database file
curl http://localhost:5000/api/backup/download-db -o basketball_sim.db
```

**Set up automated backups:**
```bash
# Add to crontab (daily backup at 2 AM)
0 2 * * * curl http://localhost:5000/api/backup/download-db -o ~/backups/basketball_sim_$(date +\%Y\%m\%d).db
```

## 🎯 Recommended Setup for Your Use Case

Since this is for **personal pickup basketball fun**, I recommend:

**Best Option**: Run on your home computer/server
- Always available when you need it
- No hosting costs
- Full control over data
- Fast performance

**Steps:**
1. Keep running locally during games
2. Access from your phone's browser at `http://your-computer-ip:3000`
3. Make sure both devices are on same WiFi
4. Bookmark on your phone for quick access

**OR** if you want it always available:

**Railway.app** (Free tier is perfect for this):
- Push to GitHub
- Connect Railway
- Deploy in 5 minutes
- Get permanent URL
- Free for personal projects

## 📱 Mobile Access

Your app works on mobile browsers! Just visit the URL from your phone.

For best mobile experience:
1. Add to home screen (iOS/Android)
2. Opens like a native app
3. No app store needed!

## 🐛 Troubleshooting

**Backend won't start:**
```bash
cd backend
rm -rf __pycache__
python app.py
```

**Frontend build fails:**
```bash
cd frontend
rm -rf node_modules build
npm install
npm run build
```

**Port already in use:**
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

**Database issues:**
```bash
cd backend
rm basketball_sim.db
python seed_data.py
python add_free_agents.py
```

## 🎮 Ready to Play!

Your app is **production-ready** with:
- ✅ Modular, maintainable codebase
- ✅ Full NBA rosters + 80 free agents
- ✅ Game extrapolation algorithm
- ✅ Tournament bracket system
- ✅ Stats tracking
- ✅ Backup functionality

**Start using it now** at http://localhost:3000 or deploy using any option above!

---

**Need help?** The app is designed to be simple:
1. Open frontend
2. See tournament bracket
3. Click on a game
4. Input your real quarter scores
5. Watch the extrapolated full game
6. Repeat until champion crowned!

Enjoy your basketball tournaments! 🏆
