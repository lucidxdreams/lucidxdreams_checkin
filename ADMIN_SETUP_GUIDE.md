# Admin Dashboard Setup Guide

## Overview

The new professional admin dashboard provides complete access to customer data including:

✅ **Full customer information** (name, DOB, contact, address)  
✅ **Government ID images** (front and back)  
✅ **Registration tracking** (status, dates, IDs)  
✅ **Search and filtering** capabilities  
✅ **CSV export** functionality  
✅ **Secure authentication** via Supabase Auth  

---

## Step 1: Update Supabase Database Schema

Run the following SQL in your **Supabase SQL Editor**:

```sql
-- Add columns for ID images
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS id_front_url TEXT,
ADD COLUMN IF NOT EXISTS id_back_url TEXT,
ADD COLUMN IF NOT EXISTS id_front_filename TEXT,
ADD COLUMN IF NOT EXISTS id_back_filename TEXT;

-- Create storage bucket for ID images
INSERT INTO storage.buckets (id, name, public)
VALUES ('customer-ids', 'customer-ids', false)
ON CONFLICT (id) DO NOTHING;

-- Enable RLS on storage bucket
CREATE POLICY "Allow authenticated users to upload IDs"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'customer-ids');

CREATE POLICY "Allow authenticated users to read IDs"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'customer-ids');

CREATE POLICY "Allow anon to upload IDs during submission"
ON storage.objects FOR INSERT
TO anon
WITH CHECK (bucket_id = 'customer-ids');

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_customers_id_images 
ON customers(id) WHERE id_front_url IS NOT NULL;

-- Add comments
COMMENT ON COLUMN customers.id_front_url IS 'Supabase Storage URL for front of government ID';
COMMENT ON COLUMN customers.id_back_url IS 'Supabase Storage URL for back of government ID';
```

---

## Step 2: Configure Backend Environment Variables

Add these environment variables to your Railway deployment:

### Required Variables:

```bash
# Supabase Configuration (for storing customer data and ID images)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...  # Get from Supabase Settings > API > service_role key

# IMPORTANT: Use the service_role key for backend, NOT the anon key
# The service_role key has full access to storage and database
```

### How to set on Railway:

1. Go to your Railway project
2. Click on your backend service
3. Go to **Variables** tab
4. Add the above variables
5. Click **Deploy** to restart with new variables

---

## Step 3: Update Backend Dependencies

The backend has been updated to include Supabase support. Make sure `requirements.txt` includes:

```txt
supabase>=2.3.4
```

Railway will automatically install this on next deployment.

---

## Step 4: Deploy Backend Changes

1. Commit the backend changes:
   ```bash
   git add backend/
   git commit -m "Add Supabase integration for ID image storage"
   git push
   ```

2. Railway will automatically redeploy

3. Verify deployment:
   - Check Railway logs for "Supabase client initialized successfully"
   - Test the API: `https://your-backend.railway.app/health`

---

## Step 5: Create Admin User

1. Go to your **Supabase Dashboard**
2. Navigate to **Authentication** → **Users**
3. Click **Add user** → **Create new user**
4. Enter credentials:
   - Email: `admin@lucidxdreams.com` (or your preferred email)
   - Password: Choose a strong password
5. Click **Create user**

**Save these credentials securely** - you'll need them to access the admin dashboard.

---

## Step 6: Access the Admin Dashboard

### URL:
```
https://lucidxdreams.github.io/admin.html
```

Or if using custom domain:
```
https://yourdomain.com/admin.html
```

### Login:
1. Navigate to the admin dashboard URL
2. Enter the admin email and password you created in Step 5
3. Click **Sign In**

---

## Features of the New Admin Dashboard

### 📊 Dashboard Overview
- **Statistics Cards**: Total customers, pending, checked-in counts
- **Real-time Updates**: Refresh button to reload data
- **Status at a Glance**: Color-coded status badges

### 🔍 Search & Filter
- **Search Bar**: Search by name, email, phone, or registration ID
- **Status Filter**: Filter by pending/checked-in status
- **Instant Results**: Real-time filtering as you type

### 📋 Customer Table
- **Complete Information**: All customer details in one view
- **Sortable Columns**: Click headers to sort
- **Action Buttons**: Quick access to detailed view

### 👤 Customer Details Modal
- **Full Profile**: All customer information organized by sections
- **ID Images**: View front and back of government IDs
- **Click to Enlarge**: Click images to open in new tab
- **Status Tracking**: Created date, check-in date, etc.

### 📥 Export Functionality
- **CSV Export**: Download customer data as CSV
- **Filtered Export**: Only exports currently filtered results
- **Date-stamped**: Filenames include current date

---

## How ID Images Are Stored

### Storage Flow:

1. **Customer submits application** with ID image
2. **Backend receives** base64 encoded image
3. **Supabase Storage** stores image in `customer-ids` bucket
4. **Database updated** with image URL (`id_front_url`)
5. **Admin dashboard** displays images via secure URLs

### Storage Structure:

