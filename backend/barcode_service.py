"""
Barcode Scanner Service for Driver's License PDF417 Barcodes
Uses pdf417decoder (primary), zxing-cpp, and pyzbar for barcode detection
Parses AAMVA-compliant driver's license data
"""

import re
import base64
import io
import random
import json
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
from PIL import Image
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import barcode libraries - multiple engines for best results
# 1. pdf417decoder - specialized for PDF417 (driver's licenses)
try:
    from pdf417decoder import PDF417Decoder
    PDF417_AVAILABLE = True
    logger.info("pdf417decoder loaded successfully")
except Exception as e:
    PDF417_AVAILABLE = False
    logger.warning(f"pdf417decoder not available: {e}")

# 2. zxing-cpp - fast C++ library
try:
    import zxingcpp
    ZXING_AVAILABLE = True
    logger.info("zxing-cpp loaded successfully")
except Exception as e:
    ZXING_AVAILABLE = False
    logger.warning(f"zxing-cpp not available: {e}")

# 3. pyzbar - Python wrapper for ZBar
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
    logger.info("pyzbar loaded successfully")
except Exception as e:
    PYZBAR_AVAILABLE = False
    logger.warning(f"pyzbar not available: {e}")

# Load DC addresses for non-DC IDs
with open('dc_addresses.json', 'r') as f:
    DC_ADDRESSES = json.load(f)['addresses']


# AAMVA Field Mappings (based on AAMVA DL/ID Card Design Standard)
AAMVA_FIELDS = {
    # Name fields
    'DCS': 'lastName',
    'DCT': 'lastName',  # Some states use DCT
    'DAC': 'firstName',
    'DAD': 'middleName',
    'DBN': 'middleName',  # Alternate middle name field
    'DCU': 'suffix',
    
    # DOB and identifiers
    'DBB': 'dateOfBirth',  # MMDDYYYY
    'DAQ': 'licenseNumber',
    'DCF': 'documentNumber',
    'DCG': 'country',
    'DCH': 'federalCommercialVehicle',
    
    # Address fields
    'DAG': 'street',
    'DAH': 'street2',
    'DAI': 'city',
    'DAJ': 'state',
    'DAK': 'zip',
    'DCL': 'race',
    
    # Physical characteristics
    'DAY': 'eyeColor',
    'DAZ': 'hairColor',
    'DAU': 'height',
    'DAW': 'weight',
    'DBC': 'sex',
    
    # Dates
    'DBD': 'issueDate',
    'DBA': 'expirationDate',
    
    # Additional fields
    'DDD': 'endorsements',
    'DDE': 'restrictions',
    'DDK': 'organDonor',
    'DDL': 'veteran'
}


def process_barcode_image(image_base64: str) -> Image.Image:
    """
    Convert base64 image to PIL Image for barcode scanning
    """
    if ',' in image_base64:
        image_base64 = image_base64.split(',')[1]
    
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_bytes))
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Save debug image to see what we're working with
    # DISABLED for production/clean UX
    # try:
    #     import time
    #     import os
    #     debug_dir = os.path.join(os.path.dirname(__file__), 'debug_images')
    #     os.makedirs(debug_dir, exist_ok=True)
    #     debug_path = os.path.join(debug_dir, f'barcode_input_{int(time.time())}.jpg')
    #     image.save(debug_path, 'JPEG', quality=95)
    #     logger.info(f"Saved debug image ({image.size}) to {debug_path}")
    # except Exception as e:
    #     logger.debug(f"Could not save debug image: {e}")
            
    logger.info(f"Barcode image processed: {image.size}")
    return image


