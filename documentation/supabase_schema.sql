-- Supabase Schema for Lucid x Dreams Medical Card Submission
-- Run this in your Supabase SQL Editor to set up the database

-- Customers table: stores all customer check-ins and applications
CREATE TABLE IF NOT EXISTS customers (
    id BIGSERIAL PRIMARY KEY,
    
    -- Personal Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    
    -- Contact Information
    email VARCHAR(255),
    phone VARCHAR(20),
    
    -- Address
    street_address VARCHAR(255),
    city VARCHAR(100) DEFAULT 'Washington',
    state VARCHAR(10) DEFAULT 'DC',
    zip_code VARCHAR(10),
    
    -- Registration Details
    registration_id VARCHAR(50),
    expiration_date DATE,
    resident_type VARCHAR(10) CHECK (resident_type IN ('dc', 'nondc')),
    
    -- Consent Flags
    consent_email BOOLEAN DEFAULT FALSE,
    consent_auth BOOLEAN DEFAULT FALSE,
    consent_legal BOOLEAN DEFAULT FALSE,
    has_existing_card BOOLEAN,
    
    -- Status Tracking
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'form_filled', 'checked_in')),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    checked_in_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster searches
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_registration_id ON customers(registration_id);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at DESC);

-- Enable Row Level Security
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Policy: Allow authenticated users to read all customers
CREATE POLICY "Allow authenticated read" ON customers
    FOR SELECT TO authenticated
    USING (true);

-- Policy: Allow authenticated users to insert customers
CREATE POLICY "Allow authenticated insert" ON customers
    FOR INSERT TO authenticated
    WITH CHECK (true);

-- Policy: Allow authenticated users to update customers
CREATE POLICY "Allow authenticated update" ON customers
    FOR UPDATE TO authenticated
    USING (true);

-- Policy: Allow anon users to insert (for public form submissions)
CREATE POLICY "Allow anon insert" ON customers
    FOR INSERT TO anon
    WITH CHECK (true);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL ON customers TO authenticated;
GRANT INSERT ON customers TO anon;
GRANT USAGE, SELECT ON SEQUENCE customers_id_seq TO authenticated, anon;
