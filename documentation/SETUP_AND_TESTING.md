# Setup and Testing Guide

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- Node.js (for Playwright browser installation)
- 8GB+ RAM recommended (for OCR models)

### Step 1: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Install Playwright Browsers

```bash
# Install Playwright browsers (Chromium, Firefox, WebKit)
playwright install chromium

# Or install all browsers
playwright install
```

### Step 3: Verify Installation

```bash
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

---

## 🧪 Testing Strategy

### Phase 1: OCR Testing (Manual)

Test OCR extraction with different ID types:

```bash
cd backend
python test_ocr.py
```

**Test with:**
1. DC Driver's License (front)
2. DC Real ID
3. Other state driver's license
4. US Passport
5. Faded/worn ID (low quality)
6. Rotated ID (test auto-rotation)

**Expected Output:**
```json
{
  "success": true,
  "data": {
    "firstName": "John",
    "lastName": "Doe",
    "dateOfBirth": "1990-01-15",
    "street": "123 Main St NW",
    "zip": "20001"
  },
  "confidence": 0.92,
  "ocrEngine": "surya"
}
```

### Phase 2: Browser Automation Testing (Visible)

Test form submission with visible browser:

```python
# backend/test_automation.py
from quickbase_browser_automation import QuickBaseFormAutomation

automation = QuickBaseFormAutomation(
    headless=False,  # Show browser
    slow_mo=500      # Slow down by 500ms per action
)

test_data = {
    'firstName': 'Test',
    'lastName': 'User',
    'dateOfBirth': '1990-01-15',
    'street': '123 Main St NW',
    'zip': '20001',
    'phoneNumber': '(202) 555-0123',
    'email': 'test@example.com',
    'idImageBase64': '<base64-encoded-image>'
}

result = automation.submit_application(test_data)
print(result)
```

**Watch for:**
- ✅ All fields filled correctly
- ✅ Dropdowns selected properly
- ✅ Files uploaded successfully
- ✅ Checkboxes checked
- ✅ Form submitted without errors
- ✅ Redirect to success page

### Phase 3: End-to-End Testing

```bash
# Terminal 1: Start backend
cd backend
python app.py

# Terminal 2: Test endpoints
curl -X POST http://localhost:5000/api/extract-id \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/jpeg;base64,..."}'

curl -X POST http://localhost:5000/api/submit-application \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "dateOfBirth": "1990-01-15",
    "street": "123 Main St NW",
    "zip": "20001",
    "phoneNumber": "(202) 555-0123",
    "email": "john@example.com",
    "idImageBase64": "data:image/jpeg;base64,..."
  }'
```

### Phase 4: Frontend Integration Testing

Open `frontend/index.html` in browser and test:

1. **Upload ID Image**
   - Drag & drop
   - Click to select
   - File size validation (max 10MB)
   - File type validation (JPG, PNG, PDF)

2. **View Extracted Data**
   - All fields populated from OCR
   - User can review/edit
   - Validation messages clear

3. **Enter Contact Info**
   - Phone auto-formats as typed
   - Email validation works
   - Re-enter email matches

4. **Submit Application**
   - Loading states display
   - Progress indicators work
   - Success message shown
   - Error handling graceful

---

## 🎯 Test Scenarios

### Scenario 1: Happy Path (21+ with DC Address)
```
Input:
- DOB: 1990-01-15 (Age: 33)
- Address: Washington, DC
- Valid phone & email
- Clear ID image

Expected: ✅ Success - Application submitted
```

### Scenario 2: Under 21
```
Input:
- DOB: 2010-01-15 (Age: 15)

Expected: ❌ Error - "Self-certification requires age 21+"
```

### Scenario 3: Poor Quality ID
```
Input:
- Blurry/faded ID image
- OCR confidence < 80%

Expected: ⚠️ Warning - Switch to EasyOCR fallback, show extracted data for review
```

### Scenario 4: Missing Required Field
```
Input:
- No phone number provided

Expected: ❌ Error - "Missing required fields: phoneNumber"
```

### Scenario 5: Invalid Email Format
```
Input:
- Email: "notanemail"

Expected: ❌ Error - "Invalid email format"
```

### Scenario 6: File Too Large
```
Input:
- ID image > 10MB

Expected: ❌ Error - "File size exceeds 10MB limit"
```

### Scenario 7: Network Failure
```
Simulate: Disconnect network during submission

Expected: ❌ Error - "Network error. Please try again."
```

### Scenario 8: Form Validation Error on QuickBase
```
Simulate: Submit with invalid data format

