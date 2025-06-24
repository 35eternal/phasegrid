"""
Google Sheets Authentication Module
Handles file-based authentication for Google Sheets API
"""
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class SheetsAuthenticator:
    """Handles authentication for Google Sheets API using service account credentials"""
    
    def __init__(self, credentials_path=None):
        """
        Initialize authenticator with service account credentials
        
        Args:
            credentials_path: Path to service account JSON file. 
                            Defaults to GOOGLE_APPLICATION_CREDENTIALS env var
        """
        self.credentials_path = credentials_path or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not self.credentials_path:
            raise ValueError("No credentials path provided. Set GOOGLE_APPLICATION_CREDENTIALS env var")
        
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
        
        self._service = None
        self._credentials = None
    
    def _load_credentials(self):
        """Load service account credentials from JSON file"""
        try:
            with open(self.credentials_path, 'r') as f:
                credentials_data = json.load(f)
            
            # Validate required fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in credentials_data]
            if missing_fields:
                raise ValueError(f"Missing required fields in credentials: {missing_fields}")
            
            # Fix potential padding issues with private key
            private_key = credentials_data.get('private_key', '')
            if private_key and not private_key.endswith('\n'):
                credentials_data['private_key'] = private_key + '\n'
            
            self._credentials = service_account.Credentials.from_service_account_info(
                credentials_data,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            logger.info("Successfully loaded service account credentials")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in credentials file: {e}")
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            raise
    
    def get_service(self):
        """Get authenticated Google Sheets service instance"""
        if not self._service:
            if not self._credentials:
                self._load_credentials()
            
            try:
                self._service = build('sheets', 'v4', credentials=self._credentials)
                logger.info("Successfully created Google Sheets service instance")
            except Exception as e:
                logger.error(f"Failed to create service: {e}")
                raise
        
        return self._service
    
    def test_connection(self, spreadsheet_id=None):
        """
        Test the connection to Google Sheets API
        
        Args:
            spreadsheet_id: Optional spreadsheet ID to test access
            
        Returns:
            bool: True if connection successful
        """
        try:
            service = self.get_service()
            
            if spreadsheet_id:
                # Try to get spreadsheet metadata
                result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                logger.info(f"Successfully accessed spreadsheet: {result.get('properties', {}).get('title')}")
            else:
                # Just verify service is working
                logger.info("Google Sheets service is operational")
            
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error testing connection: {e}")
            return False
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return False

# Singleton instance for application-wide use
_authenticator = None

def get_sheets_authenticator():
    """Get or create singleton authenticator instance"""
    global _authenticator
    if not _authenticator:
        _authenticator = SheetsAuthenticator()
    return _authenticator

def get_sheets_service():
    """Convenience function to get authenticated service"""
    return get_sheets_authenticator().get_service()
