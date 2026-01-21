-- SQL command to add the raw_barcode_data column to the customers table
-- Run this in your Supabase Dashboard > SQL Editor

ALTER TABLE customers ADD COLUMN IF NOT EXISTS raw_barcode_data TEXT;

-- Verify the column was added
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'customers';