Expected: ❌ Error - Screenshot captured, error messages displayed
```

---

## 🐛 Debugging Tips

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### View Browser in Non-Headless Mode
```python
automation = QuickBaseFormAutomation(headless=False, slow_mo=1000)
```

### Capture Screenshots at Each Step
```python
page.screenshot(path=f"step_{step_number}.png")
```

### Inspect Form HTML in Real-Time
```python
# In Playwright script
page.pause()  # Opens Playwright Inspector
```

### Check Temporary Files
```bash
ls -lh /tmp/*id*.jpg
```

### Monitor Network Requests
```python
page.on("request", lambda request: print(f">> {request.method} {request.url}"))
page.on("response", lambda response: print(f"<< {response.status} {response.url}"))
```

---

## 📊 Performance Benchmarks

### Expected Processing Times

| Operation | Time | Notes |
|-----------|------|-------|
| OCR Extraction (Surya) | 2-5s | CPU-only, faster with GPU |
| OCR Extraction (EasyOCR) | 3-8s | Fallback engine |
| Browser Launch | 1-2s | Chromium startup |
| Form Fill & Submit | 3-5s | Includes file upload |
| **Total End-to-End** | **8-15s** | From upload to confirmation |

### Optimization Tips
1. **Use GPU for OCR:** 5-10x faster
2. **Reuse Browser Context:** Save 1-2s per submission
3. **Preload OCR Models:** Save 2-3s on first request
4. **Compress Images:** Reduce upload time

---

## 🔒 Security Testing

### Test Cases

1. **SQL Injection in Text Fields**
   ```
   Input: firstName = "'; DROP TABLE--"
   Expected: ✅ No SQL injection (browser automation escapes inputs)
   ```

2. **XSS in Text Fields**
   ```
   Input: firstName = "<script>alert('xss')</script>"
   Expected: ✅ HTML entities escaped
   ```

3. **File Upload Validation**
   ```
   Input: Upload .exe file as ID
   Expected: ❌ Error - "Invalid file type"
   ```

4. **Base64 Decode Attacks**
   ```
   Input: Malformed base64 in idImageBase64
   Expected: ❌ Error - "Invalid image data"
   ```

5. **Rate Limiting**
   ```
   Input: 100 requests in 1 minute
   Expected: ⚠️ Rate limit applied (if configured)
   ```

---

## 📝 Test Checklist

Before deploying to production:

### Backend Tests
- [ ] OCR extracts all fields correctly from DC license
- [ ] OCR handles low-quality images gracefully
- [ ] Age validation works (21+ requirement)
- [ ] API endpoints return proper HTTP status codes
- [ ] Error messages are user-friendly
- [ ] Temporary files are cleaned up

### Browser Automation Tests
- [ ] Form loads without errors
- [ ] All fields populated correctly
- [ ] File uploads work reliably
- [ ] Conditional fields show/hide properly
- [ ] Checkboxes are checked automatically
- [ ] Form submits successfully
- [ ] Success page redirect detected
- [ ] Error states captured with screenshots

### Frontend Tests
- [ ] File upload UI works (drag & drop + click)
- [ ] File validation (size, type) works
- [ ] OCR extracted data displays correctly
- [ ] User can edit extracted data
- [ ] Phone number auto-formats
- [ ] Email validation works
- [ ] Loading states show during processing
- [ ] Success message displays after submission
- [ ] Error messages are clear and actionable

### Integration Tests
- [ ] Full flow: Upload → Extract → Review → Submit
- [ ] Multiple submissions in sequence
- [ ] Handles concurrent requests
- [ ] Works across browsers (Chrome, Firefox, Safari)
- [ ] Mobile responsive (if applicable)

### Security Tests
- [ ] No sensitive data logged
- [ ] Temporary files deleted
- [ ] No XSS vulnerabilities
- [ ] File upload restrictions enforced
- [ ] HTTPS enforced in production

---

## 🚨 Known Issues & Workarounds

### Issue 1: Playwright Installation Fails on M1 Mac
**Error:** `Cannot find browser executable`
**Solution:**
```bash
PLAYWRIGHT_BROWSERS_PATH=$HOME/pw-browsers playwright install chromium
export PLAYWRIGHT_BROWSERS_PATH=$HOME/pw-browsers
```

### Issue 2: OCR Model Download Timeout
**Error:** `Failed to download model`
**Solution:**
```python
import os
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'
```

### Issue 3: Form JavaScript Not Executing
**Symptom:** Fields not showing/hiding correctly
**Solution:** Add delays after triggering events
```python
page.fill('input[name="_fid_11"]', dob)
page.wait_for_timeout(500)  # Wait for JavaScript
```

### Issue 4: File Upload Fails Silently
**Symptom:** No error, but file not uploaded
**Solution:** Verify file path is absolute
```python
import os
abs_path = os.path.abspath(file_path)
page.set_input_files('input[name="_fid_50"]', abs_path)
```

---

## 📈 Monitoring & Logging

### Production Logging Setup

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
```

### Key Metrics to Track
- OCR success rate (% with confidence > 80%)
- Average OCR processing time
- Form submission success rate
- Average end-to-end processing time
- Error rate by error type
- Files processed per hour

### Alerts to Configure
- Error rate > 5% in 5 minutes
- Average processing time > 30 seconds
- Disk space < 10% (for temp files)
- Memory usage > 80%

---

**Last Updated:** January 3, 2026  
**Status:** Ready for testing
