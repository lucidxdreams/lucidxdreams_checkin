# PRD: DC Cannabis Medical Card Automated Application System

**Version:** 1.0  
**Date:** January 3, 2026

***

## 1. Overview
Build a web application that captures customer ID uploads, extracts personal information using OCR, and auto-submits to Quickbase for DC cannabis medical card registration.

***

## 2. System Architecture

```
Frontend (HTML/CSS/JS)
    ↓
Backend API (Python/Flask)
    ↓ [Surya OCR → EasyOCR fallback]
    ↓
Quickbase API (Submit record)
```

***

## 3. Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | HTML5, Vanilla JavaScript, CSS |
| **Backend** | Python 3.10+, Flask |
| **OCR Primary** | Surya (surya-ocr package) |
| **OCR Backup** | EasyOCR |
| **API Integration** | Quickbase REST API v1 |
| **File Handling** | Base64 encoding |
| **Deployment** | Docker container |

***

## 4. Core Features

### 4.1 Frontend Form
- **Fields:**
  - Government ID upload (drag-drop + click, JPG/PNG/PDF, max 10MB)
  - Phone number (auto-formatted: `(202) 555-0123`)
  - Email address
- **Display extracted data** for user confirmation before submission
- **Status messages:** Loading, success, error states
- **Pre-filled:** Certification Type = "Self certification"

### 4.2 Backend OCR Service
- **Primary:** Surya OCR extracts text from ID
- **Fallback:** If Surya confidence < 80%, use EasyOCR
- **Extract fields:**
  - First Name
  - Last Name
  - Date of Birth (normalize to MM/DD/YYYY)
  - Address (full)
- **Image preprocessing:** Auto-rotate, denoise, contrast enhancement

### 4.3 Quickbase Integration
- **Endpoint:** `POST https://api.quickbase.com/v1/records`
- **Headers:**
  - `QB-Realm-Hostname: octo.quickbase.com`
  - `Authorization: QB-USER-TOKEN [your-token]`
  - `Content-Type: application/json`
- **Submit:** All extracted + user-entered data
- **File attachment:** Upload original ID image to file field

***

## 5. Project Structure

```
cannabis-card-app/
├── frontend/
│   ├── index.html          # Main form (existing canvas code)
│   ├── styles.css          # Embedded in HTML
│   └── app.js              # Embedded in HTML
├── backend/
│   ├── app.py              # Flask server
│   ├── ocr_service.py      # Surya + EasyOCR logic
│   ├── quickbase_api.py    # Quickbase integration
│   ├── parsers.py          # Extract name/DOB/address from OCR text
│   └── requirements.txt    # Python dependencies
├── config/
│   └── .env                # QB token, realm hostname
├── Dockerfile
├── docker-compose.yml
└── README.md
```

***

## 6. API Endpoints

### `POST /api/extract-id`
**Request:**
```json
{
  "image": "image/jpeg;base64,/9j/4AAQ..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "firstName": "John",
    "lastName": "Doe",
    "dateOfBirth": "01/15/1990",
    "address": "123 Main St NW, Washington, DC 20001"
  },
  "confidence": 0.92,
  "ocrEngine": "surya"
}
```

### `POST /api/submit-application`
**Request:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "dateOfBirth": "01/15/1990",
  "address": "123 Main St NW, Washington, DC 20001",
  "phoneNumber": "(202) 555-0123",
  "email": "john@example.com",
  "idImage": "image/jpeg;base64,..."
}
```

**Response:**
```json
{
  "success": true,
  "quickbaseRecordId": "12345",
  "message": "Application submitted successfully"
}
```

***

## 7. Implementation Steps

### **Step 1: Setup Backend (30 min)**
```bash
mkdir cannabis-card-app && cd cannabis-card-app
mkdir backend frontend config
cd backend

# Create requirements.txt
cat > requirements.txt << EOF
flask==3.0.0
flask-cors==4.0.0
surya-ocr==0.4.0
easyocr==1.7.1
Pillow==10.1.0
python-dotenv==1.0.0
requests==2.31.0
torch==2.1.0
EOF

pip install -r requirements.txt
```

### **Step 2: Create Flask Server (`backend/app.py`)**
```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from ocr_service import extract_id_data
from quickbase_api import submit_to_quickbase
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

@app.route('/api/extract-id', methods=['POST'])
def extract_id():
    try:
        data = request.json
        image_base64 = data.get('image')
        result = extract_id_data(image_base64)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/submit-application', methods=['POST'])
