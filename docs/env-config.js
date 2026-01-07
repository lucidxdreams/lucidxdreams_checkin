/**
 * Environment Configuration
 * 
 * This file should be replaced or modified during deployment to inject
 * environment-specific values. You can either:
 * 
 * 1. Replace this file during CI/CD with actual values
 * 2. Use a server-side template to inject values
 * 3. Set these values via your hosting platform's environment variable injection
 * 
 * For GitHub Pages or static hosting, replace the empty strings with your actual values.
 * For dynamic hosting (Railway, Vercel, etc.), you can inject these at build time.
 */

// Environment variables - set these for your deployment
window.ENV_SUPABASE_URL = '';  // e.g., 'https://your-project.supabase.co'
window.ENV_SUPABASE_ANON_KEY = '';  // e.g., 'your-anon-key'
window.ENV_API_BASE_URL = '';  // e.g., 'https://your-api.railway.app' or leave empty for same-origin
