/**
 * Environment Configuration for Lucid x Dreams Medical Card Submission
 * 
 * DEPLOYMENT INSTRUCTIONS:
 * ========================
 * 
 * 1. RAILWAY BACKEND:
 *    - Deploy backend folder to Railway
 *    - Copy the Railway URL (e.g., https://your-app.up.railway.app)
 *    - Set ENV_API_BASE_URL below to that URL
 * 
 * 2. SUPABASE (Optional - for admin dashboard):
 *    - Create a Supabase project at https://supabase.com
 *    - Get your Project URL and anon key from Settings > API
 *    - Set ENV_SUPABASE_URL and ENV_SUPABASE_ANON_KEY below
 *    - Run the SQL schema from documentation/supabase_schema.sql
 * 
 * 3. GITHUB PAGES (Frontend):
 *    - Edit this file with your actual values
 *    - Commit and push to deploy
 */

// Backend API URL - REQUIRED for barcode scanning and form submission
window.ENV_API_BASE_URL = 'https://lucidxdreamscheckin-production.up.railway.app';

// Supabase Configuration - enables admin dashboard
window.ENV_SUPABASE_URL = 'https://dzhmckhifjqklaeelsww.supabase.co';
window.ENV_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR6aG1ja2hpZmpxa2xhZWVsc3d3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MjQ4NTksImV4cCI6MjA4MzMwMDg1OX0.KZ_HeRDkvhj_rWQG0xzf857SwiZT7HgrJF-WRFNL1AM';
