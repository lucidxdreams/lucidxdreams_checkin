"""
Flask Backend for Medical Cannabis Card Application System
Uses browser automation to submit to QuickBase
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy imports for heavy dependencies to prevent startup timeouts
_ocr_service = None
_barcode_service = None
_qb_automation_class = None

def get_ocr_service():
    """Lazy load OCR service"""
    global _ocr_service
    if _ocr_service is None:
        from ocr_service import extract_id_data
        _ocr_service = extract_id_data
    return _ocr_service

def get_barcode_service():
    """Lazy load barcode service"""
    global _barcode_service
    if _barcode_service is None:
        from barcode_service import extract_id_from_barcode
        _barcode_service = extract_id_from_barcode
    return _barcode_service

def get_qb_automation_class():
    """Lazy load QuickBase automation class"""
    global _qb_automation_class
    if _qb_automation_class is None:
        from quickbase_browser_automation import QuickBaseFormAutomation
        _qb_automation_class = QuickBaseFormAutomation
    return _qb_automation_class

# Initialize Flask app
app = Flask(__name__)

# Configure CORS with allowed origins
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://lucidxdreams.github.io')
CORS(app, origins=[
    FRONTEND_URL,
    'https://lucidxdreams.github.io',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost:5001',
    'http://127.0.0.1:5001'
])

# Increase max content length to 50MB for large images
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Frontend directory (HTML files are in docs folder)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')

# Lazy initialization of browser automation instance
_qb_automation_instance = None

def get_qb_automation():
    """Lazy load QuickBase automation instance"""
    global _qb_automation_instance
    if _qb_automation_instance is None:
        QuickBaseFormAutomation = get_qb_automation_class()
        is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT')
        _qb_automation_instance = QuickBaseFormAutomation(headless=bool(is_production))
        logger.info(f"QuickBase automation initialized (headless={bool(is_production)})")
    return _qb_automation_instance


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint - responds quickly without loading heavy dependencies"""
    return jsonify({
        'status': 'healthy', 
        'service': 'medical-card-backend',
        'version': '1.0.0'
    }), 200


@app.route('/api/extract-id', methods=['POST'])
def extract_id():
    """
    Extract information from government ID using OCR
    
    Request body:
    {
        "image": "data:image/jpeg;base64,..."
    }
    
    Response:
    {
        "success": true,
        "data": {
            "firstName": "John",
            "middleInitial": "M",
            "lastName": "Doe",
            "suffix": "",
            "dateOfBirth": "1990-01-15",
            "street": "123 Main St NW",
            "aptSuite": "Apt 4B",
            "city": "Washington",
            "state": "DC",
            "zip": "20001"
        },
        "confidence": 0.92,
        "ocrEngine": "surya",
        "age": 33
    }
    """
    try:
        import time
        request_start = time.time()
        
        data = request.json
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing image data'
            }), 400
        
        image_base64 = data.get('image')
        logger.info("Starting ID extraction...")
        
        # Extract data using OCR (lazy-loaded)
        extract_id_data = get_ocr_service()
        result = extract_id_data(image_base64)
        
        total_time = time.time() - request_start
        logger.info(f"Total ID extraction took {total_time:.2f}s")
        
        if not result.get('success'):
            return jsonify(result), 500
        
        # Calculate age from DOB
        from datetime import datetime
        try:
            dob = result['data'].get('dateOfBirth', '')
            if dob:
                dob_date = datetime.strptime(dob, "%m/%d/%Y")
                today = datetime.today()
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                result['age'] = age
                
                # Convert DOB to YYYY-MM-DD format for form submission
                result['data']['dateOfBirth'] = dob_date.strftime("%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Could not calculate age: {e}")
            result['age'] = None
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error extracting ID: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to extract ID data: {str(e)}'
        }), 500


@app.route('/api/scan-barcode', methods=['POST'])
def scan_barcode():
    """
    Extract information from driver's license barcode (PDF417)
    
    Request body:
    {
        "image": "data:image/jpeg;base64,..."
    }
    
    Response:
    {
        "success": true,
        "data": {
            "firstName": "John",
            "middleInitial": "M",
            "lastName": "Doe",
            "dateOfBirth": "1990-02-12",
            "street": "123 Main St NW",
            "city": "Washington",
            "state": "DC",
            "zip": "20001"
        },
        "isDC": true,
        "scanEngine": "zxing-cpp",
        "processingTime": 0.042,
        "age": 33
    }
    """
    try:
        import time
        request_start = time.time()
        
        data = request.json
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing image data'
            }), 400
        
        image_base64 = data.get('image')
        logger.info("Starting barcode scanning...")
        
        # Extract data using barcode scanner (lazy-loaded)
        extract_id_from_barcode = get_barcode_service()
        result = extract_id_from_barcode(image_base64)
        
        total_time = time.time() - request_start
        logger.info(f"Total barcode scan took {total_time:.2f}s")
        
        if not result.get('success'):
            return jsonify(result), 500
        
        # Calculate age from DOB
        from datetime import datetime
        try:
            dob = result['data'].get('dateOfBirth', '')
            if dob:
                # DOB from barcode is already in YYYY-MM-DD format
                dob_date = datetime.strptime(dob, "%Y-%m-%d")
                today = datetime.today()
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                result['age'] = age
        except Exception as e:
            logger.warning(f"Could not calculate age: {e}")
            result['age'] = None
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error scanning barcode: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to scan barcode: {str(e)}'
        }), 500