```
customer-ids/
├── customer_1/
│   ├── front_20260110_140522.jpg
│   └── back_20260110_140523.jpg
├── customer_2/
│   ├── front_20260110_141234.jpg
│   └── back_20260110_141235.jpg
└── ...
```

### Security:

- **Private Bucket**: Images not publicly accessible
- **RLS Policies**: Only authenticated admin users can view
- **Secure URLs**: Time-limited signed URLs (if needed)

---

## Testing the System

### Test ID Image Storage:

1. **Submit a test application** via the main form
2. **Check Backend Logs** on Railway:
   ```
   Customer data stored in Supabase: ID 123
   Uploaded front ID image: customer_123/front_...jpg
   ```
3. **Check Supabase Storage**:
   - Go to Storage → `customer-ids` bucket
   - Verify images were uploaded
4. **Check Admin Dashboard**:
   - Login to admin panel
   - View customer details
   - Verify ID images display correctly

### Test Admin Features:

- ✅ **Login**: Can authenticate with admin credentials
- ✅ **View List**: All customers appear in table
- ✅ **Search**: Search by name/email/phone works
- ✅ **Filter**: Status filter works correctly
- ✅ **View Details**: Modal opens with full customer info
- ✅ **View Images**: ID images display and can be opened
- ✅ **Export**: CSV download works
- ✅ **Refresh**: Data reloads correctly

---

## Troubleshooting

### Images Not Appearing:

**Check 1**: Verify storage bucket exists
```sql
SELECT * FROM storage.buckets WHERE name = 'customer-ids';
```

**Check 2**: Verify RLS policies
```sql
SELECT * FROM storage.policies WHERE bucket_id = 'customer-ids';
```

**Check 3**: Check backend logs for upload errors
```
Railway → Your Service → Deployments → View Logs
```

**Check 4**: Verify `SUPABASE_SERVICE_KEY` is set (not anon key)
```
Railway → Your Service → Variables
```

### Login Not Working:

**Check 1**: Verify admin user exists in Supabase Auth
```
Supabase → Authentication → Users
```

**Check 2**: Check browser console for errors
```
Right-click → Inspect → Console tab
```

**Check 3**: Verify Supabase credentials in `env-config.js`
```javascript
window.ENV_SUPABASE_URL = 'https://...';
window.ENV_SUPABASE_ANON_KEY = 'eyJ...'; // anon key for frontend
```

### Database Connection Issues:

**Check 1**: Verify Supabase project is active
```
Supabase → Project Settings → General
```

**Check 2**: Check RLS policies on `customers` table
```sql
SELECT * FROM pg_policies WHERE tablename = 'customers';
```

**Check 3**: Test API endpoint directly
```bash
curl https://your-backend.railway.app/api/admin/customers
```

---

## Security Best Practices

### ✅ DO:
- Use **service_role key** on backend (never exposed to client)
- Use **anon key** on frontend (safe for public)
- Require **authentication** for all admin endpoints
- Enable **RLS policies** on all tables
- Use **strong passwords** for admin accounts
- Set **CORS origins** to your actual domains

### ❌ DON'T:
- Expose service_role key in frontend code
- Store passwords in plain text
- Disable RLS policies
- Use default/weak admin passwords
- Allow public access to storage buckets

---

## Data Privacy Compliance

Since this system stores government ID images:

1. **Inform Customers**: Update privacy policy to mention ID storage
2. **Secure Storage**: Supabase provides encrypted storage at rest
3. **Access Control**: Only authenticated admins can view images
4. **Data Retention**: Implement policies for how long to keep images
5. **Audit Logs**: Monitor who accesses customer data

---

## Maintenance

### Regular Tasks:

**Daily:**
- Monitor for new customers
- Review pending applications

**Weekly:**
- Check storage usage in Supabase
- Review admin access logs

**Monthly:**
- Backup customer database
- Review and update RLS policies
- Check for Supabase platform updates

### Storage Limits:

**Supabase Free Tier:**
- 1GB storage included
- ~500-1000 high-res ID images

**If approaching limit:**
- Upgrade to Supabase Pro ($25/month)
- Implement image compression
- Archive old customer data

---

## Support

### Issues with Setup:
1. Check this guide's troubleshooting section
2. Review Supabase logs: Dashboard → Logs
3. Review Railway logs: Service → Deployments

### Supabase Documentation:
- Storage: https://supabase.com/docs/guides/storage
- Auth: https://supabase.com/docs/guides/auth
- RLS: https://supabase.com/docs/guides/auth/row-level-security

### Railway Documentation:
- Environment Variables: https://docs.railway.app/develop/variables
- Deployments: https://docs.railway.app/deploy/deployments

---

## Summary

The new admin system provides:

✅ **Professional UI** - Modern, responsive design  
✅ **Complete Data Access** - All customer information in one place  
✅ **ID Image Storage** - Secure viewing of government IDs  
✅ **Search & Filter** - Easy data management  
✅ **Export Capability** - CSV downloads for reporting  
✅ **Secure Authentication** - Admin-only access  

**Status**: Ready for production use with real customer data.

**Last Updated**: January 10, 2026