def preprocess_for_barcode(image: Image.Image) -> list:
    """
    Create multiple preprocessed versions of image for better barcode detection using OpenCV.
    PDF417 barcodes need good contrast and proper orientation.
    """
    import cv2
    import numpy as np
    
    variants = []
    
    # Convert PIL directly to OpenCV BGR
    # (PIL is RGB, OpenCV is BGR)
    pil_img = np.array(image)
    if len(pil_img.shape) < 3:
        pil_img = cv2.cvtColor(pil_img, cv2.COLOR_GRAY2BGR)
    else:
        pil_img = cv2.cvtColor(pil_img, cv2.COLOR_RGB2BGR)
        
    gray = cv2.cvtColor(pil_img, cv2.COLOR_BGR2GRAY)
    
    # Add raw grayscale variant (as Image object for zxing wrapper)
    variants.append((Image.fromarray(gray), "cv_gray"))
    
    # 1. Resize/Upscale Logic (Upscaling often helps small barcodes)
    # Check if image is too small for PDF417 details
    height, width = gray.shape
    if width < 1500:
        logger.info(f"Upscaling image from {width}x{height} to better detect PDF417")
        # Upscale 2x using Cubic interpolation
        upscaled = cv2.resize(gray, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
        variants.append((Image.fromarray(upscaled), "cv_upscaled_2x"))
        
        # Add a sharpened upscaled variant
        sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        upscaled_sharp = cv2.filter2D(upscaled, -1, sharpen_kernel)
        variants.append((Image.fromarray(upscaled_sharp), "cv_upscaled_sharp"))
        
        # Adaptive Threshold on Upscaled
        up_thresh = cv2.adaptiveThreshold(upscaled, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 21, 10)
        variants.append((Image.fromarray(up_thresh), "cv_upscaled_adaptive"))

    # 2. Gaussian Blur + Adaptive Threshold (The "Scanner App" look)
    # This is usually the best for documents with uneven lighting
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 21, 10)
    variants.append((Image.fromarray(thresh), "cv_adaptive_gauss"))

    # 3. Super High Contrast (CLAHE) - Contrast Limited Adaptive Histogram Equalization
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl1 = clahe.apply(gray)
    variants.append((Image.fromarray(cl1), "cv_clahe"))
    
    # 4. Standard Sharpening
    sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, sharpen_kernel)
    variants.append((Image.fromarray(sharpened), "cv_sharpened"))
    
    # 5. Dilation (to thicken bars if they are too thin/faded)
    kernel = np.ones((2,2), np.uint8) 
    dilated = cv2.erode(thresh, kernel, iterations=1) # Erode in CV is Dilation for black ink
    variants.append((Image.fromarray(dilated), "cv_dilated"))

    return variants


def decode_barcode_zxing(image: Image.Image) -> Optional[str]:
    """
    Decode PDF417 barcode using zxing-cpp with multiple preprocessing attempts.
    """
    if not ZXING_AVAILABLE:
        return None
        
    try:
        import time
        start_time = time.time()
        
        # Get preprocessed variants (Now returns PIL images)
        variants = preprocess_for_barcode(image)
        
        for img, variant_name in variants:
            try:
                # Try with different zxing options
                # zxing-cpp python usually accepts PIL Image directly
                results = zxingcpp.read_barcodes(img)
                
                if results:
                    for result in results:
                        barcode_text = result.text
                        if barcode_text and len(barcode_text) > 50:  # AAMVA barcodes are long
                            elapsed = time.time() - start_time
                            logger.info(f"✅ zxing-cpp decoded {result.format.name} via {variant_name} in {elapsed:.3f}s ({len(barcode_text)} chars)")
                            return barcode_text
                    
                    # Return first result even if short - sometimes it's split
                    elapsed = time.time() - start_time
                    logger.info(f"✅ zxing-cpp decoded {results[0].format.name} via {variant_name} in {elapsed:.3f}s")
                    return results[0].text
                    
            except Exception as e:
                # Fallback: Convert to numpy if PIL fails
                try:
                    results = zxingcpp.read_barcodes(np.array(img))
                    if results:
                        logger.info(f"✅ zxing-cpp decoded via {variant_name} (numpy fallback)")
                        return results[0].text
                except Exception:
                    logger.debug(f"zxing variant {variant_name} failed: {e}")
                continue
        
        elapsed = time.time() - start_time
        logger.warning(f"zxing-cpp found no barcodes after trying {len(variants)} variants in {elapsed:.3f}s")
        return None
            
    except Exception as e:
        logger.error(f"zxing-cpp decoding error: {e}")
        return None


def decode_barcode_pyzbar(image: Image.Image) -> Optional[str]:
    """
    Decode PDF417 barcode using pyzbar (fallback)
    """
    try:
        import time
        start_time = time.time()
        
        results = pyzbar.decode(image)
        
        elapsed = time.time() - start_time
        
        if results:
            for result in results:
                if result.type == 'PDF417':
                    barcode_text = result.data.decode('utf-8', errors='ignore')
                    logger.info(f"pyzbar decoded PDF417 barcode in {elapsed:.3f}s ({len(barcode_text)} chars)")
                    return barcode_text
            
            barcode_text = results[0].data.decode('utf-8', errors='ignore')
            logger.info(f"pyzbar decoded {results[0].type} barcode in {elapsed:.3f}s")
            return barcode_text
        else:
            logger.warning(f"pyzbar found no barcodes in {elapsed:.3f}s")
            return None
            
    except Exception as e:
        logger.error(f"pyzbar decoding error: {e}")
        return None