@app.route('/api/parse-barcode', methods=['POST'])
def parse_barcode():
    """
    Parse AAMVA barcode text that was decoded client-side via html5-qrcode.
    This is the preferred endpoint for production use - client-side detection
    is faster and more efficient than sending images to the server.
    
    Request body:
    {
        "barcodeText": "@\n\x1e\rANSI 636049030002DL00410466..."
    }
    
    Response:
    {
        "success": true,
        "data": {
            "firstName": "John",
            "middleInitial": "M",
            "lastName": "Doe",
            "dateOfBirth": "1990-02-12",
            "street": "123 Main St NW",
            "city": "Washington",
            "state": "DC",
            "zip": "20001"
        },
        "isDC": true,
        "processingTime": 0.005,
        "age": 33
    }
    """
    try:
        import time
        request_start = time.time()
        
        # Lazy import barcode parsing functions
        from barcode_service import parse_aamva_barcode, format_date, detect_dc_from_barcode, get_random_dc_address
        
        data = request.json
        
        if not data or 'barcodeText' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing barcodeText data'
            }), 400
        
        barcode_text = data.get('barcodeText')
        logger.info(f"Parsing client-decoded barcode ({len(barcode_text)} chars)")
        
        # Parse AAMVA data
        parsed_data = parse_aamva_barcode(barcode_text)
        
        if not parsed_data:
            return jsonify({
                'success': False,
                'error': 'Failed to parse barcode data. The barcode may be damaged or not AAMVA-compliant.'
            }), 400
        
        # Format extracted data
        extracted_data = {}
        
        # Name fields
        if 'firstName' in parsed_data:
            extracted_data['firstName'] = parsed_data['firstName'].title()
        if 'middleName' in parsed_data:
            middle = parsed_data['middleName']
            extracted_data['middleInitial'] = middle[0].upper() if middle else ''
        if 'lastName' in parsed_data:
            extracted_data['lastName'] = parsed_data['lastName'].title()
        if 'suffix' in parsed_data:
            extracted_data['suffix'] = parsed_data['suffix'].upper()
        
        # Date of birth
        if 'dateOfBirth' in parsed_data:
            extracted_data['dateOfBirth'] = format_date(parsed_data['dateOfBirth'])
        
        # Detect DC vs Non-DC
        is_dc = detect_dc_from_barcode(parsed_data)
        
        # Always extract the actual address from ID
        actual_address = {}
        if 'street' in parsed_data:
            actual_address['street'] = parsed_data['street']
        if 'street2' in parsed_data:
            actual_address['aptSuite'] = parsed_data['street2']
        if 'city' in parsed_data:
            actual_address['city'] = parsed_data['city']
        if 'state' in parsed_data:
            actual_address['state'] = parsed_data['state']
        if 'zip' in parsed_data:
            actual_address['zip'] = parsed_data['zip'][:5]
        
        if is_dc:
            # DC ID: Use extracted address
            extracted_data.update(actual_address)
            logger.info("DC ID - Using extracted address")
        else:
            # Non-DC ID: Use random DC address as default, but include actual address
            dc_address = get_random_dc_address()
            extracted_data.update(dc_address)
            # Store actual address separately for Non-DC resident applications
            extracted_data['actualAddress'] = actual_address
            logger.info("Non-DC ID - Using random DC address (actual address preserved)")
        
        elapsed = time.time() - request_start
        
        # Calculate age from DOB
        from datetime import datetime
        age = None
        try:
            dob = extracted_data.get('dateOfBirth', '')
            if dob:
                dob_date = datetime.strptime(dob, "%Y-%m-%d")
                today = datetime.today()
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        except Exception as e:
            logger.warning(f"Could not calculate age: {e}")
        
        logger.info(f"Barcode parsing completed in {elapsed:.3f}s")
        
        return jsonify({
            'success': True,
            'data': extracted_data,
            'isDC': is_dc,
            'processingTime': round(elapsed, 3),
            'age': age
        })
        
    except Exception as e:
        logger.error(f"Error parsing barcode: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to parse barcode data: {str(e)}'
        }), 500


@app.route('/api/debug-form', methods=['POST'])
def debug_form():
    """
    Debug endpoint - returns detailed logs without actually submitting
    """
    try:
        data = request.json
        
        # Validate data
        required_fields = ['firstName', 'lastName', 'dateOfBirth', 'street', 
                          'zip', 'phoneNumber', 'email', 'idImageBase64']
        missing = [f for f in required_fields if not data.get(f)]
        
        if missing:
            return jsonify({
                'success': False,
                'error': f'Missing fields: {", ".join(missing)}',
                'receivedData': {k: v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v 
                                for k, v in data.items() if k != 'idImageBase64'}
            }), 400
        
        # Test browser launch only
        try:
            QuickBaseFormAutomation = get_qb_automation_class()
            automation = QuickBaseFormAutomation(headless=True)
            return jsonify({
                'success': True,
                'message': 'Backend is configured correctly',
                'receivedData': {k: 'OK' for k in required_fields},
                'residentType': data.get('residentType', 'dc')
            }), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Browser initialization failed: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/submit-application', methods=['POST'])
