# 🚂 Railway Deployment Guide

## Quick Deploy to Railway (5 Minutes!)

### Prerequisites
- GitHub account
- Railway account (sign up at https://railway.app - free tier available)
- Your code pushed to GitHub

### Step 1: Push to GitHub

```bash
cd /workspaces/basketballsimulation

# Initialize git if not already done
git init
git add .
git commit -m "Basketball simulation app ready for deployment"

# Push to GitHub
git remote add origin https://github.com/YOUR-USERNAME/basketballsimulation.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Railway

1. **Go to Railway**: https://railway.app
2. **Sign in** with GitHub
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose** your `basketballsimulation` repository
6. **Railway will automatically detect** the configuration files and deploy!

### Step 3: Configuration

Railway will automatically:
- ✅ Detect Python backend (via `requirements.txt`)
- ✅ Install dependencies (Flask, SQLAlchemy, gunicorn)
- ✅ Initialize database (seed_data.py, add_free_agents.py)
- ✅ Build frontend (npm install, npm run build)
- ✅ Start backend with gunicorn
- ✅ Serve frontend from Flask

### Step 4: Get Your URL

After deployment completes:
1. Click on your project in Railway
2. Go to **"Settings"** tab
3. Click **"Generate Domain"** to get a public URL
4. Your app will be live at: `https://your-app.up.railway.app`

**That's it! 🎉**

## Configuration Files Explained

Railway uses these files to deploy your app:

### `railway.toml` (Main config)
```toml
[build]
builder = "nixpacks"
buildCommand = "..."

[deploy]
startCommand = "cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT app:app"
```

### `start.sh` (Startup script)
- Checks if database exists
- Initializes data if needed
- Builds frontend
- Starts gunicorn server

### `Procfile` (Process definition)
```
web: cd backend && gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

## Environment Variables (Optional)

If needed, add these in Railway dashboard:

- `FLASK_ENV=production`
- `PYTHONUNBUFFERED=1`
- `PORT` (automatically set by Railway)

## Database Persistence

Your SQLite database will persist on Railway's volume storage. To backup:

1. Visit: `https://your-app.up.railway.app/api/backup/download-db`
2. Save the database file locally

## Monitoring & Logs

In Railway dashboard:
- **Deployments** tab: View build logs
- **Logs** tab: See runtime logs
- **Metrics** tab: Monitor CPU/Memory usage

## Troubleshooting

### Build Fails
Check Railway build logs for errors. Common issues:
- Missing dependencies in `requirements.txt`
- Frontend build errors

**Fix:** Check logs, update dependencies, commit, and Railway auto-redeploys

### App Crashes
Check runtime logs. Common issues:
- Database initialization errors
- Port binding issues

**Fix:** Ensure `start.sh` runs correctly and PORT variable is used

### Frontend Not Loading
Ensure frontend is built during deployment:
```bash
cd frontend && npm run build
```

Check that `backend/app.py` serves static files correctly.

## Free Tier Limits

Railway free tier includes:
- ✅ 500 hours/month execution time
- ✅ 1GB memory
- ✅ 1GB storage
- ✅ Custom domain support

Perfect for personal use! 🎯

## Updating Your App

Railway auto-deploys on GitHub push:

```bash
# Make changes locally
git add .
git commit -m "Your changes"
git push

# Railway automatically redeploys!
```

## Custom Domain (Optional)

1. In Railway project settings
2. Click "Add Custom Domain"
3. Enter your domain (e.g., `basketball.yourdomain.com`)
4. Add CNAME record in your DNS:
   ```
   CNAME basketball -> your-app.up.railway.app
   ```

## Testing Locally First

Before deploying, test the production setup locally:

```bash
# Install gunicorn
pip install gunicorn

# Test startup script
./start.sh

# Or run gunicorn directly
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Visit http://localhost:5000 to verify.

## Alternative: Separate Services

For more control, deploy backend and frontend as separate Railway services:

### Backend Service
- Source: `backend/` directory
- Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
- Generate domain: `https://backend.up.railway.app`

### Frontend Service
- Source: `frontend/` directory
- Build: `npm run build`
- Start: `npx serve -s build -p $PORT`
- Set env: `REACT_APP_API_URL=https://backend.up.railway.app`

## Cost Optimization

Railway charges after free tier based on usage:

**Tips to minimize costs:**
- Use free tier for personal projects
- Set up auto-sleep (app sleeps when inactive)
- Monitor usage in Railway dashboard
- Consider cold starts acceptable for hobby projects

## Production Checklist

Before going live:

- [ ] Test all features locally
- [ ] Ensure database is seeded (33 teams, 400 players)
- [ ] Frontend builds without errors
- [ ] Backend serves frontend correctly
- [ ] API endpoints respond correctly
- [ ] Set FLASK_ENV=production
- [ ] Test on mobile devices
- [ ] Set up database backups
- [ ] Monitor logs after deployment

## Support

**Railway Docs:** https://docs.railway.app  
**Community:** https://discord.gg/railway

---

## 🎮 Your App Will Be Live!

After deployment:
- ✅ Access from anywhere: `https://your-app.up.railway.app`
- ✅ Share with friends
- ✅ Input scores from your phone
- ✅ Run tournaments anytime!

**Deploy now and start playing!** 🏀🏆
