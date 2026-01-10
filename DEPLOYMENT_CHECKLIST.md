# Deployment Checklist - Admin System

## Pre-Deployment

- [ ] Review `ADMIN_SETUP_GUIDE.md`
- [ ] Backup existing Supabase database
- [ ] Test current system is working

## Database Updates

- [ ] Run SQL schema updates in Supabase SQL Editor
- [ ] Verify `customer-ids` storage bucket created
- [ ] Verify RLS policies applied
- [ ] Test storage upload with test image

## Backend Configuration

- [ ] Add `SUPABASE_URL` to Railway environment variables
- [ ] Add `SUPABASE_SERVICE_KEY` to Railway environment variables
- [ ] Verify `supabase>=2.3.4` in requirements.txt
- [ ] Commit and push backend changes
- [ ] Verify Railway deployment successful
- [ ] Check Railway logs for "Supabase client initialized"

## Admin User Setup

- [ ] Create admin user in Supabase Auth
- [ ] Save admin credentials securely
- [ ] Test login to Supabase dashboard

## Frontend Deployment

- [ ] Verify `env-config.js` has correct Supabase URL and anon key
- [ ] Commit new `admin.html` to repository
- [ ] Push to GitHub (auto-deploys to GitHub Pages)
- [ ] Wait 2-3 minutes for deployment

## Testing

- [ ] Access admin dashboard at `https://lucidxdreams.github.io/admin.html`
- [ ] Login with admin credentials
- [ ] Verify customer list loads
- [ ] Test search functionality
- [ ] Test status filter
- [ ] Submit test application with ID image
- [ ] Verify new customer appears in admin
- [ ] View customer details modal
- [ ] Verify ID images display correctly
- [ ] Test CSV export
- [ ] Test refresh button

## Verification

- [ ] Check Supabase Storage has test images
- [ ] Check Railway logs for successful image uploads
- [ ] Verify no console errors in browser
- [ ] Test on mobile device
- [ ] Test with real customer data (if available)

## Documentation

- [ ] Update README.md with admin dashboard URL
- [ ] Document admin credentials location
- [ ] Share access instructions with team

## Post-Deployment

- [ ] Monitor Railway logs for errors
- [ ] Monitor Supabase storage usage
- [ ] Set up alerts for storage limits
- [ ] Schedule regular backups

## Rollback Plan (If Issues)

If deployment fails:

1. Revert database schema changes:
   ```sql
   ALTER TABLE customers DROP COLUMN IF EXISTS id_front_url;
   ALTER TABLE customers DROP COLUMN IF EXISTS id_back_url;
   DELETE FROM storage.buckets WHERE id = 'customer-ids';
   ```

2. Remove backend environment variables from Railway

3. Revert git commits:
   ```bash
   git revert HEAD
   git push
   ```

4. Use old admin.html from git history if needed

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Status**: ☐ Success  ☐ Failed  ☐ Rolled Back