def decode_barcode(image: Image.Image) -> Tuple[Optional[str], str]:
    """
    Decode barcode using multiple engines in order of preference:
    1. zxing-cpp (fastest & most accurate with good image)
    2. pdf417decoder (specialized fallback)
    3. pyzbar (last resort)
    """
    # 1. Try zxing-cpp first (fast and accurate)
    if ZXING_AVAILABLE:
        barcode_text = decode_barcode_zxing(image)
        if barcode_text:
            return barcode_text, 'zxing-cpp'
        logger.info("zxing-cpp failed, trying pdf417decoder...")
    
    # 2. Try pdf417decoder (specialized for driver's license barcodes)
    if PDF417_AVAILABLE:
        barcode_text = decode_barcode_pdf417decoder(image)
        if barcode_text:
            return barcode_text, 'pdf417decoder'
        logger.info("pdf417decoder failed, trying pyzbar...")
    
    # 3. Fallback to pyzbar
    if PYZBAR_AVAILABLE:
        barcode_text = decode_barcode_pyzbar(image)
        if barcode_text:
            return barcode_text, 'pyzbar'
        logger.error("pyzbar also failed")
    
    return None, 'none'


def parse_aamva_barcode(barcode_text: str) -> Dict:
    """
    Parse AAMVA-compliant barcode data from driver's license
    
    AAMVA Format:
    @\n\x1e\rANSI 636049030002DL00410466ZN05070057DL...
    
    Args:
        barcode_text: Raw barcode text from PDF417
        
    Returns:
        Dictionary with parsed fields
    """
    logger.info(f"Parsing AAMVA barcode data ({len(barcode_text)} chars)")
    
    # Remove header garbage if present to find the "ANSI" marker
    # Many scanners start with compliance indicators like @
    
    # robust cleanup - keep alphanumeric and special chars used in IDs
    # But AAMVA relies on newlines (\n) or \r as delimiters sometimes.
    # We should be careful cleaning.
    
    clean_text = barcode_text
    
    parsed_data = {}
    
    # Direct Regex Strategy: Look for the specific field codes followed by data
    # Standard codes:
    # DCS: Last Name
    # DAC: First Name
    # DAD: Middle Name
    # DBB: DOB (MMDDYYYY)
    # DAG: Address
    # DAI: City
    # DAJ: State
    # DAK: Zip
    
    # We utilize a flexible regex that looks for the 3-letter code, 
    # and captures everything until the next likely 3-letter code (starts with D or Z usually)
    # or a newline/terminator.
    
def parse_aamva_barcode(barcode_text: str) -> Dict:
    """
    Parse AAMVA-compliant barcode data from driver's license
    
    AAMVA Format:
    @
    
    Args:
        barcode_text: Raw barcode text from PDF417
        
    Returns:
        Dictionary with parsed fields
    """
    logger.info(f"Parsing AAMVA barcode data ({len(barcode_text)} chars)")
    
    clean_text = barcode_text
    parsed_data = {}
    
    # List of known AAMVA Element IDs to use as delimiters
    # This prevents values like "David" (starts with Da) from being cut off,
    # because 'DAV' is not in this list, but 'Dad' (Middle Name) is.
    aamva_codes = [
        'DCA', 'DCB', 'DCD', 'DBA', 'DCS', 'DAC', 'DAD', 'DBD', 'DBB', 'DBC', 
        'DAY', 'DAU', 'DAG', 'DAI', 'DAJ', 'DAK', 'DAQ', 'DCF', 'DCG', 'DDE', 
        'DDF', 'DDG', 'DAH', 'DAZ', 'DCI', 'DCJ', 'DCM', 'DCN', 'DCO', 'DCP', 
        'DCQ', 'DCR', 'DDA', 'DDB', 'DDC', 'DDD', 'DAW', 'DAX', 'DCE', 'DCL', 
        'DAA', 'DAB', 'DAE', 'DAF', 'DAM', 'DAN', 'DAO', 'DAR', 'DAS', 'DAT',
        'Dbf', 'Dbg' # Some extra codes sometimes seen
    ]
    
    # Build lookahead pattern for ANY of these codes
    # (?=...) checks for presence without consuming
    # We match: Code + Value + (Lookahead for Next Code OR Terminator OR EndOfString)
    
    known_codes_pattern = '|'.join(aamva_codes)
    
    # Map of Code -> Field Name
    field_map = {
        'DCS': 'lastName',
        'DAC': 'firstName',
        'DAD': 'middleName',
        'DBB': 'dateOfBirth',
        'DAG': 'street',
        'DAH': 'street2',
        'DAI': 'city',
        'DAJ': 'state',
        'DAK': 'zip',
        'DAQ': 'licenseNumber',
        'DBC': 'sex',
        'DAY': 'eyeColor',
        'DAU': 'height'
    }
    
    # We iterate nicely through our expected fields
    for code, field in field_map.items():
        # Regex explanation:
        # {code}        : The specific field code we want (e.g. DAC)
        # \s*           : Optional whitespace
        # (.*?)         : Non-greedy capture of the value
        # (?=           : Positive lookahead (stop when we see...)
        #   [\n\r\x1e]  : A standard delimiter (newline, return, RS)
        #   |           : OR
        #   (?:...codes): Any valid AAMVA code (case insensitive due to re.I)
        #   |           : OR
        #   $           : End of string
        # )
        
        pattern = rf'({code})\s*(.*?)(?=[\n\r\x1e]|(?:{known_codes_pattern})|$)'
        
        # Use IGNORECASE to handle mixed case codes like 'Dac' or 'Dad' seen in wild
        match = re.search(pattern, clean_text, re.IGNORECASE)
            
        if match:
            value = match.group(2).strip()
            
            # Aggressively clean up:
            # 1. Remove literal "<Lf>" or "<LF>" or "<lf>"
            value = re.sub(r'<lf>', '', value, flags=re.IGNORECASE)
            # 2. Remove all control characters (non-printable) except space
            # \x00-\x1f are standard ASCII control chars
            value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
            
            value = value.strip()
            
            if value:
                parsed_data[field] = value
                logger.info(f"Found {field} ({code}): {value}")

    return parsed_data

