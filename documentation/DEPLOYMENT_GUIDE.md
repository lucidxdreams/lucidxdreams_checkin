# Deployment Guide - Full Stack Setup

Complete guide for deploying Lucid x Dreams Check-in System to production.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Pages                            │
│  Frontend (Static): index.html, admin.html, CSS, JS, logo       │
│  URL: https://yourusername.github.io/repo-name                  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ API Calls (CORS enabled)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (Flask API)                          │
│  Host: Railway / Render / Fly.io                                │
│  Endpoints: /api/scan-barcode, /api/extract-id                  │
│  URL: https://your-backend.railway.app                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Database Queries
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Supabase Database                          │
│  PostgreSQL + Auth + Real-time                                  │
│  URL: https://yourproject.supabase.co                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Backend Hosting Options

### Option 1: Railway (Recommended) ⭐

**Why Railway:**
- ✅ Free tier: $5 credit/month (enough for low-medium traffic)
- ✅ Automatic deployments from GitHub
- ✅ Built-in domain with HTTPS
- ✅ Simple environment variables
- ✅ Supports Python + system dependencies

**Cost:** ~$3-5/month (500 hours uptime)

### Option 2: Render

**Why Render:**
- ✅ Free tier available (with limitations)
- ✅ Easy Python deployment
- ✅ Auto-sleep on free tier (wakes on request)

**Cost:** Free (spins down after 15 min inactivity) or $7/month

### Option 3: Fly.io

**Why Fly.io:**
- ✅ Free tier: 3 small VMs
- ✅ Edge deployment (fast globally)
- ✅ Dockerfile support

**Cost:** Free tier available

---

## Part 2: Deploy Backend to Railway

### Step 1: Prepare Backend for Deployment

#### Create `railway.json` in backend folder

```bash
cd backend
```

Create `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### Create `Procfile`

```bash
echo "web: gunicorn app:app" > Procfile
```

#### Create `runtime.txt` (specify Python version)

```bash
echo "python-3.11.7" > runtime.txt
```

#### `app.py` Production Configuration

The backend is already configured for production mode:
- `debug=False` is set
- PORT is read from environment variable
- Gunicorn is included in requirements.txt

No changes needed - the app is production-ready.

#### Update CORS settings

In `app.py`, update CORS to allow your frontend domain:

```python
from flask_cors import CORS

# Update this after you deploy frontend
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://yourusername.github.io')

CORS(app, origins=[
    FRONTEND_URL,
    'http://localhost:8080',  # For local development
    'http://127.0.0.1:8080'
])
```

### Step 2: Deploy to Railway

#### Option A: Using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Deploy
railway up
```

#### Option B: Using Railway Dashboard (Easier)

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Select **"backend"** as the root directory
6. Railway will auto-detect Python and deploy

### Step 3: Configure Environment Variables

In Railway dashboard:

1. Go to your project → **Variables** tab
2. Add these variables:

```bash
FRONTEND_URL=https://yourusername.github.io
PORT=5001
FLASK_ENV=production
```

### Step 4: Get Your Backend URL

Railway will provide a URL like:
```
https://medical-card-submission-production.up.railway.app
```

Save this URL - you'll need it for the frontend.

---

## Part 3: Deploy Frontend to GitHub Pages

### Step 1: Push to GitHub

```bash
cd /path/to/medical_card_submission
git init
git add .
git commit -m "Initial commit: Lucid x Dreams check-in system"
git remote add origin https://github.com/yourusername/your-repo-name.git
git push -u origin main
```

### Step 2: Enable GitHub Pages

1. Go to your repo on GitHub
2. **Settings** → **Pages**
3. Source: **Deploy from a branch**
4. Branch: **main** → **/frontend**
5. Click **Save**

After 1-2 minutes, your site will be live at:
```
https://yourusername.github.io/your-repo-name
```

### Step 3: Update Frontend Configuration

Edit `frontend/index.html` and update:

```javascript
// Backend API URL
const API_BASE_URL = 'https://medical-card-submission-production.up.railway.app';

// Supabase (from Part 4)
const SUPABASE_URL = 'https://yourproject.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key-here';
```

Commit and push:

```bash
git add frontend/index.html
git commit -m "Update API URLs for production"
git push
```

GitHub Pages will auto-redeploy.

---

## Part 4: Setup Supabase Database

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create account
3. **New Project**
4. Name: `lucid-dreams-checkin`
5. Database password: (generate strong password, save it!)
6. Region: **US East** (closest to DC)

### Step 2: Create Database Tables

Go to **SQL Editor** and run:

```sql
-- Create customers table
CREATE TABLE customers (
    id BIGSERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE,
    street_address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    phone TEXT,
    email TEXT,
    consent_email BOOLEAN DEFAULT false,
    consent_auth BOOLEAN DEFAULT false,
    consent_legal BOOLEAN DEFAULT false,
    registration_id TEXT,
    expiration_date DATE,
    has_existing_card BOOLEAN DEFAULT false,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    checked_in_at TIMESTAMPTZ
);

-- Create indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_created ON customers(created_at DESC);
CREATE INDEX idx_customers_registration ON customers(registration_id);

-- Enable Row Level Security
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Policy: Allow anonymous inserts (for check-in form)
CREATE POLICY "Allow anonymous inserts" ON customers
    FOR INSERT
    WITH CHECK (true);

-- Policy: Allow anonymous updates (for check-in completion)
CREATE POLICY "Allow anonymous update own record" ON customers
    FOR UPDATE
    TO anon
    USING (true);

-- Policy: Allow authenticated users to read all (for admin dashboard)
CREATE POLICY "Allow authenticated read" ON customers
    FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Allow authenticated users to update
CREATE POLICY "Allow authenticated update" ON customers
    FOR UPDATE
    TO authenticated
    USING (true);
```

