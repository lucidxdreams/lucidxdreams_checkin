# Complete QuickBase Form Field Mapping

**Form Action:** `https://octo.quickbase.com/db/bscn22vp9?act=API_AddRecord&apptoken=cwfcy7gdzqrsyncqbi2bn4u4kr`  
**Table ID:** `bscn22vp9` (not bscn22va8 - this is the actual submission table!)  
**Method:** POST with multipart/form-data  
**Redirect After Submit:** `https://octo.quickbase.com/db/bscn22va8?a=dbpage&pageID=18`

---

## 📋 All Form Fields (31 Total)

### Section 1: DC Resident Patient Information

| Field ID | Label | Type | Required | Default Value | Validation | Source |
|----------|-------|------|----------|---------------|------------|--------|
| `_fid_76` | Application Type | dropdown | ✅ Yes | - | Initial / Renewal / Card Request | User Input |
| `_fid_6` | First Name | text | ✅ Yes | - | - | **OCR** |
| `_fid_7` | Middle Initial | text | ❌ No | - | Max 1 char | **OCR** (optional) |
| `_fid_8` | Last Name | text | ✅ Yes | - | - | **OCR** |
| `_fid_35` | Suffix | text | ❌ No | - | Jr., Sr., III, etc. | **OCR** (optional) |
| `_fid_122` | DC DMV Real ID | dropdown | ✅ Yes | "No" | Yes / No | User Input |
| `_fid_11` | Date of Birth | date | ✅ Yes | - | Must be 18+ | **OCR** |
| `_fid_12` | Street | text | ✅ Yes | - | - | **OCR** |
| `_fid_13` | Apt/Suite | text | ❌ No | - | - | **OCR** (optional) |
| `_fid_14` | City | text | ✅ Yes | "Washington" | - | Static (Washington) |
| `_fid_15` | State | dropdown | ✅ Yes | "DC" | US States | Static (DC) |
| `_fid_16` | Zip | text | ✅ Yes | - | 5 digits | **OCR** |
| `_fid_17` | Phone | phone | ✅ Yes | - | (XXX) XXX-XXXX format | **User Input** |
| `_fid_18` | Email | email | ✅ Yes | - | Valid email format | **User Input** |
| `_fid_117` | Reenter Email | email | ✅ Yes | - | Must match _fid_18 | **User Input** |

### Section 2: Recommendation Information

| Field ID | Label | Type | Required | Conditional Logic | Source |
|----------|-------|------|----------|-------------------|--------|
| `_fid_124` | Certification Type | dropdown | ✅ Yes* | Only shown if age >= 21 | **Static (Self certification)** |
| `_fid_19` | Recommendation Number | text | ✅ Yes* | Only if "Recommendation" selected | Hidden (Self cert) |
| `_fid_36` | Healthcare Professional First Name | text | ✅ Yes* | Only if "Recommendation" selected | Hidden (Self cert) |
| `_fid_38` | Healthcare Professional Last Name | text | ✅ Yes* | Only if "Recommendation" selected | Hidden (Self cert) |

**Note:** Fields marked * are conditionally required based on age and certification type. For self-certification (our use case), recommendation fields are hidden.

### Section 3: Required Documents

| Field ID | Label | Type | Required | Conditional Logic | Source |
|----------|-------|------|----------|-------------------|--------|
| `_fid_50` | Government ID | file | ✅ Yes | Always required | **User Upload** |
| `_fid_55` | Proof of Residency #1 | file | ✅ Yes* | Required if Real ID = "No" | User Upload (optional) |
| `_fid_121` | DC DMV Real ID | file | ✅ Yes* | Required if Real ID = "Yes" | User Upload (optional) |

### Section 4: Reduced Fee (Optional)

| Field ID | Label | Type | Required | Conditional Logic | Source |
|----------|-------|------|----------|-------------------|--------|
| (no fid) | Below FPL? | dropdown | ❌ No | Triggers reduced fee fields | User Input (default: No) |
| `_fid_64` | Medicaid/DC Alliance Card | file | ✅ Yes* | Required if reduced fee = Yes | User Upload (skip) |
| `_fid_57` | Proof of Income #1 | file | ❌ No | Optional if reduced fee = Yes | User Upload (skip) |
| `_fid_58` | Proof of Income #2 | file | ❌ No | Optional if reduced fee = Yes | User Upload (skip) |

