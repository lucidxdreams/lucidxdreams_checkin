# Database Migration Required

## Critical: Add Required Columns to Customers Table

The following database schema changes are required:

### SQL Migration (Run in Supabase SQL Editor)

```sql
-- Add barcode column to customers table
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS barcode TEXT;

-- Add location column to customers table
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS location TEXT;

-- Create indexes for faster lookups (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_customers_barcode ON customers(barcode);
CREATE INDEX IF NOT EXISTS idx_customers_location ON customers(location);
```

### Verify Columns Exist

After running the migration, verify the columns were added:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'customers' AND column_name IN ('barcode', 'location');
```

### Expected Schema

The `customers` table should now include:
- `barcode` (TEXT, nullable) - Stores driver's license barcode number from ID scan
- `location` (TEXT, nullable) - Stores selected dispensary location

## Storage Bucket Verification

Ensure the `customer-ids` storage bucket exists and has public access enabled:

1. Go to Supabase Dashboard → Storage
2. Verify bucket `customer-ids` exists
3. Ensure bucket policies allow:
   - Authenticated users can INSERT
   - Public can SELECT (for viewing images)

### Create Bucket (if missing)

```sql
-- Create storage bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('customer-ids', 'customer-ids', true)
ON CONFLICT (id) DO NOTHING;
```

### Set Bucket Policies

```sql
-- Allow authenticated users to upload
CREATE POLICY "Authenticated users can upload ID images"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'customer-ids');

-- Allow public access to view images
CREATE POLICY "Public can view ID images"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'customer-ids');
```

## Deployment Checklist

- [ ] Run SQL migration to add barcode column
- [ ] Verify `customer-ids` storage bucket exists
- [ ] Check bucket policies allow upload and public read
- [ ] Test image upload and retrieval
- [ ] Verify barcode data is saved correctly
- [ ] Test date filter on admin dashboard
- [ ] Confirm no duplicate entries are created

## Rolling Back (If Needed)

To remove the new columns:

```sql
ALTER TABLE customers DROP COLUMN IF EXISTS barcode;
ALTER TABLE customers DROP COLUMN IF EXISTS location;
DROP INDEX IF EXISTS idx_customers_barcode;
DROP INDEX IF EXISTS idx_customers_location;
```
