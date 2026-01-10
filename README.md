Do you meet the requirements for a reduced application fee?# Lucid x Dreams - Dispensary Check-in System

In-store check-in system for Lucid x Dreams Medical Cannabis Dispensary. Customers can verify their ID, submit medical cannabis applications to DC ABCA, and check in with their registration.

## Features

- **Welcome Screen** - Business branding with logo and store information
- **Smart ID Upload** - Streamlined mobile experience:
  - Front of ID: Uses native device file picker (camera/gallery)
  - Back of ID: Live barcode scanner with professional scanning animation
  - Compact filename display after upload
  - Automatic fallback to manual upload if scanner times out
- **ID Verification** - Front photo + PDF417 barcode scanning from driver's license
- **Medical Card Detection** - Different flows for existing vs new cardholders
- **DC & Non-DC Residents** - Support for both DC residents and visitors
- **QuickBase Integration** - Automated form submission to DC ABCA portal
- **Supabase Integration** - Cloud database for customer records and ID image storage
- **Professional Admin Dashboard** - Complete customer data access with ID image viewing
- **Modern UI** - Professional dark theme with smooth animations

## Customer Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Welcome Page  │────▶│  ID Capture +   │────▶│   Check-in      │
│   (Check-in)    │     │  Card Question  │     │   Complete      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              Has Card: YES          Has Card: NO
              (Skip to Check-in)     (Submit Application)
```

### Flow Details

| Step | Has Existing Card (YES) | New Customer (NO) |
|------|------------------------|-------------------|
| 1 | Welcome → Check-in button | Welcome → Check-in button |
| 2 | Upload Front ID → Live barcode scan | Upload Front ID → Live barcode scan |
| 3 | Enter Registration ID → Check-in | Verify info → Submit application |
| 4 | Done | Enter Registration ID → Check-in |

### ID Upload Experience

1. **Front of ID**: Tap to upload - uses native mobile options (Photo Library, Take Photo, Choose File)
2. **After Front Upload**: Shows compact filename display (e.g., "IMG_1234.jpeg ✓")
3. **Back of ID Scanner**: Full-width professional scanner with:
   - Animated green scanning line
   - Corner bracket frame overlay
   - Pulsing grid animation
   - Status indicator with live feedback
4. **Fallback**: After 15 seconds, manual upload option appears

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | HTML/CSS/JavaScript |
| Backend | Flask + Gunicorn (Production) |
| Barcode | zxing-cpp (PDF417) |
| OCR | Surya OCR |
| Browser Automation | Playwright (Chromium) |
| Database | Supabase (PostgreSQL) |
| Hosting | GitHub Pages (frontend) / Railway (backend) |

## Quick Start

### Option 1: Frontend Only (Static Hosting)

The frontend works standalone and can be hosted on GitHub Pages. Barcode scanning requires the backend server.

```bash
# Serve frontend locally
cd frontend
python3 -m http.server 8080
# Open http://localhost:8080
```

### Option 2: Full Setup (with Barcode Scanning)

#### Prerequisites
- Python 3.11+
- macOS: `brew install zbar`
- Ubuntu: `sudo apt-get install libzbar0`

#### Setup Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright (for browser automation)
playwright install chromium

# Start server
python app.py
```

Server runs at **http://localhost:5001**

#### Serve Frontend

```bash
# In another terminal
cd frontend
python3 -m http.server 8080
```

Open **http://localhost:8080**

## Supabase Setup (Cloud Database)

For persistent customer data accessible from anywhere:

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Run SQL from `docs/SUPABASE_SETUP.md` to create tables
4. Update credentials in `frontend/index.html`:

```javascript
const SUPABASE_URL = 'https://YOUR_PROJECT.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key';
```

See `docs/SUPABASE_SETUP.md` for detailed instructions.

## Project Structure