def submit_application():
    """
    Submit application to QuickBase via browser automation
    
    Request body:
    {
        "firstName": "John",
        "middleInitial": "M",
        "lastName": "Doe",
        "suffix": "",
        "dateOfBirth": "1990-01-15",
        "street": "123 Main St NW",
        "aptSuite": "Apt 4B",
        "city": "Washington",
        "state": "DC",
        "zip": "20001",
        "phoneNumber": "(202) 555-0123",
        "email": "john.doe@example.com",
        "idImageBase64": "data:image/jpeg;base64,...",
        "residentType": "dc" or "nondc",
        "timePeriod": "30days" (optional, for Non-DC residents)
    }
    
    Response:
    {
        "success": true,
        "message": "Application form filled successfully",
        "formUrl": "https://octo.quickbase.com/db/bscn22va8?a=dbpage&pageid=23",
        "autoSubmit": false,
        "filledData": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "dob": "1990-01-15"
        }
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = [
            'firstName', 'lastName', 'dateOfBirth', 'street', 
            'zip', 'phoneNumber', 'email', 'idImageBase64'
        ]
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Get resident type (default to 'dc')
        resident_type = data.get('residentType', 'dc')
        if resident_type not in ['dc', 'nondc']:
            return jsonify({
                'success': False,
                'error': 'Invalid residentType. Must be "dc" or "nondc"'
            }), 400
        
        # For Non-DC residents, validate timePeriod
        if resident_type == 'nondc' and not data.get('timePeriod'):
            return jsonify({
                'success': False,
                'error': 'timePeriod is required for Non-DC residents'
            }), 400
        
        # Validate email format
        email = data.get('email', '')
        if '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Validate phone format (should be (XXX) XXX-XXXX)
        phone = data.get('phoneNumber', '')
        if len(phone.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')) != 10:
            return jsonify({
                'success': False,
                'error': 'Phone number must be 10 digits'
            }), 400
        
        # Submit via browser automation (auto_submit=True to submit the form)
        logger.info(f"Processing {resident_type.upper()} application for {data['firstName']} {data['lastName']}")
        result = get_qb_automation().submit_application(data, auto_submit=True, resident_type=resident_type)
        
        if result.get('success'):
            logger.info(f"{resident_type.upper()} application form filled successfully: {data['email']}")
            return jsonify(result), 200
        else:
            logger.error(f"Application submission failed: {result.get('error')}")
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to submit application: {str(e)}'
        }), 500


@app.route('/api/validate-age', methods=['POST'])
def validate_age():
    """
    Validate if applicant is eligible (21+) for self-certification
    
    Request body:
    {
        "dateOfBirth": "1990-01-15"
    }
    
    Response:
    {
        "success": true,
        "age": 33,
        "eligible": true,
        "message": "Applicant is eligible for self-certification"
    }
    """
    try:
        data = request.json
        dob = data.get('dateOfBirth', '')
        
        if not dob:
            return jsonify({
                'success': False,
                'error': 'Date of birth is required'
            }), 400
        
        from datetime import datetime
        
        try:
            # Support both YYYY-MM-DD and MM/DD/YYYY formats
            if '-' in dob:
                dob_date = datetime.strptime(dob, "%Y-%m-%d")
            else:
                dob_date = datetime.strptime(dob, "%m/%d/%Y")
            
            today = datetime.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            eligible = age >= 21
            
            if eligible:
                message = "Applicant is eligible for self-certification"
            else:
                message = f"Applicant must be 21+ for self-certification. Current age: {age}"
            
            return jsonify({
                'success': True,
                'age': age,
                'eligible': eligible,
                'message': message
            })
            
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY'
            }), 400
        
    except Exception as e:
        logger.error(f"Error validating age: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/')
def index():
    """Serve the frontend HTML"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static frontend files"""
    return send_from_directory(FRONTEND_DIR, path)


if __name__ == '__main__':
    import os
    PORT = int(os.environ.get('PORT', 5001))
    
    logger.info("=" * 60)
    logger.info("DC Medical Cannabis Application Server")
    logger.info("=" * 60)
    logger.info(f"Frontend: http://localhost:{PORT}")
    logger.info(f"Health Check: http://localhost:{PORT}/health")
    logger.info(f"Barcode API: http://localhost:{PORT}/api/scan-barcode")
    logger.info("=" * 60)
    
    # Production mode - use gunicorn in deployment
    # gunicorn -w 4 -b 0.0.0.0:5001 app:app
    app.run(host='0.0.0.0', port=PORT, debug=False)
