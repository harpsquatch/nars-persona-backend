# Railway Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- Git repository pushed to GitHub

## Step 1: Create Railway Project

1. Go to Railway.app and create a new project
2. Select "Deploy from GitHub repo"
3. Connect your `nars-persona-backend` repository

## Step 2: Add MySQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"Add MySQL"**
3. Railway will automatically create a MySQL database and provide environment variables

## Step 3: Configure Environment Variables

Go to your backend service → **Variables** tab and add:

### Required Variables (if Railway MySQL plugin doesn't auto-populate):
```
DATABASE_URL=mysql://user:password@host:port/database
```
**Note:** Railway's MySQL plugin should automatically provide `DATABASE_URL`. If not, construct it from the MySQL service variables.

### Application Variables:
```
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
SECRET_KEY=your-secret-key-change-this
APP_ENV=production
FLASK_ENV=production
PORT=8080
```

### Optional Variables:
```
INIT_DATABASE=true          # Set to 'true' only for first deployment to initialize schema
RESET_DATABASE=false        # DANGER: Set to 'true' only if you want to wipe and reset database
LOG_LEVEL=INFO
JWT_ACCESS_TOKEN_EXPIRES=3600
```

## Step 4: Initial Database Setup

For the **first deployment only**, set:
```
INIT_DATABASE=true
```

This will run `init_db.py` to create all tables and seed initial data.

After the first successful deployment, **remove or set to false**:
```
INIT_DATABASE=false
```

## Step 5: Deploy

1. Railway will automatically deploy when you push to your GitHub repository
2. Monitor the deployment logs in Railway dashboard
3. Once deployed, Railway will provide a public URL (e.g., `https://your-app.up.railway.app`)

## Step 6: Update Frontend Environment Variable

In **Vercel** (your frontend deployment):
1. Go to your project settings
2. Navigate to **Environment Variables**
3. Add:
   ```
   VITE_API_URL=https://your-railway-url.up.railway.app
   ```
4. Redeploy your frontend

## Troubleshooting

### Database Connection Failed
- Verify `DATABASE_URL` is set correctly
- Check that MySQL service is running in Railway
- Ensure the database name, user, and password are correct

### Port Issues
- Railway automatically sets the `PORT` environment variable
- The app listens on `$PORT` (default: 8080)

### Database Not Initialized
- Set `INIT_DATABASE=true` for the first deployment
- Check deployment logs for any schema creation errors

### Migration Errors
- This app uses manual migration scripts, not Flask-Migrate
- Run migration scripts manually if needed:
  ```bash
  railway run python add_wishlist_seasonal.py
  railway run python add_product_url.py
  railway run python add_instruction_progress.py
  ```

## Security Notes

1. **Never commit** `.env` files or credentials to Git
2. Always use strong, unique values for `JWT_SECRET_KEY` and `SECRET_KEY`
3. Rotate secrets regularly
4. Use Railway's built-in environment variables when possible

## Monitoring

- Check Railway logs for errors: `railway logs`
- Monitor database usage in Railway dashboard
- Set up alerts for crashes or high resource usage

## Database Backup

Railway provides automatic backups for MySQL. Additionally:
```bash
# Manual backup (run locally with Railway CLI)
railway run python -c "from app import app, db; from models import *; import json; # backup logic"
```

## Useful Railway CLI Commands

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs
railway logs

# Run commands in Railway environment
railway run python your_script.py

# Open database shell
railway run mysql
```