def format_date(date_str: str, input_format: str = 'MMDDYYYY') -> str:
    """
    Convert date from AAMVA format to YYYY-MM-DD
    
    Args:
        date_str: Date string (e.g., "02121990" for Feb 12, 1990)
        input_format: Format of input date
        
    Returns:
        Date in YYYY-MM-DD format or empty string
    """
    try:
        # Some IDs have trailing data in date fields if parsing wasn't perfect,
        # try to substring logical lengths
        clean_date = date_str.strip()[:8]
        
        if input_format == 'MMDDYYYY' and len(clean_date) == 8:
            if clean_date.isdigit():
                month, day, year = clean_date[:2], clean_date[2:4], clean_date[4:]
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
        elif input_format == 'YYYYMMDD' and len(clean_date) == 8:
            if clean_date.isdigit():
                year, month, day = clean_date[:4], clean_date[4:6], clean_date[6:]
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
        
        logger.warning(f"Unrecognized date format: {date_str}")
        return date_str
    except Exception as e:
        logger.error(f"Date parsing error: {e}")
        return date_str


def detect_dc_from_barcode(parsed_data: Dict) -> bool:
    """
    Detect if ID is from DC based on parsed barcode data
    
    Args:
        parsed_data: Parsed AAMVA data
        
    Returns:
        True if DC ID, False otherwise
    """
    state = parsed_data.get('state', '').upper()
    city = parsed_data.get('city', '').upper()
    
    if state == 'DC':
        logger.info("DC ID detected: state field = DC")
        return True
    
    if 'WASHINGTON' in city and state in ['', 'DC']:
        logger.info("DC ID detected: Washington in city field")
        return True
    
    logger.info("Non-DC ID detected")
    return False


def get_random_dc_address() -> Dict[str, str]:
    """Get a random DC address for non-DC IDs"""
    address = random.choice(DC_ADDRESSES)
    logger.info(f"Assigned random DC address: {address['street']}")
    return address


def extract_id_from_barcode(image_base64: str) -> Dict:
    """
    Extract ID data from driver's license barcode (PDF417)
    
    Args:
        image_base64: Base64 encoded image of ID barcode
        
    Returns:
        Dictionary with success status and extracted data
    """
    try:
        import time
        start_time = time.time()
        
        logger.info("=" * 60)
        logger.info("Starting barcode extraction...")
        
        # Process image
        image = process_barcode_image(image_base64)
        
        # Decode barcode
        barcode_text, engine = decode_barcode(image)
        
        if not barcode_text:
            return {
                'success': False,
                'error': 'No barcode detected. Please ensure the barcode on the back of the ID is visible and in focus.'
            }
        
        logger.info(f"Barcode decoded using {engine}")
        logger.info(f"Raw barcode text preview: {barcode_text[:100]}...")
        
        # Parse AAMVA data
        parsed_data = parse_aamva_barcode(barcode_text)
        
        if not parsed_data:
            return {
                'success': False,
                'error': 'Failed to parse barcode data. The barcode may be damaged or not AAMVA-compliant.'
            }
        
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
            actual_address['zip'] = parsed_data['zip'][:5]  # First 5 digits only
        
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
        
        elapsed = time.time() - start_time
        logger.info(f"Barcode extraction completed in {elapsed:.3f}s")
        logger.info(f"Extracted fields: {list(extracted_data.keys())}")
        logger.info("=" * 60)
        
        return {
            'success': True,
            'data': extracted_data,
            'isDC': is_dc,
            'scanEngine': engine,
            'processingTime': round(elapsed, 3)
        }
        
    except Exception as e:
        logger.error(f"Barcode extraction error: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f'Failed to extract barcode data: {str(e)}'
        }