```
medical_card_submission/
├── frontend/
│   ├── index.html                    # Main check-in app
│   ├── admin.html                    # Admin dashboard
│   ├── terms.html                    # Terms of service
│   ├── privacy.html                  # Privacy policy
│   └── logo/                         # Business logo
├── backend/
│   ├── app.py                        # Flask server (production-ready)
│   ├── barcode_service.py            # PDF417 barcode scanning
│   ├── ocr_service.py                # ID OCR extraction
│   ├── quickbase_browser_automation.py  # ABCA form automation
│   ├── dc_addresses.json             # DC address database
│   └── requirements.txt              # Python dependencies
├── docs/
│   ├── DEPLOYMENT_GUIDE.md           # Full deployment instructions
│   ├── SUPABASE_SETUP.md             # Database setup guide
│   ├── COMPLETE_FIELD_MAPPING.md     # QuickBase field mapping
│   └── PRD.md                        # Product requirements
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/scan-barcode` | POST | Scan PDF417 barcode from image |
| `/api/parse-barcode` | POST | Parse client-decoded barcode text |
| `/api/extract-id` | POST | OCR extraction from ID photo |
| `/api/submit-application` | POST | Submit application to QuickBase |
| `/api/validate-age` | POST | Validate applicant is 21+ |

## Admin Dashboard Access

### Professional Admin Interface

Access the admin dashboard to view complete customer data including uploaded ID images:

**URL**: `https://lucidxdreams.github.io/admin.html`

### Features:
- 📊 **Dashboard Statistics** - Total, pending, and checked-in counts
- 🔍 **Search & Filter** - Find customers by name, email, phone, or registration ID
- 👤 **Customer Details** - View full profile with all submitted information
- 🆔 **ID Image Viewing** - Secure access to front and back of government IDs
- 📥 **CSV Export** - Download customer data for reporting
- 🔐 **Secure Authentication** - Admin-only access via Supabase Auth

### Setup Instructions:

**First-time setup required** - See `ADMIN_SETUP_GUIDE.md` for detailed instructions:
1. Update database schema (add ID image columns)
2. Configure backend environment variables
3. Create admin user in Supabase Auth
4. Deploy and test

**Quick Deploy**: See `DEPLOYMENT_CHECKLIST.md` for step-by-step deployment verification.

---

## Deployment to Production

### Quick Overview

| Component | Service | Cost |
|-----------|---------|------|
| **Frontend** | GitHub Pages | Free |
| **Backend** | Railway / Render | $3-5/month (or free tier) |
| **Database** | Supabase | Free (up to 500MB) |

### Backend Hosting Options

**Railway (Recommended)** ⭐
- $3-5/month for 500 hours uptime
- Automatic GitHub deployments
- Built-in HTTPS domain
- Best for: Production use

**Render**
- Free tier available (spins down after 15 min)
- $7/month for always-on
- Best for: Testing or low-traffic

**Fly.io**
- Free tier: 3 small VMs
- Edge deployment
- Best for: Global users

### Complete Setup Guide

See **`docs/DEPLOYMENT_GUIDE.md`** for:
- Step-by-step Railway deployment
- GitHub Pages setup
- Supabase configuration
- Connecting all services
- Custom domain setup
- Production testing checklist

**Total setup time: ~30 minutes**

## Troubleshooting

### Check-in Button Not Working
- Check browser console for JavaScript errors
- Ensure logo file exists at `frontend/logo/logo.webp`

### Flask ModuleNotFoundError
```bash
cd backend
source venv/bin/activate  # Activate virtual environment first!
pip install -r requirements.txt
```

### Barcode Not Detected
- Ensure good lighting on the barcode
- Hold ID 6-12 inches from camera
- Make sure entire barcode is visible

### Supabase Not Saving
- Verify credentials are correct (not placeholders)
- Check browser console for errors
- Ensure RLS policies are created

## Contact

**Lucid x Dreams**  
Medical Cannabis Dispensary  
1334 North Capitol St NW  
Washington, DC 20002  
Email: help@lucidxdreams.com  
Phone: (202) 600-7610

---

© 2026 Lucid x Dreams. All rights reserved.