def submit_application():
    try:
        data = request.json
        result = submit_to_quickbase(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### **Step 3: Create OCR Service (`backend/ocr_service.py`)**
```python
from surya.ocr import run_ocr
from surya.model.detection.segformer import load_model as load_det_model
from surya.model.recognition.model import load_model as load_rec_model
import easyocr
from PIL import Image
import io
import base64
from parsers import parse_id_data

# Load models once at startup
surya_det_model = load_det_model()
surya_rec_model = load_rec_model()
easyocr_reader = easyocr.Reader(['en'])

def extract_id_data(image_base64):
    # Decode base64
    image_data = base64.b64decode(image_base64.split(',')[1])
    image = Image.open(io.BytesIO(image_data))
    
    # Try Surya first
    try:
        predictions = run_ocr([image], [surya_det_model], surya_rec_model)
        text = ' '.join([line.text for page in predictions for line in page.text_lines])
        confidence = sum([line.confidence for page in predictions for line in page.text_lines]) / len([line for page in predictions for line in page.text_lines])
        
        if confidence >= 0.80:
            parsed = parse_id_data(text)
            return {
                'success': True,
                'data': parsed,
                'confidence': confidence,
                'ocrEngine': 'surya'
            }
    except Exception as e:
        print(f"Surya failed: {e}")
    
    # Fallback to EasyOCR
    try:
        results = easyocr_reader.readtext(image_data)
        text = ' '.join([item[1] for item in results])
        confidence = sum([item[2] for item in results]) / len(results)
        
        parsed = parse_id_data(text)
        return {
            'success': True,
            'data': parsed,
            'confidence': confidence,
            'ocrEngine': 'easyocr'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'OCR failed: {str(e)}'
        }
```

### **Step 4: Create Parser (`backend/parsers.py`)**
```python
import re
from datetime import datetime

def parse_id_data(text):
    """Extract structured data from OCR text"""
    
    # Extract DOB (various formats)
    dob = extract_dob(text)
    
    # Extract name (usually after "NAME" or at top)
    name = extract_name(text)
    
    # Extract address
    address = extract_address(text)
    
    return {
        'firstName': name.get('first', ''),
        'lastName': name.get('last', ''),
        'dateOfBirth': dob,
        'address': address
    }

def extract_dob(text):
    # Try MM/DD/YYYY, MM-DD-YYYY, MMDDYYYY
    patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # 01/15/1990
        r'DOB[:\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DOB: 01/15/1990
        r'(\d{2})(\d{2})(\d{4})'  # 01151990
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            month, day, year = match.groups()
            return f"{month.zfill(2)}/{day.zfill(2)}/{year}"
    return ''

def extract_name(text):
    # Look for "NAME" field or first capitalized sequence
    name_match = re.search(r'(?:NAME|LN|FN)[:\s]+([A-Z]+)[,\s]+([A-Z]+)', text)
    if name_match:
        return {'last': name_match.group(1).title(), 'first': name_match.group(2).title()}
    
    # Fallback: first two capitalized words
    words = re.findall(r'\b[A-Z][a-z]+\b', text)
    if len(words) >= 2:
        return {'first': words[0], 'last': words[1]}
    
    return {'first': '', 'last': ''}

def extract_address(text):
    # Look for street address pattern (number + street + DC)
    address_match = re.search(r'(\d+\s+[A-Za-z\s]+(?:ST|AVE|RD|BLVD|DR)[^,\n]*[,\s]*Washington[,\s]*DC[,\s]*\d{5})', text, re.IGNORECASE)
    if address_match:
        return address_match.group(1)
    
    # Fallback: look for DC zip code
    zip_match = re.search(r'([^\n]*DC\s+\d{5})', text, re.IGNORECASE)
    if zip_match:
        return zip_match.group(1)
    
    return ''
```

### **Step 5: Create Quickbase API (`backend/quickbase_api.py`)**
```python
import requests
import os
import base64

QB_TOKEN = os.getenv('QUICKBASE_TOKEN')
QB_REALM = 'octo.quickbase.com'
QB_TABLE_ID = 'bscn22va8'  # Your table ID

def submit_to_quickbase(application_data):
    """Submit application to Quickbase"""
    
    url = 'https://api.quickbase.com/v1/records'
    
    headers = {
        'QB-Realm-Hostname': QB_REALM,
        'Authorization': f'QB-USER-TOKEN {QB_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Prepare file attachment
    id_image_base64 = application_data.get('idImage', '').split(',')[1]
    
    payload = {
        'to': QB_TABLE_ID,
        'data': [{
            '6': {'value': application_data['firstName']},        # Field ID 6 = First Name
            '7': {'value': application_data['lastName']},         # Field ID 7 = Last Name
            '8': {'value': application_data['dateOfBirth']},      # Field ID 8 = DOB
            '9': {'value': application_data['address']},          # Field ID 9 = Address
            '10': {'value': application_data['phoneNumber']},     # Field ID 10 = Phone
            '11': {'value': application_data['email']},           # Field ID 11 = Email
            '12': {'value': 'Self certification'},                # Field ID 12 = Cert Type
            '13': {'value': {'fileName': 'id.jpg', 'data': id_image_base64}}  # Field ID 13 = ID File
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return {
            'success': True,
            'quickbaseRecordId': data['metadata']['createdRecordIds'][0],
            'message': 'Application submitted successfully'
        }
    else:
        return {
            'success': False,
            'error': f'Quickbase API error: {response.text}'
        }
```

### **Step 6: Create Environment File (`config/.env`)**
```bash
QUICKBASE_TOKEN=your_token_here
QUICKBASE_REALM=octo.quickbase.com
QUICKBASE_TABLE_ID=bscn22va8
```

### **Step 7: Update Frontend (Modify existing HTML)**
Add these functions to your existing `<script>` section:

```javascript
// Add after existing variables
const BACKEND_URL = 'http://localhost:5000';

// Replace existing handleSubmit function with:
async function handleSubmit(e) {
    e.preventDefault();

    if (!idFileData || !phoneInput.value.trim() || !emailInput.value.trim()) {
        showStatus('Please fill all required fields', 'error');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading-spinner"></span>Extracting ID data...';
    showStatus('Analyzing your ID...', 'loading');

    try {
        // Step 1: Extract ID data using OCR
        const extractResponse = await fetch(`${BACKEND_URL}/api/extract-id`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({image: idFileData})
        });
        
        const extractResult = await extractResponse.json();
        
        if (!extractResult.success) {
            throw new Error('Failed to extract ID data');
        }

        showStatus(`ID data extracted (${Math.round(extractResult.confidence * 100)}% confidence). Submitting...`, 'loading');
        submitBtn.innerHTML = '<span class="loading-spinner"></span>Submitting to Quickbase...';

        // Step 2: Submit to Quickbase
        const submitResponse = await fetch(`${BACKEND_URL}/api/submit-application`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                firstName: extractResult.data.firstName,
                lastName: extractResult.data.lastName,
                dateOfBirth: extractResult.data.dateOfBirth,
                address: extractResult.data.address,
                phoneNumber: phoneInput.value.trim(),
                email: emailInput.value.trim(),
                idImage: idFileData
            })
        });

        const submitResult = await submitResponse.json();

        if (submitResult.success) {
            showStatus(`✓ Application submitted! Record ID: ${submitResult.quickbaseRecordId}`, 'success');
            setTimeout(() => resetForm(), 3000);
        } else {
            throw new Error(submitResult.error);
        }

    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit Application';
    }
}
```

### **Step 8: Docker Setup (Optional)**

**`Dockerfile`:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY config/.env ./config/

EXPOSE 5000

CMD ["python", "backend/app.py"]
```

**`docker-compose.yml`:**
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./backend:/app/backend
      - ./config:/app/config
    environment:
      - FLASK_ENV=development
```

***

## 8. Testing Checklist

- [ ] Upload DC driver's license → Verify name/DOB/address extracted
- [ ] Upload passport → Verify extraction works
- [ ] Test phone formatting (202) 555-0123
- [ ] Test email validation
- [ ] Verify Surya is primary OCR (check console logs)
- [ ] Test EasyOCR fallback (artificially lower Surya confidence)
- [ ] Verify Quickbase record created with correct field IDs
- [ ] Test file size validation (>10MB rejection)
- [ ] Test error states (invalid file, API failures)

***

## 9. Deployment Commands

```bash
# Development
cd backend
python app.py

# Open frontend/index.html in browser

# Production (Docker)
docker-compose up --build
```

***

## 10. Known Issues & TODOs

- **Field IDs:** Update field IDs (6-13) in `quickbase_api.py` with actual Quickbase field IDs
- **Name parsing:** May need tuning for different ID formats
- **GPU:** Surya runs faster with CUDA GPU (optional)
- **Rate limiting:** Add if needed for production

***

**Estimated Build Time:** 2-3 hours  
**Status:** Ready to build in Windsurf

Sources
[1] QuickBase_RESTful_API_2025-12-30T15_55_51.495Z.json https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/124685071/eed44191-16be-4a9c-a656-b97f314a6093/QuickBase_RESTful_API_2025-12-30T15_55_51.495Z.json