### Section 5: Caregiver (Optional)

| Field ID | Label | Type | Required | Source |
|----------|-------|------|----------|--------|
| `_fid_119` | Caregiver Application | file | ❌ No | User Upload (skip for now) |

### Section 6: Signature

| Field ID | Label | Type | Required | Default Value | Source |
|----------|-------|------|----------|---------------|--------|
| `_fid_72` | Terms & Conditions Checkbox | checkbox | ✅ Yes | - | Auto-check |
| `_fid_176` | Self Certification Checkbox | checkbox | ✅ Yes* | - | Auto-check (if self-cert) |
| `_fid_59` | First and Last Name (Signature) | text | ✅ Yes | - | OCR (First + Last) |
| `_fid_60` | Date | date | ✅ Yes | Today's date | Auto-filled |

### Hidden Fields

| Field | Value |
|-------|-------|
| `fform` | "1" |
| `rdr` | "https://octo.quickbase.com/db/bscn22va8?a=dbpage&pageID=18" |

---

## 🎯 Our Automation Strategy

### Fields We'll Auto-Fill from OCR:

1. **_fid_6** - First Name ← Extract from ID
2. **_fid_7** - Middle Initial ← Extract from ID (if present)
3. **_fid_8** - Last Name ← Extract from ID
4. **_fid_35** - Suffix ← Extract from ID (if present)
5. **_fid_11** - Date of Birth ← Extract from ID (format: YYYY-MM-DD)
6. **_fid_12** - Street ← Extract from ID
7. **_fid_13** - Apt/Suite ← Extract from ID (if present)
8. **_fid_16** - Zip ← Extract from ID

### Fields We'll Use User Input:

1. **_fid_17** - Phone ← User enters manually
2. **_fid_18** - Email ← User enters manually
3. **_fid_117** - Reenter Email ← Copy from _fid_18
4. **_fid_50** - Government ID ← User uploads (same file as OCR source)

### Fields We'll Set to Static Values:

1. **_fid_76** - Application Type = **"Initial"**
2. **_fid_122** - DC DMV Real ID = **"No"** (will trigger proof of residency requirement)
3. **_fid_14** - City = **"Washington"** (pre-filled)
4. **_fid_15** - State = **"DC"** (pre-filled)
5. **_fid_124** - Certification Type = **"Self certification"** (if age >= 21)
6. **_fid_59** - Signature = Concatenate First Name + Last Name from OCR
7. **_fid_60** - Date = Today's date (auto-filled by form)

### Fields We'll Handle with Additional Logic:

1. **_fid_55** - Proof of Residency #1 
   - If Real ID = "No", use the same Government ID file
   - OR ask user to upload separate proof of residency

### Fields We'll Skip (Not in Scope):

