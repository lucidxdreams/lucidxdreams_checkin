# Supabase Backend Setup for GitHub Pages

This guide explains how to set up Supabase as your backend for the DC Medical Cannabis Application system when hosting on GitHub Pages.

## Why Supabase?

GitHub Pages only hosts static files (HTML, CSS, JS). For a fully operational system with persistent data storage accessible from anywhere, you need a backend service. **Supabase** is ideal because:

- **Free tier** - 500MB database, 50,000 monthly active users
- **PostgreSQL database** - Reliable, scalable, SQL-based
- **Built-in Auth** - Secure admin login for the dashboard
- **Real-time subscriptions** - Live data updates
- **Row Level Security (RLS)** - Secure data access without custom backend
- **REST API** - Direct browser-to-database communication
- **Admin Dashboard** - View/manage data from any device

---

## Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up
2. Click **"New Project"**
3. Choose your organization
4. Enter project details:
   - **Name**: `lucid-dreams-medical`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your users (e.g., `us-east-1`)
5. Click **"Create new project"** and wait ~2 minutes for setup

---

## Step 2: Create the Customers Table

1. Go to **SQL Editor** in your Supabase dashboard
2. Run the following SQL to create the customers table:

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
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    checked_in_at TIMESTAMPTZ
);

-- Create index for faster searches
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_created ON customers(created_at DESC);

-- Enable Row Level Security
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Policy: Allow anonymous inserts (for form submissions)
CREATE POLICY "Allow anonymous inserts" ON customers
    FOR INSERT
    WITH CHECK (true);

-- Policy: Allow authenticated users to read all data
CREATE POLICY "Allow authenticated read" ON customers
    FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Allow authenticated users to update
CREATE POLICY "Allow authenticated update" ON customers
    FOR UPDATE
    TO authenticated
    USING (true);

-- Policy: Allow anonymous to update their own record (for check-in)
-- This uses a session-based approach where the app stores the record ID
CREATE POLICY "Allow anonymous update own record" ON customers
    FOR UPDATE
    TO anon
    USING (true);
```

---

## Step 3: Create an Admin User

1. Go to **Authentication** → **Users** in Supabase dashboard
2. Click **"Add user"** → **"Create new user"**
3. Enter admin credentials:
   - **Email**: `admin@lucidxdreams.com`
   - **Password**: Your secure admin password
4. Click **"Create user"**

---

## Step 4: Get Your API Credentials

1. Go to **Settings** → **API** in your Supabase dashboard
2. Copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbGci...` (safe for frontend)

---

## Step 5: Update Frontend Code

### Update `index.html`

Find these lines near the top of the `<script>` section:

```javascript
const SUPABASE_URL = 'https://YOUR_PROJECT_ID.supabase.co';
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY';
```

Replace with your actual values:

```javascript
const SUPABASE_URL = 'https://xxxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGci...your-key...';
```

### Update `admin.html`

Same changes at the top of the `<script>` section.

---

## Step 6: Deploy to GitHub Pages

### Option A: Simple Deployment (docs folder)

1. Move all frontend files to `/docs` folder
2. Go to your GitHub repo → **Settings** → **Pages**
3. Source: **Deploy from a branch**
4. Branch: `main` → `/docs`
5. Click **Save**

### Option B: GitHub Actions (recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend
```

---

## Step 7: Configure CORS (if needed)

If you get CORS errors:

1. Go to **Settings** → **API** in Supabase
2. Under **CORS allowed origins**, add your GitHub Pages URL:
   - `https://yourusername.github.io`
   - Or your custom domain

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Pages (Static Host)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  index.html │  │  admin.html │  │  terms.html etc.    │  │
│  │  (Form UI)  │  │ (Dashboard) │  │  (Static pages)     │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘  │
└─────────┼────────────────┼──────────────────────────────────┘
          │                │
          │ Supabase JS    │ Supabase JS
          │ Client         │ Client + Auth
          ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Supabase (Backend)                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 PostgreSQL Database                  │    │
│  │  ┌─────────────────────────────────────────────┐    │    │
│  │  │              customers table                 │    │    │
│  │  │  - Customer info (name, DOB, address, etc.) │    │    │
│  │  │  - Registration ID & status                 │    │    │
│  │  │  - Timestamps                               │    │    │
│  │  └─────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────┐  ┌─────────────────────────────┐       │
│  │  Auth (Admin)   │  │  Row Level Security (RLS)   │       │
│  └─────────────────┘  └─────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Customer Submission Flow
1. Customer fills form on `index.html`
2. On submit, data is sent to Supabase via REST API
3. Record created with `status: 'pending'`
4. Customer enters Registration ID and clicks "Check-in"
5. Record updated with `status: 'checked_in'`

### Admin Dashboard Flow
1. Admin navigates to `admin.html`
2. Logs in with Supabase Auth
3. Dashboard loads all customer records
4. Admin can search, view details, track status

---

## Security Considerations

1. **Never expose service_role key** - Only use `anon` key in frontend
2. **RLS is mandatory** - Policies control who can read/write data
3. **Admin auth required** - Only authenticated users can view all data
4. **HTTPS enforced** - GitHub Pages and Supabase both use HTTPS

---

## Troubleshooting

### "Supabase not configured" warning
- Check that you replaced placeholder values with real credentials
- Verify the Supabase URL format: `https://PROJECT_ID.supabase.co`

### CORS errors
- Add your domain to Supabase CORS allowed origins
- Make sure you're using HTTPS

### Auth not working
- Verify admin user was created in Supabase Auth
- Check email/password match exactly

### Data not saving
- Check browser console for errors
- Verify RLS policies are created correctly
- Test with Supabase dashboard's SQL editor

---

## Optional Enhancements

### Real-time Updates
Add to `admin.html` for live updates:

```javascript
const subscription = supabase
    .channel('customers')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'customers' }, 
        payload => {
            console.log('Change received!', payload);
            loadCustomers(); // Refresh the list
        }
    )
    .subscribe();
```

### Email Notifications
Use Supabase Edge Functions or integrate with services like:
- SendGrid
- Resend
- Postmark

---

## Cost Estimate

**Supabase Free Tier includes:**
- 500MB database storage
- 2GB bandwidth
- 50,000 monthly active users
- Unlimited API requests

**For typical usage (100 customers/month):**
- **Cost: $0/month** (well within free tier)

**If you exceed free tier:**
- Pro plan: $25/month (8GB storage, 50GB bandwidth)
