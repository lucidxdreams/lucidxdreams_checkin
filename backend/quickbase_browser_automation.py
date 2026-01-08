"""
QuickBase Form Automation using Playwright
Handles form submission via browser automation
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from datetime import datetime
import os
import base64
import tempfile
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuickBaseFormAutomation:
    """Automates QuickBase medical cannabis application form submission"""
    
    DC_FORM_URL = "https://octo.quickbase.com/db/bscn22va8?a=dbpage&pageid=23"
    NONDC_FORM_URL = "https://octo.quickbase.com/db/bscn22va8?a=dbpage&pageID=39"
    SUCCESS_URL = "https://octo.quickbase.com/db/bscn22va8?a=dbpage&pageID=18"
    
    # Time period mapping for Non-DC residents
    TIME_PERIOD_MAP = {
        '3days': '3 days ($10)',
        '30days': '30 days ($20)',
        '90days': '90 days ($50)',
        '180days': '180 days ($75)',
        '365days': '365 days ($100)'
    }
    
    def __init__(self, headless: bool = True, slow_mo: int = 0):
        """
        Initialize browser automation
        
        Args:
            headless: Run browser in headless mode (no UI)
            slow_mo: Slow down operations by N milliseconds (useful for debugging)
        """
        self.headless = headless
        self.slow_mo = slow_mo
    
    def calculate_age(self, dob_str: str) -> int:
        """Calculate age from date of birth string (YYYY-MM-DD)"""
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except ValueError as e:
            logger.error(f"Invalid DOB format: {dob_str}. Expected YYYY-MM-DD")
            raise ValueError(f"Invalid date format: {dob_str}")
    
    def save_base64_to_temp_file(self, base64_data: str, filename: str = "temp_id.jpg") -> str:
        """
        Save base64 encoded image to temporary file
        
        Args:
            base64_data: Base64 encoded image (with or without data URI prefix)
            filename: Name for the temporary file
            
        Returns:
            Path to temporary file
        """
        # Remove data URI prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_data)
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        with open(temp_path, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Saved temporary file: {temp_path}")
        return temp_path
    
    def submit_application(self, application_data: Dict, auto_submit: bool = False, resident_type: str = 'dc') -> Dict:
        """
        Submit application to QuickBase form via browser automation
        
        Args:
            application_data: Dictionary containing:
                - firstName: str
                - middleInitial: str (optional)
                - lastName: str
                - suffix: str (optional)
                - dateOfBirth: str (YYYY-MM-DD format)
                - street: str
                - aptSuite: str (optional)
                - city: str (default: "Washington")
                - state: str (default: "DC")
                - zip: str
                - phoneNumber: str
                - email: str
                - idImageBase64: str (base64 encoded image)
                - timePeriod: str (optional, for Non-DC residents)
            resident_type: 'dc' or 'nondc'
            auto_submit: If True, submit the form automatically (default: False)
                
        Returns:
            Dictionary with success status and message
        """
        temp_file_path = None
        
        try:
            # Validate age (must be 21+ for self-certification)
            age = self.calculate_age(application_data['dateOfBirth'])
            if age < 21:
                return {
                    'success': False,
                    'error': f'Self-certification requires age 21+. Applicant age: {age}',
                    'age': age
                }
            
            # Save ID image to temporary file
            temp_file_path = self.save_base64_to_temp_file(
                application_data['idImageBase64'],
                f"id_{application_data['lastName']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            )
            
            # Launch browser
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Select appropriate form URL based on resident type
                form_url = self.DC_FORM_URL if resident_type == 'dc' else self.NONDC_FORM_URL
                logger.info(f"Navigating to {resident_type.upper()} form: {form_url}")
                page.goto(form_url, wait_until='networkidle', timeout=30000)
                
                # Wait for form to be ready
                page.wait_for_selector('form[name="qdbform"]', timeout=10000)
                logger.info("Form loaded successfully")
                
                # Fill Section 1: Patient Information
                logger.info("Filling patient information...")
                
                if resident_type == 'dc':
                    # DC Resident Form Fields
                    # Application Type
                    page.select_option('select[name="_fid_76"]', 'Initial')
                    
                    # Name fields
                    page.fill('input[name="_fid_6"]', application_data['firstName'])
                    if application_data.get('middleInitial'):
                        page.fill('input[name="_fid_7"]', application_data['middleInitial'][:1])
                    page.fill('input[name="_fid_8"]', application_data['lastName'])
                    if application_data.get('suffix'):
                        page.fill('input[name="_fid_35"]', application_data['suffix'])
                    
                    # DC DMV Real ID (set to "Yes" as requested)
                    page.select_option('select[name="_fid_122"]', 'Yes')
                    # Wait for QuickBase JavaScript to hide "Proof of Residency #1" and show "DC DMV Real ID" upload
                    page.wait_for_timeout(1500)
                    logger.info("DC DMV Real ID set to Yes, waiting for form update")
                    
                    # Date of Birth
                    page.fill('input[name="_fid_11"]', application_data['dateOfBirth'])
                    page.wait_for_timeout(500)
                    
                    # Address fields
                    page.fill('input[name="_fid_12"]', application_data['street'])
                    if application_data.get('aptSuite'):
                        page.fill('input[name="_fid_13"]', application_data['aptSuite'])
                    page.fill('input[name="_fid_14"]', application_data.get('city', 'Washington'))
                    page.select_option('select[name="_fid_15"]', application_data.get('state', 'DC'))
                    page.fill('input[name="_fid_16"]', application_data['zip'])
                    
                    # Contact information
                    page.fill('input[name="_fid_17"]', application_data['phoneNumber'])
                    page.fill('input[name="_fid_18"]', application_data['email'])
                    page.fill('input[name="_fid_117"]', application_data['email'])
                    
                    # Certification Type
                    try:
                        page.wait_for_selector('select[name="_fid_124"]', state='visible', timeout=2000)
                        page.select_option('select[name="_fid_124"]', 'Self certification')
                        # Wait for QuickBase JavaScript to hide recommendation fields (when self-cert is selected)
                        page.wait_for_timeout(1500)
                        logger.info("Self certification selected, waiting for form update")
                    except PlaywrightTimeout:
                        logger.warning("Certification type dropdown not visible")
                    
                    # Upload Government ID
                    page.set_input_files('input[name="_fid_50"]', temp_file_path)
                    logger.info("Government ID uploaded")
                    
                    # Upload DC DMV Real ID file
                    page.set_input_files('input[name="_fid_121"]', temp_file_path)
                    logger.info("DC DMV Real ID uploaded")
                    
                    # Reduced Fee (Always "No" as per user requirement)
                    try:
                        page.wait_for_selector('select.belowFPL', state='visible', timeout=2000)
                        page.select_option('select.belowFPL', 'No')
                        page.wait_for_timeout(500)
                        logger.info("Reduced fee set to 'No'")
                    except Exception as e:
                        logger.warning(f"Could not set reduced fee option: {e}")
                    
                else:
                    # Non-DC Resident Form Fields
                    logger.info("Filling Non-DC resident form...")
                    
                    # Time Period (required for Non-DC)
                    if application_data.get('timePeriod'):
                        time_period_value = self.TIME_PERIOD_MAP.get(application_data['timePeriod'], '30 days ($20)')
                        page.select_option('select[name="_fid_204"]', time_period_value)
                        logger.info(f"Time Period set to: {time_period_value}")
                    
                    # Name fields
                    page.fill('input[name="_fid_6"]', application_data['firstName'])
                    if application_data.get('middleInitial'):
                        page.fill('input[name="_fid_7"]', application_data['middleInitial'][:1])
                    page.fill('input[name="_fid_8"]', application_data['lastName'])
                    if application_data.get('suffix'):
                        page.fill('input[name="_fid_35"]', application_data['suffix'])
                    
                    # Date of Birth
                    page.fill('input[name="_fid_11"]', application_data['dateOfBirth'])
                    page.wait_for_timeout(500)
                    
                    # Address fields (from customer ID, not DC addresses)
                    page.fill('input[name="_fid_12"]', application_data['street'])
                    if application_data.get('aptSuite'):
                        page.fill('input[name="_fid_13"]', application_data['aptSuite'])
                    
                    # Country (default to United States)
                    page.select_option('select[name="_fid_175"]', 'United States of America')
                    
                    page.fill('input[name="_fid_14"]', application_data.get('city', ''))
                    page.select_option('select[name="_fid_15"]', application_data.get('state', ''))
                    page.fill('input[name="_fid_16"]', application_data['zip'])
                    
                    # Contact information (Phone is optional for Non-DC)
                    if application_data.get('phoneNumber'):
                        page.fill('input[name="_fid_17"]', application_data['phoneNumber'])
                    page.fill('input[name="_fid_18"]', application_data['email'])
                    page.fill('input[name="_fid_117"]', application_data['email'])
                    
                    # Upload Government ID
                    page.set_input_files('input[name="_fid_50"]', temp_file_path)
                    logger.info("Government ID uploaded for Non-DC resident")
                    
                    # Payment Method (Online only for Non-DC)
                    try:
                        page.select_option('select[name="_fid_120"]', 'Online')
                        logger.info("Payment method set to Online")
                    except Exception as e:
                        logger.warning(f"Could not set payment method: {e}")
                
                # Signature Section (Common for both)
                logger.info("Completing signature section...")
                
                # Check Terms & Conditions
                page.check('input[name="_fid_72"]')
                
                # Check Self Certification (if visible)
                try:
                    if page.is_visible('input[name="_fid_176"]'):
                        page.check('input[name="_fid_176"]')
                        logger.info("Self certification checkbox checked")
                except Exception as e:
                    logger.warning(f"Self certification checkbox not found: {e}")
                
                # Signature name
                signature_name = f"{application_data['firstName']} {application_data['lastName']}"
                page.fill('input[name="_fid_59"]', signature_name)
                
                # Date field
                date_value = page.input_value('input[name="_fid_60"]')
                if not date_value:
                    today = datetime.now().strftime("%Y-%m-%d")
                    page.evaluate(f'document.querySelector("input[name=\\"_fid_60\\"]").value = "{today}"')
                
                logger.info(f"{resident_type.upper()} form filled completely.")
                
                if auto_submit:
                    logger.info("Auto-submit enabled. Checking for validation errors...")
                    
                    # Wait for any client-side validation to complete
                    page.wait_for_timeout(2000)
                    
                    # Check for validation errors before submitting
                    error_messages = []
                    try:
                        errors = page.query_selector_all('.error, .validation-error, label.error, .errMsg')
                        for error in errors:
                            if error.is_visible():
                                error_text = error.inner_text()
                                if error_text and error_text.strip():
                                    error_messages.append(error_text)
                                    logger.warning(f"Validation error found: {error_text}")
                    except Exception as e:
                        logger.warning(f"Could not check for validation errors: {e}")
                    
                    if error_messages:
                        error_screenshot = f"validation_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        page.screenshot(path=error_screenshot)
                        browser.close()
                        return {
                            'success': False,
                            'error': 'Form has validation errors',
                            'errorMessages': error_messages,
                            'screenshot': error_screenshot
                        }
                    
                    logger.info("No validation errors found. Submitting form...")
                    
                    # Capture console errors
                    console_messages = []
                    page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
                    
                    # Check if submit button is enabled
                    submit_btn = page.query_selector('input[type="submit"]')
                    if submit_btn:
                        is_disabled = submit_btn.get_attribute('disabled')
                        if is_disabled:
                            logger.error("Submit button is disabled!")
                            return {
                                'success': False,
                                'error': 'Submit button is disabled - form may have validation errors'
                            }
                    
                    # Submit form
                    page.click('input[type="submit"]')
                    
                    # Wait for navigation with extended timeout
                    try:
                        # Wait for either success page or any navigation
                        page.wait_for_load_state('networkidle', timeout=60000)
                        page.wait_for_timeout(3000)
                        
                        current_url = page.url
                        logger.info(f"After submit, current URL: {current_url}")
                        
                        # Check for JavaScript alerts/popups
                        try:
                            alert_text = page.evaluate("() => window.alert && window.alert.toString()")
                            if alert_text:
                                logger.warning(f"Alert detected: {alert_text}")
                        except:
                            pass
                        
                        # Check if we're on the success page (pageID=18)
                        if 'pageID=18' in current_url or 'pageid=18' in current_url.lower():
                            logger.info(f"Successfully redirected to success page: {current_url}")
                            
                            success_result = {
                                'success': True,
                                'message': 'Application submitted successfully',
                                'redirectUrl': current_url,
                                'submittedData': {
                                    'name': signature_name,
                                    'email': application_data['email'],
                                    'dob': application_data['dateOfBirth']
                                }
                            }
                            
                            browser.close()
                            return success_result
                        else:
                            # Not on success page - check for errors
                            error_screenshot = f"submission_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            page.screenshot(path=error_screenshot)
                            
                            # Capture full page HTML for debugging
                            page_html = page.content()
                            html_dump = f"submission_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                            with open(html_dump, 'w', encoding='utf-8') as f:
                                f.write(page_html)
                            logger.info(f"Saved page HTML to {html_dump}")
                            
                            # Check for validation errors with multiple selectors
                            error_messages = []
                            try:
                                # QuickBase-specific error patterns
                                error_selectors = [
                                    '.error', '.validation-error', 'label.error', '.errMsg',
                                    '[class*="error"]', '[class*="Error"]', 
                                    'div[style*="color: red"]', 'span[style*="color: red"]',
                                    '.errormessage', '.error-message', '.field-error'
                                ]
                                
                                for selector in error_selectors:
                                    errors = page.query_selector_all(selector)
                                    for error in errors:
                                        if error.is_visible():
                                            error_text = error.inner_text()
                                            if error_text and error_text.strip() and error_text not in error_messages:
                                                error_messages.append(error_text)
                                                logger.warning(f"Error found with selector '{selector}': {error_text}")
                                
                                # Also check for any alerts or messages near the submit button
                                try:
                                    page_text = page.evaluate("() => document.body.innerText")
                                    if "required" in page_text.lower() or "invalid" in page_text.lower():
                                        logger.warning(f"Page contains 'required' or 'invalid' text")
                                except:
                                    pass
                                    
                            except Exception as e:
                                logger.error(f"Could not extract error messages: {e}")
                            
                            # Log console messages
                            if console_messages:
                                logger.error(f"Console messages during submission: {console_messages}")
                            
                            browser.close()
                            return {
                                'success': False,
                                'error': 'Form submission failed - did not redirect to success page',
                                'currentUrl': current_url,
                                'errorMessages': error_messages if error_messages else ['Unknown error - form did not submit'],
                                'consoleMessages': console_messages,
                                'screenshot': error_screenshot,
                                'htmlDump': html_dump
                            }
                        
                    except PlaywrightTimeout:
                        # Capture error state
                        error_screenshot = f"submission_timeout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        page.screenshot(path=error_screenshot)
                        
                        current_url = page.url
                        logger.error(f"Timeout waiting for form submission. Current URL: {current_url}")
                        
                        browser.close()
                        return {
                            'success': False,
                            'error': 'Form submission timeout - page did not respond',
                            'currentUrl': current_url,
                            'screenshot': error_screenshot
                        }
                else:
                    # Auto-submit disabled - form is filled but not submitted
                    logger.info("Auto-submit disabled. Form filled and ready for manual review.")
                    
                    # Take screenshot for verification
                    screenshot_path = f"form_filled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    page.screenshot(path=screenshot_path)
                    
                    # Keep browser open for manual review (only if not headless)
                    if not self.headless:
                        logger.info("Browser kept open for manual review. Close browser to continue.")
                        page.wait_for_timeout(300000)  # Wait 5 minutes for review
                    
                    browser.close()
                    return {
                        'success': True,
                        'message': 'Form filled successfully. Ready for manual review.',
                        'formUrl': page.url,
                        'screenshot': screenshot_path,
                        'autoSubmit': False,
                        'filledData': {
                            'name': signature_name,
                            'email': application_data['email'],
                            'dob': application_data['dateOfBirth']
                        }
                    }
        
        except Exception as e:
            logger.error(f"Automation error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Browser automation failed: {str(e)}'
            }
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete temporary file: {e}")


def test_automation():
    """Test function for development"""
    automation = QuickBaseFormAutomation(headless=False, slow_mo=100)
    
    # Sample test data
    test_data = {
        'firstName': 'John',
        'middleInitial': 'M',
        'lastName': 'Doe',
        'dateOfBirth': '1990-01-15',
        'street': '123 Main St NW',
        'aptSuite': 'Apt 4B',
        'city': 'Washington',
        'state': 'DC',
        'zip': '20001',
        'phoneNumber': '(202) 555-0123',
        'email': 'john.doe@example.com',
        'idImageBase64': 'data:image/jpeg;base64,/9j/4AAQSkZJRg...'  # Truncated
    }
    
    result = automation.submit_application(test_data)
    print(f"Result: {result}")


if __name__ == "__main__":
    test_automation()