1. **_fid_19** - Recommendation Number (hidden for self-cert)
2. **_fid_36** - Healthcare Professional First Name (hidden)
3. **_fid_38** - Healthcare Professional Last Name (hidden)
4. **_fid_121** - DC DMV Real ID file (we're using Real ID = "No")
5. **_fid_64, _fid_57, _fid_58** - Reduced fee documents (optional)
6. **_fid_119** - Caregiver Application (optional)

### Checkboxes We'll Auto-Check:

1. **_fid_72** - Terms & Conditions = **checked**
2. **_fid_176** - Self Certification = **checked** (if age >= 21 and self-cert)

---

## 🔄 Form Submission Logic

### Step-by-Step Flow:

```
1. User uploads Government ID image
2. Backend extracts data via OCR (Surya/EasyOCR)
3. User enters Phone and Email
4. Frontend shows extracted data for confirmation
5. User clicks "Submit Application"
6. Browser automation (Playwright) executes:
   
   a. Navigate to form URL
   b. Fill all text fields with OCR data
   c. Fill phone and email from user input
   d. Set dropdown values (Application Type, Real ID, State, etc.)
   e. Upload Government ID file to _fid_50
   f. Upload same file to _fid_55 (Proof of Residency)
   g. Check both checkboxes (_fid_72, _fid_176)
   h. Click Submit button
   i. Wait for redirect to confirmation page
   j. Extract success message or record ID
   
7. Return success/failure to user
```

---

## ⚠️ Important Validation Rules

### Age-Based Logic:
```javascript
// Form has JavaScript that checks age:
if (age >= 21) {
  // Show Certification Type dropdown
  // Show Self Certification checkbox
  // Can choose "Self certification" or "Recommendation"
} else {
  // Hide Certification Type
  // Hide Self Certification checkbox
  // Force "Recommendation" path (require healthcare professional info)
}
```

**Our Strategy:** Extract DOB from ID, calculate age. If < 21, show error to user (cannot use self-certification).

### Real ID Logic:
```javascript
// Form toggles based on Real ID selection:
if (Real ID == "Yes") {
  // Show _fid_121 (DC DMV Real ID file upload)
  // Hide _fid_55 (Proof of Residency #1)
} else {
  // Hide _fid_121
  // Show _fid_55 (Proof of Residency #1) - REQUIRED
}
```

**Our Strategy:** Set Real ID = "No" and upload Government ID to both _fid_50 AND _fid_55.

### Email Validation:
- Form uses jQuery validation
- _fid_117 must match _fid_18 exactly
- Must be valid email format

### Phone Formatting:
- Form applies mask: `(999) 999-9999`
- Input automatically formatted as user types

### Date Format:
- _fid_11 (DOB): `YYYY-MM-DD` (HTML5 date input)
- _fid_60 (Signature Date): Auto-set to today, read-only

---

## 📝 Sample Submission Data

```json
{
  "fform": "1",
  "_fid_76": "Initial",
  "_fid_6": "John",
  "_fid_7": "M",
  "_fid_8": "Doe",
  "_fid_35": "",
  "_fid_122": "No",
  "_fid_11": "1990-01-15",
  "_fid_12": "123 Main St NW",
  "_fid_13": "Apt 4B",
  "_fid_14": "Washington",
  "_fid_15": "DC",
  "_fid_16": "20001",
  "_fid_17": "(202) 555-0123",
  "_fid_18": "john.doe@example.com",
  "_fid_117": "john.doe@example.com",
  "_fid_124": "Self certification",
  "_fid_50": "[FILE: government_id.jpg]",
  "_fid_55": "[FILE: government_id.jpg]",
  "_fid_72": "on",
  "_fid_176": "on",
  "_fid_59": "John Doe",
  "_fid_60": "2026-01-03",
  "rdr": "https://octo.quickbase.com/db/bscn22va8?a=dbpage&pageID=18"
}
```

---

## 🚨 Critical Discoveries

### 1. **Wrong Table ID in PRD!**
- PRD mentions table: `bscn22va8`
- Actual submission table: **`bscn22vp9`**
- The form submits to a DIFFERENT table than the page URL!

### 2. **App Token Available**
The form includes an app token in the action URL:
```
apptoken=cwfcy7gdzqrsyncqbi2bn4u4kr
```
This is publicly visible in the HTML. We could potentially use this with the API approach if we can get proper authentication!

### 3. **No Authentication Required for Form**
The form page itself doesn't require login - it's publicly accessible. This makes browser automation straightforward.

### 4. **File Upload Requirements**
- Multiple file fields
- Same file can be used for multiple fields (_fid_50 and _fid_55)
- No explicit size limits in HTML (but PRD says 10MB)

### 5. **Conditional Field Logic**
Form uses extensive JavaScript to show/hide fields based on:
- Age (from DOB)
- Real ID selection
- Certification Type
- Reduced Fee status

We need to handle these in the correct order.

---

## Next Steps

1. ✅ Field mapping complete
2. ⏭️ Create Playwright automation script
3. ⏭️ Update backend to use browser automation
4. ⏭️ Create testing scenarios
5. ⏭️ Update PRD with correct table ID

**Status:** Ready to build automation  
**Last Updated:** January 3, 2026
