"""
Supabase client for storing customer data and ID images
"""
import os
import base64
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Manages Supabase database and storage operations"""
    
    def __init__(self):
        self.url = os.environ.get('SUPABASE_URL', '')
        self.key = os.environ.get('SUPABASE_SERVICE_KEY', '')
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials not configured - ID storage disabled")
            self.client = None
        else:
            try:
                self.client: Client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
    
    def is_configured(self) -> bool:
        """Check if Supabase is properly configured"""
        return self.client is not None
    
    def upload_id_image(self, image_base64: str, customer_id: int, side: str = 'front') -> Optional[str]:
        """
        Upload ID image to Supabase Storage
        
        Args:
            image_base64: Base64 encoded image data (with or without data URI prefix)
            customer_id: Customer database ID
            side: 'front' or 'back'
        
        Returns:
            Public URL of uploaded image or None if failed
        """
        if not self.is_configured():
            logger.warning("Supabase not configured - cannot upload image")
            return None
        
        try:
            # Remove data URI prefix if present
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            
            # Decode base64
            image_data = base64.b64decode(image_base64)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"customer_{customer_id}/{side}_{timestamp}.jpg"
            
            # Upload to storage
            response = self.client.storage.from_('customer-ids').upload(
                filename,
                image_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            if response:
                # Get public URL
                public_url = self.client.storage.from_('customer-ids').get_public_url(filename)
                logger.info(f"Uploaded {side} ID image: {filename}")
                return public_url
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to upload {side} ID image: {e}")
            return None
    
    def store_customer(self, customer_data: Dict) -> Optional[int]:
        """
        Store customer data in database
        
        Args:
            customer_data: Dictionary with customer information
        
        Returns:
            Customer ID if successful, None if failed
        """
        if not self.is_configured():
            logger.warning("Supabase not configured - cannot store customer")
            return None
        
        try:
            # Prepare data for insertion
            db_data = {
                'first_name': customer_data.get('firstName', ''),
                'last_name': customer_data.get('lastName', ''),
                'date_of_birth': customer_data.get('dateOfBirth'),
                'email': customer_data.get('email'),
                'phone': customer_data.get('phoneNumber'),
                'street_address': customer_data.get('street'),
                'city': customer_data.get('city', 'Washington'),
                'state': customer_data.get('state', 'DC'),
                'zip_code': customer_data.get('zip'),
                'resident_type': customer_data.get('residentType', 'dc'),
                'status': 'pending'
            }
            
            # Insert into database
            response = self.client.table('customers').insert(db_data).execute()
            
            if response.data and len(response.data) > 0:
                customer_id = response.data[0]['id']
                logger.info(f"Customer stored successfully: ID {customer_id}")
                return customer_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to store customer: {e}")
            return None
    
    def update_customer_images(self, customer_id: int, front_url: Optional[str], back_url: Optional[str]) -> bool:
        """
        Update customer record with ID image URLs
        
        Args:
            customer_id: Customer database ID
            front_url: URL to front of ID
            back_url: URL to back of ID
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            return False
        
        try:
            update_data = {}
            if front_url:
                update_data['id_front_url'] = front_url
            if back_url:
                update_data['id_back_url'] = back_url
            
            if not update_data:
                return True
            
            response = self.client.table('customers').update(update_data).eq('id', customer_id).execute()
            
            if response.data:
                logger.info(f"Updated customer {customer_id} with image URLs")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update customer images: {e}")
            return False
    
    def store_customer_with_images(
        self, 
        customer_data: Dict, 
        id_front_base64: str, 
        id_back_base64: Optional[str] = None
    ) -> Tuple[Optional[int], bool]:
        """
        Store customer data and ID images in one operation
        
        Args:
            customer_data: Customer information
            id_front_base64: Base64 encoded front of ID
            id_back_base64: Optional base64 encoded back of ID
        
        Returns:
            Tuple of (customer_id, success)
        """
        # Store customer data first
        customer_id = self.store_customer(customer_data)
        if not customer_id:
            return None, False
        
        # Upload ID images
        front_url = self.upload_id_image(id_front_base64, customer_id, 'front')
        back_url = None
        if id_back_base64:
            back_url = self.upload_id_image(id_back_base64, customer_id, 'back')
        
        # Update customer record with image URLs
        success = self.update_customer_images(customer_id, front_url, back_url)
        
        return customer_id, success
    
    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """
        Retrieve customer data by ID
        
        Args:
            customer_id: Customer database ID
        
        Returns:
            Customer data dictionary or None
        """
        if not self.is_configured():
            return None
        
        try:
            response = self.client.table('customers').select('*').eq('id', customer_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get customer: {e}")
            return None
    
    def list_customers(self, limit: int = 100, status: Optional[str] = None) -> list:
        """
        List customers with optional filtering
        
        Args:
            limit: Maximum number of customers to return
            status: Optional status filter ('pending', 'checked_in')
        
        Returns:
            List of customer dictionaries
        """
        if not self.is_configured():
            return []
        
        try:
            query = self.client.table('customers').select('*').order('created_at', desc=True).limit(limit)
            
            if status:
                query = query.eq('status', status)
            
            response = query.execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Failed to list customers: {e}")
            return []
