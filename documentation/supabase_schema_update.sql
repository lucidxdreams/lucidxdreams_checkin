-- Update customers table to store ID images
-- Run this in your Supabase SQL Editor to add image tracking

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

-- Add comment for documentation
COMMENT ON COLUMN customers.id_front_url IS 'Supabase Storage URL for front of government ID';
COMMENT ON COLUMN customers.id_back_url IS 'Supabase Storage URL for back of government ID';