### Step 3: Create Admin User

1. **Authentication** → **Users** → **Add user**
2. Email: `admin@lucidxdreams.com`
3. Password: (your secure admin password)
4. Click **Create user**

### Step 4: Get API Credentials

1. **Settings** → **API**
2. Copy:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGci...`

Update these in `frontend/index.html` AND `frontend/admin.html`.

---

## Part 5: Connect Everything

### Update Frontend with All URLs

Edit `frontend/index.html`:

```javascript
// ============================================
// PRODUCTION CONFIGURATION
// ============================================

// Backend API (Railway)
const API_BASE_URL = 'https://your-backend.railway.app';

// Supabase Database
const SUPABASE_URL = 'https://xxxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGci...your-key...';
```

Same for `frontend/admin.html`.

### Update Backend CORS

In Railway dashboard, update environment variable:

```
FRONTEND_URL=https://yourusername.github.io
```

Or if using custom domain:

```
FRONTEND_URL=https://checkin.lucidxdreams.com
```

---

## Part 6: Testing Production Setup

### Test Checklist

- [ ] Frontend loads at GitHub Pages URL
- [ ] Logo displays correctly
- [ ] Check-in button works
- [ ] Can upload ID images
- [ ] Backend barcode scanning works (check Network tab)
- [ ] Customer data saves to Supabase
- [ ] Admin dashboard loads
- [ ] Can login to admin dashboard
- [ ] Customer list displays
- [ ] Search works in admin dashboard

### Debugging Production Issues

#### Frontend shows CORS error
```
Access to fetch at 'https://backend.railway.app/api/...' has been blocked by CORS
```

**Fix:** Update `FRONTEND_URL` in Railway environment variables.

#### Backend API not responding
```
Failed to fetch: net::ERR_CONNECTION_REFUSED
```

**Fix:** 
1. Check Railway logs
2. Verify backend is running (Railway dashboard)
3. Check `API_BASE_URL` in frontend code

#### Supabase "401 Unauthorized"
```
Error: Invalid API key
```

**Fix:**
1. Verify `SUPABASE_ANON_KEY` is correct
2. Check RLS policies are created
3. Ensure policies allow anonymous inserts

---

## Part 7: Custom Domain (Optional)

### For Frontend (GitHub Pages)

1. Buy domain (e.g., `checkin.lucidxdreams.com`)
2. Add DNS records:
   ```
   Type: CNAME
   Name: checkin (or @)
   Value: yourusername.github.io
   ```
3. In GitHub repo: **Settings** → **Pages** → **Custom domain**
4. Enter: `checkin.lucidxdreams.com`
5. Wait 10-30 minutes for DNS propagation

### For Backend (Railway)

1. In Railway project → **Settings** → **Domains**
2. Click **Generate Domain** (free Railway subdomain)
3. Or add custom domain: `api.lucidxdreams.com`
4. Add DNS record:
   ```
   Type: CNAME
   Name: api
   Value: your-project.railway.app
   ```

---

## Cost Summary

| Service | Purpose | Cost |
|---------|---------|------|
| **GitHub Pages** | Frontend hosting | **Free** |
| **Railway** | Backend API | **$3-5/month** |
| **Supabase** | Database | **Free** (500MB, 2GB bandwidth) |
| **Domain** (optional) | Custom URL | **$10-15/year** |

**Total: $3-5/month** (or free if using Render free tier)

---

## Alternative: Deploy Backend to Render (Free Tier)

If you want completely free hosting:

### Deploy to Render

1. Go to [render.com](https://render.com)
2. **New** → **Web Service**
3. Connect GitHub repo
4. Settings:
   - **Name:** `lucid-dreams-backend`
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt && playwright install chromium`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free

**Trade-off:** Free tier spins down after 15 minutes of inactivity (50-second cold start on first request).

---

## Maintenance & Monitoring

### Railway Monitoring

- Dashboard shows CPU, memory, bandwidth usage
- Logs available in real-time
- Set up alerts for downtime

### Supabase Monitoring

- **Database** → Check storage usage
- **Logs** → Monitor query performance
- Free tier limits: 500MB database, 2GB bandwidth/month

### GitHub Pages

- Automatically rebuilds on push to main branch
- Check **Actions** tab for deployment status

---

## Security Checklist

- [ ] Supabase RLS policies enabled
- [ ] Admin dashboard requires authentication
- [ ] HTTPS enabled on all services (automatic)
- [ ] Environment variables not committed to Git
- [ ] CORS restricted to your domain only
- [ ] Regular backups of Supabase database
- [ ] Keep dependencies updated

---

## Support & Troubleshooting

### Railway Issues
- Check logs: Railway Dashboard → Logs
- Restart service: Deployments → Latest → Restart

### Supabase Issues
- Check RLS policies: Database → Policies
- View logs: Logs → Postgres / Realtime

### Need Help?
- Railway Discord: https://discord.gg/railway
- Supabase Discord: https://discord.supabase.com

---

**Your production stack is now live! 🎉**

Frontend: `https://yourusername.github.io/repo-name`  
Backend: `https://your-backend.railway.app`  
Database: `https://yourproject.supabase.co`
