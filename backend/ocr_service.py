"""
OCR Service for ID extraction with DC vs Non-DC detection
Uses Surya OCR (primary) and PaddleOCR (backup) for text extraction
"""

import re
import os
import json
import random
import base64
import io
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
import logging
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OCR engines
try:
    from surya.ocr import run_ocr
    from surya.model.detection.segformer import load_model as load_det_model, load_processor as load_det_processor
    from surya.model.recognition.model import load_model as load_rec_model
    from surya.model.recognition.processor import load_processor as load_rec_processor
    SURYA_AVAILABLE = True
    logger.info("Surya OCR loaded successfully")
except Exception as e:
    SURYA_AVAILABLE = False
    logger.warning(f"Surya OCR not available: {e}")

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
    logger.info("PaddleOCR loaded successfully")
except Exception as e:
    PADDLE_AVAILABLE = False
    logger.warning(f"PaddleOCR not available: {e}")

# Load DC addresses (use absolute path for production compatibility)
_dc_addresses_path = os.path.join(os.path.dirname(__file__), 'dc_addresses.json')
with open(_dc_addresses_path, 'r') as f:
    DC_ADDRESSES = json.load(f)['addresses']

# Initialize OCR engines (lazy loading)
_surya_models = None
_paddle_ocr = None


def get_surya_models():
    """Lazy load Surya models"""
    global _surya_models
    if _surya_models is None and SURYA_AVAILABLE:
        try:
            logger.info("Loading Surya models...")
            det_model = load_det_model()
            det_processor = load_det_processor()
            rec_model = load_rec_model()
            rec_processor = load_rec_processor()
            _surya_models = {
                'det_model': det_model,
                'det_processor': det_processor,
                'rec_model': rec_model,
                'rec_processor': rec_processor
            }
            logger.info("Surya models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Surya models: {e}")
            return None
    return _surya_models


def get_paddle_ocr():
    """Lazy load PaddleOCR with simple config"""
    global _paddle_ocr
    if _paddle_ocr is None and PADDLE_AVAILABLE:
        try:
            import os
            # Enable verbose logging from PaddleOCR for debugging
            # os.environ['PADDLEOCR_LOG_LEVEL'] = 'ERROR'
            
            logger.info("Loading PaddleOCR...")
            # Updated config for PaddleOCR 2.8+ (show_log removed)
            _paddle_ocr = PaddleOCR(
                use_angle_cls=True,  # Enable angle classification for rotated IDs
                lang='en'
            )
            logger.info("PaddleOCR loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load PaddleOCR: {e}")
            return None
    return _paddle_ocr


