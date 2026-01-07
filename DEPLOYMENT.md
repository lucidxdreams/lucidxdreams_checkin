# Deployment Guide: Railway + Supabase

## Quick Start (10 minutes)

### Step 1: Deploy Backend to Railway

1. **Create Railway Account**: Go to [railway.app](https://railway.app) and sign up
2. **New Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select Repository**: Connect your GitHub and select this repo
4. **Configure Root Directory**: 
   - Go to Settings → Root Directory
   - Set to: `backend`
5. **Set Environment Variables** (Settings → Variables):
   ```
   PORT=5001
   RAILWAY_ENVIRONMENT=production
   ```
6. **Deploy**: Railway auto-deploys. Wait for green checkmark.
7. **Copy URL**: Settings → Domains → Copy your Railway URL (e.g., `https://xxx.up.railway.app`)

### Step 2: Configure Frontend

1. **Edit** `docs/env-config.js`:
   ```javascript
   window.ENV_API_BASE_URL = 'https://your-railway-url.up.railway.app';
   ```
2. **Commit and push** to GitHub

### Step 3: Deploy Frontend to GitHub Pages

1. Go to repo Settings → Pages
2. Source: Deploy from branch → `main` → `/docs`
3. Save. Site available at `https://username.github.io/repo-name/`

---

## Optional: Supabase Admin Dashboard

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) → New Project
2. Name: `lucidxdreams` (or any name)
3. Region: Choose closest to you
4. Wait for project to initialize

### Step 2: Create Database Schema

1. Go to SQL Editor in Supabase Dashboard
2. Paste contents of `documentation/supabase_schema.sql`
3. Click "Run"

### Step 3: Create Admin User

1. Go to Authentication → Users → Add User
2. Email: `admin@lucidxdreams.com`
3. Password: (choose a strong password)
4. Click "Create User"

### Step 4: Get API Keys

1. Go to Settings → API
2. Copy:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGci...`

### Step 5: Configure Frontend

Update `docs/env-config.js`:
```javascript
window.ENV_API_BASE_URL = 'https://your-railway-url.up.railway.app';
window.ENV_SUPABASE_URL = 'https://xxxxx.supabase.co';
window.ENV_SUPABASE_ANON_KEY = 'eyJhbGci...your-key';
```

### Step 6: Access Admin Dashboard

- URL: `https://your-site.github.io/repo-name/admin.html`
- Login with the admin user you created

---

## Troubleshooting

### Railway Healthcheck Fails
- **Check logs**: Railway Dashboard → Deployments → View Logs
- **Verify**: `/health` endpoint returns `{"status": "healthy"}`
- **Common fix**: Ensure `PORT` env variable is set

### Scanner Not Working
- **Check**: Browser console for API errors
- **Verify**: `ENV_API_BASE_URL` is set correctly in `env-config.js`
- **CORS**: Backend allows your frontend domain

### Admin Login Fails
- **Check**: Supabase credentials in `env-config.js`
- **Verify**: User exists in Supabase Authentication
- **Console**: Check browser console for errors

### Camera Not Working
- **HTTPS Required**: Camera only works on HTTPS or localhost
- **Permissions**: User must grant camera permission
- **Fallback**: Manual upload option appears after 15 seconds

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  GitHub Pages   │────▶│  Railway Backend │
│  (Frontend)     │     │  (Python/Flask)  │
│  docs/          │     │  backend/        │
└─────────────────┘     └──────────────────┘
        │                        │
        │                        │
        ▼                        ▼
┌─────────────────┐     ┌──────────────────┐
│    Supabase     │     │    QuickBase     │
│  (Admin Data)   │     │ (Form Submission)│
└─────────────────┘     └──────────────────┘
```

## Environment Variables Reference

### Railway Backend
| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | Yes | Server port (Railway sets automatically) |
| `RAILWAY_ENVIRONMENT` | No | Enables headless browser mode |
| `FRONTEND_URL` | No | For CORS (defaults to GitHub Pages) |

### Frontend (env-config.js)
| Variable | Required | Description |
|----------|----------|-------------|
| `ENV_API_BASE_URL` | Yes | Railway backend URL |
| `ENV_SUPABASE_URL` | No | Supabase project URL |
| `ENV_SUPABASE_ANON_KEY` | No | Supabase anon key |