def process_image(image_base64: str) -> Image.Image:
    """
    Convert base64 image to PIL Image with optimization
    
    Args:
        image_base64: Base64 encoded image (with or without data URI prefix)
        
    Returns:
        Optimized PIL Image object
    """
    # Remove data URI prefix if present
    if ',' in image_base64:
        image_base64 = image_base64.split(',')[1]
    
    # Decode base64 to bytes
    image_bytes = base64.b64decode(image_base64)
    
    # Open image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Handle EXIF orientation
    try:
        from PIL import ImageOps
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass
    
    # Optimize: Resize very large images, but keep high resolution for OCR
    # IDs need good resolution, so we bump limit to 2500
    MAX_WIDTH = 2500
    MAX_HEIGHT = 2500
    
    if image.width > MAX_WIDTH or image.height > MAX_HEIGHT:
        # Calculate resize ratio maintaining aspect ratio
        ratio = min(MAX_WIDTH / image.width, MAX_HEIGHT / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        logger.info(f"Resizing image from {image.size} to {new_size} for OCR")
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    return image


def extract_text_surya(image: Image.Image) -> Tuple[str, float]:
    """
    Extract text from image using Surya OCR
    
    Args:
        image: PIL Image object
        
    Returns:
        Tuple of (extracted text, confidence score)
    """
    try:
        models = get_surya_models()
        if models is None:
            raise Exception("Surya models not available")
        
        logger.info("Running Surya OCR...")
        
        # Run OCR
        predictions = run_ocr(
            [image],
            [['en']],
            models['det_model'],
            models['det_processor'],
            models['rec_model'],
            models['rec_processor']
        )
        
        # Extract text and confidence
        if predictions and len(predictions) > 0:
            result = predictions[0]
            text_lines = []
            confidences = []
            
            for text_line in result.text_lines:
                text_lines.append(text_line.text)
                confidences.append(text_line.confidence)
            
            combined_text = '\n'.join(text_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"Surya OCR extracted {len(combined_text)} characters with confidence {avg_confidence:.2f}")
            return combined_text, avg_confidence
        else:
            return "", 0.0
            
    except Exception as e:
        logger.error(f"Surya OCR error: {e}")
        raise


def extract_text_paddle_single(paddle_ocr, img_array) -> Tuple[str, float]:
    """Helper to run paddle on a single image array"""
    try:
        # Debug: Log array properties
        if hasattr(img_array, 'shape'):
             logger.info(f"PaddleOCR Input: shape={img_array.shape}, dtype={img_array.dtype}")
             
        # Convert RGB to BGR (Paddle uses OpenCV which expects BGR)
        # Assuming input is RGB from PIL
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_bgr = img_array[..., ::-1]
        else:
            img_bgr = img_array

        # Enable angle classification (cls=True) to handle rotated IDs
        # Pass BGR image. Note: cls=True is handled by constructor arg use_angle_cls=True
        result = paddle_ocr.ocr(img_bgr)
        
        # Log absolute raw result
        logger.info(f"PaddleOCR RAW OUTPUT: {result}")
        
        text_lines = []
        confidences = []
        
        if result and result[0]:
            logger.info(f"Processable Result Items: {len(result[0])}")
            for line in result[0]:
                if line and len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, tuple) and len(text_info) >= 2:
                        text_lines.append(text_info[0])
                        confidences.append(text_info[1])
                    elif isinstance(text_info, str):
                        text_lines.append(text_info)
                        confidences.append(1.0)
        
        if text_lines:
            combined_text = '\n'.join(text_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return combined_text, avg_confidence
        return "", 0.0
    except Exception:
        return "", 0.0

def save_debug_image(image: Image.Image, name: str):
    """Save debug image to disk"""
    try:
        debug_dir = os.path.join(os.path.dirname(__file__), 'debug_output')
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        filepath = os.path.join(debug_dir, f"ocr_debug_{timestamp}_{name}.jpg")
        image.save(filepath)
        logger.info(f"Saved debug image: {filepath}")
    except Exception as e:
        logger.warning(f"Failed to save debug image: {e}")

def extract_text_paddle(image: Image.Image) -> Tuple[str, float]:
    """
    Extract text from image using PaddleOCR with retries on preprocessed versions
    """
    try:
        import time
        from PIL import ImageEnhance, ImageOps
        start_time = time.time()
        
        paddle_ocr = get_paddle_ocr()
        if paddle_ocr is None:
            raise Exception("PaddleOCR not available")
        
        logger.info(f"Running PaddleOCR on {image.size} image...")
        save_debug_image(image, "original")
        
        # 1. Try original image
        # PaddleOCR expects RGB or BGR. PIL is RGB.
        text, conf = extract_text_paddle_single(paddle_ocr, np.array(image))
        
        # If good result, return immediately
        if len(text.strip()) > 20:  # Arbitrary threshold for "good enough"
            elapsed = time.time() - start_time
            logger.info(f"PaddleOCR success on original image in {elapsed:.2f}s")
            return text, conf
            
        logger.info(f"PaddleOCR original result weak ({len(text)} chars), trying variants...")
        
        # Prepare variants
        variants = []
        
        # Grayscale
        gray = image.convert('L')
        variants.append((np.array(gray), "grayscale"))
        save_debug_image(gray, "grayscale")
        
        # High Contrast
        enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
        variants.append((np.array(enhanced), "high_contrast"))
        save_debug_image(enhanced, "high_contrast")
        
        # Thresholding (Binarization)
        thresh = gray.point(lambda x: 255 if x > 128 else 0, mode='1')
        variants.append((np.array(thresh.convert('L')), "binary"))
        save_debug_image(thresh, "binary")
        
        best_text = text
        best_conf = conf
        
        for img_array, name in variants:
            var_text, var_conf = extract_text_paddle_single(paddle_ocr, img_array)
            logger.info(f"PaddleOCR variant {name}: {len(var_text)} chars, conf {var_conf:.2f}")
            
            if len(var_text) > len(best_text):
                best_text = var_text
                best_conf = var_conf
                
            if len(best_text.strip()) > 50:
                break
        
        elapsed = time.time() - start_time
        logger.info(f"PaddleOCR final result: {len(best_text)} chars in {elapsed:.2f}s")
        return best_text, best_conf
            
    except Exception as e:
        logger.error(f"PaddleOCR error: {e}")
        raise


def extract_text_from_image(image: Image.Image) -> Tuple[str, float, str]:
    """
    Extract text from image using Surya (primary) with PaddleOCR fallback
    
    Args:
        image: PIL Image object
        
    Returns:
        Tuple of (extracted text, confidence score, engine used)
    """
    surya_text = ""
    paddle_text = ""
    
    # Try Surya first
    if SURYA_AVAILABLE:
        try:
            text, confidence = extract_text_surya(image)
            surya_text = text
            logger.info(f"Surya extracted {len(text)} chars: '{text[:200]}'...")
            if text and len(text.strip()) > 10:
                return text, confidence, 'surya'
            logger.warning(f"Surya OCR returned insufficient text (only {len(text.strip())} chars), trying PaddleOCR...")
        except Exception as e:
            logger.error(f"Surya OCR failed: {e}, trying PaddleOCR...")
    else:
        logger.warning("Surya not available")
    
    # Fallback to PaddleOCR
    if PADDLE_AVAILABLE:
        try:
            text, confidence = extract_text_paddle(image)
            paddle_text = text
            logger.info(f"PaddleOCR extracted {len(text)} chars: '{text[:200]}'...")
            if text and len(text.strip()) > 10:
                return text, confidence, 'paddle'
            logger.error(f"PaddleOCR also returned insufficient text (only {len(text.strip())} chars)")
        except Exception as e:
            logger.error(f"PaddleOCR also failed: {e}")
    else:
        logger.warning("PaddleOCR not available")
    
    # Provide detailed error message
    error_details = f"Surya: {len(surya_text)} chars, PaddleOCR: {len(paddle_text)} chars"
    logger.error(f"Both OCR engines failed. {error_details}")
    raise Exception(f"Both OCR engines failed to extract sufficient text. {error_details}")


def detect_dc_id(text: str) -> bool:
    """
    Detect if ID is from DC based on OCR text
    
    Args:
        text: Raw OCR text from ID
        
    Returns:
        True if DC ID, False otherwise
    """
    text_upper = text.upper()
    
    # DC indicators
    dc_indicators = [
        'DISTRICT OF COLUMBIA',
        'DISTRICT COLUMBIA',
        'WASHINGTON DC',
        'WASHINGTON, DC',
        'WASH DC',
        'DC DMV',
        'DEPARTMENT OF MOTOR VEHICLES',
        'DRIVER LICENSE',
        'DRIVER\'S LICENSE',
    ]
    
    # Check for DC indicators
    for indicator in dc_indicators:
        if indicator in text_upper:
            logger.info(f"DC ID detected: Found '{indicator}'")
            return True
    
    # Check for DC in address section
    if re.search(r'\bDC\b.*?\d{5}', text_upper):
        logger.info("DC ID detected: Found DC with ZIP code")
        return True
    
    logger.info("Non-DC ID detected")
    return False


def get_random_dc_address() -> Dict[str, str]:
    """
    Get a random DC address from the database
    
    Returns:
        Dictionary with address fields
    """
    address = random.choice(DC_ADDRESSES)
    logger.info(f"Assigned random DC address: {address['street']}")
    return address


def extract_name(text: str) -> Dict[str, str]:
    """
    Extract name from OCR text with multiple pattern matching
    
    Returns:
        Dictionary with firstName, middleInitial, lastName, suffix
    """
    result = {
        'firstName': '',
        'middleInitial': '',
        'lastName': '',
        'suffix': ''
    }
    
    # Pattern 1: "LN LASTNAME FN FIRSTNAME" or "LN: LASTNAME FN: FIRSTNAME"
    pattern1 = re.search(r'LN[:\s]+([A-Z][A-Za-z]+)[,\s]+FN[:\s]+([A-Z][A-Za-z]+)', text, re.IGNORECASE)
    if pattern1:
        result['lastName'] = pattern1.group(1).strip().title()
        result['firstName'] = pattern1.group(2).strip().title()
        logger.info(f"Name extracted (Pattern 1): {result['firstName']} {result['lastName']}")
        return result
    
    # Pattern 2: "LASTNAME, FIRSTNAME" (all caps)
    pattern2 = re.search(r'\b([A-Z]{2,})[,\s]+([A-Z]{2,})\b', text)
    if pattern2:
        result['lastName'] = pattern2.group(1).strip().title()
        result['firstName'] = pattern2.group(2).strip().title()
        logger.info(f"Name extracted (Pattern 2): {result['firstName']} {result['lastName']}")
        return result
    
    # Pattern 3: "FirstName LastName" (Title case after keywords like "Name:", "DL Name", etc.)
    pattern3 = re.search(r'(?:Name|DL\s*Name|Full\s*Name)[:\s]+([A-Z][a-z]+)\s+([A-Z][a-z]+)', text, re.IGNORECASE)
    if pattern3:
        result['firstName'] = pattern3.group(1).strip().title()
        result['lastName'] = pattern3.group(2).strip().title()
        logger.info(f"Name extracted (Pattern 3): {result['firstName']} {result['lastName']}")
        return result
    
    # Pattern 4: Search for two consecutive capitalized words (fallback)
    lines = text.split('\n')
    for line in lines:
        words = re.findall(r'\b[A-Z][a-z]{1,}\b', line)
        if len(words) >= 2:
            # Skip common words
            skip_words = {'Date', 'Birth', 'License', 'Driver', 'Drivers', 'Class', 'Sex', 'Height', 
                         'Eyes', 'Hair', 'Address', 'City', 'State', 'Zip', 'Issue', 'Expires', 
                         'Endorsements', 'Restrictions', 'District', 'Columbia', 'Washington'}
            
            filtered_words = [w for w in words if w not in skip_words]
            if len(filtered_words) >= 2:
                result['firstName'] = filtered_words[0]
                result['lastName'] = filtered_words[1]
                logger.info(f"Name extracted (Pattern 4): {result['firstName']} {result['lastName']}")
                return result
    
    logger.warning("Could not extract name from OCR text")
    return result


def extract_dob(text: str) -> str:
    """
    Extract date of birth from OCR text with multiple pattern matching
    
    Returns:
        Date in YYYY-MM-DD format, or empty string
    """
    # Pattern 1: DOB: MM/DD/YYYY or DOB MM/DD/YYYY
    pattern1 = re.search(r'DOB[:\s]*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text, re.IGNORECASE)
    if pattern1:
        month, day, year = pattern1.groups()
        try:
            datetime(int(year), int(month), int(day))
            dob = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            logger.info(f"DOB extracted (Pattern 1): {dob}")
            return dob
        except ValueError:
            pass
    
    # Pattern 2: Birth: MM/DD/YYYY or Birth MM/DD/YYYY
    pattern2 = re.search(r'Birth[:\s]*(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text, re.IGNORECASE)
    if pattern2:
        month, day, year = pattern2.groups()
        try:
            datetime(int(year), int(month), int(day))
            dob = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            logger.info(f"DOB extracted (Pattern 2): {dob}")
            return dob
        except ValueError:
            pass
    
    # Pattern 3: Standalone date MM/DD/YYYY (with validation)
    pattern3 = re.findall(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', text)
    for match in pattern3:
        month, day, year = match
        try:
            # Validate it's a reasonable birth date (between 1920 and 2010)
            year_int = int(year)
            if 1920 <= year_int <= 2010:
                datetime(year_int, int(month), int(day))
                dob = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                logger.info(f"DOB extracted (Pattern 3): {dob}")
                return dob
        except ValueError:
            continue
    
    # Pattern 4: MMDDYYYY format (8 consecutive digits)
    pattern4 = re.findall(r'\b(\d{2})(\d{2})(\d{4})\b', text)
    for match in pattern4:
        month, day, year = match
        try:
            year_int = int(year)
            if 1920 <= year_int <= 2010:
                datetime(year_int, int(month), int(day))
                dob = f"{year}-{month}-{day}"
                logger.info(f"DOB extracted (Pattern 4): {dob}")
                return dob
        except ValueError:
            continue
    
    logger.warning("Could not extract DOB from OCR text")
    return ''


def extract_address(text: str) -> Dict[str, str]:
    """
    Extract address from OCR text (for DC IDs only)
    
    Returns:
        Dictionary with street, aptSuite, city, state, zip
    """
    result = {
        'street': '',
        'aptSuite': '',
        'city': 'Washington',
        'state': 'DC',
        'zip': ''
    }
    
    # Extract ZIP code (5 digits, possibly followed by -XXXX)
    zip_matches = re.findall(r'\b(\d{5})(?:-\d{4})?\b', text)
    # DC ZIP codes start with 200 or 204
    for zip_code in zip_matches:
        if zip_code.startswith('200') or zip_code.startswith('204'):
            result['zip'] = zip_code
            logger.info(f"ZIP extracted: {zip_code}")
            break
    
    # Extract street address (number + street name + street type)
    street_types = r'(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl|Terrace|Ter|Court|Ct|Circle|Cir)'
    street_match = re.search(
        rf'(\d+\s+[A-Za-z\s]+\s*{street_types}\.?\s*(?:NW|NE|SW|SE)?)',
        text,
        re.IGNORECASE
    )
    if street_match:
        result['street'] = street_match.group(1).strip()
        logger.info(f"Street extracted: {result['street']}")
    
    # Extract apartment/suite
    apt_match = re.search(r'(?:Apt|Apartment|Suite|Unit|#)\s*([A-Z0-9]+)', text, re.IGNORECASE)
    if apt_match:
        result['aptSuite'] = f"Apt {apt_match.group(1)}"
        logger.info(f"Apt/Suite extracted: {result['aptSuite']}")
    
    return result


def extract_id_data(image_base64: str) -> Dict:
    """
    Extract data from ID image using Surya OCR (primary) and PaddleOCR (backup)
    
    Args:
        image_base64: Base64 encoded image
        
    Returns:
        Dictionary with success status and extracted data
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting OCR extraction...")
        
        # Process image
        image = process_image(image_base64)
        logger.info(f"Image processed: {image.size}")
        
        # Extract text using Surya or PaddleOCR
        text, confidence, engine = extract_text_from_image(image)
        
        logger.info(f"OCR Engine: {engine}")
        logger.info(f"OCR Confidence: {confidence:.2%}")
        logger.info(f"OCR text extracted ({len(text)} chars):\n{text}")
        logger.info("=" * 60)
        
        if not text or len(text.strip()) < 10:
            return {
                'success': False,
                'error': 'Could not extract sufficient text from image. Please ensure the ID is clear, well-lit, and in focus.'
            }
        
        # Detect if DC ID
        is_dc = detect_dc_id(text)
        
        # Extract name (always extracted)
        name_data = extract_name(text)
        
        # Extract DOB (always extracted)
        dob = extract_dob(text)
        
        # Extract address based on ID type
        if is_dc:
            # DC ID: Extract actual address
            address_data = extract_address(text)
            logger.info(f"DC ID - Address extracted: {address_data}")
        else:
            # Non-DC ID: Use random DC address
            address_data = get_random_dc_address()
            logger.info(f"Non-DC ID - Random DC address assigned")
        
        # Combine all data
        extracted_data = {
            **name_data,
            'dateOfBirth': dob,
            **address_data
        }
        
        # Remove empty fields
        extracted_data = {k: v for k, v in extracted_data.items() if v}
        
        # Calculate confidence based on fields extracted and OCR confidence
        required_fields = ['firstName', 'lastName', 'dateOfBirth', 'street', 'city', 'state', 'zip']
        filled_required = sum(1 for f in required_fields if extracted_data.get(f))
        field_confidence = filled_required / len(required_fields)
        
        # Combined confidence (70% OCR confidence + 30% field extraction)
        final_confidence = (confidence * 0.7) + (field_confidence * 0.3)
        
        logger.info(f"Extraction complete: {filled_required}/{len(required_fields)} required fields extracted")
        logger.info(f"Final confidence: {final_confidence:.2%}")
        
        return {
            'success': True,
            'data': extracted_data,
            'isDC': is_dc,
            'confidence': round(final_confidence, 2),
            'ocrEngine': engine
        }
        
    except Exception as e:
        logger.error(f"OCR extraction error: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f'Failed to extract ID data: {str(e)}'
        }
