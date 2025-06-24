"""
Test suite for Google Sheets authentication module
"""
import os
import json
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError

# Import from parent directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.sheets_auth import SheetsAuthenticator, get_sheets_authenticator, get_sheets_service

@pytest.fixture
def mock_credentials_file():
    """Create a temporary mock credentials file"""
    credentials_data = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END PRIVATE KEY-----",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(credentials_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

@pytest.fixture
def mock_env_credentials(mock_credentials_file):
    """Set up environment variable for credentials"""
    original = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = mock_credentials_file
    
    yield mock_credentials_file
    
    # Restore original
    if original:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = original
    else:
        os.environ.pop('GOOGLE_APPLICATION_CREDENTIALS', None)

class TestSheetsAuthenticator:
    """Test cases for SheetsAuthenticator class"""
    
    def test_init_with_path(self, mock_credentials_file):
        """Test initialization with explicit credentials path"""
        auth = SheetsAuthenticator(credentials_path=mock_credentials_file)
        assert auth.credentials_path == mock_credentials_file
        assert auth._service is None
        assert auth._credentials is None
    
    def test_init_with_env_var(self, mock_env_credentials):
        """Test initialization using environment variable"""
        auth = SheetsAuthenticator()
        assert auth.credentials_path == mock_env_credentials
    
    def test_init_no_credentials(self):
        """Test initialization without credentials raises error"""
        # Ensure env var is not set
        os.environ.pop('GOOGLE_APPLICATION_CREDENTIALS', None)
        
        with pytest.raises(ValueError, match="No credentials path provided"):
            SheetsAuthenticator()
    
    def test_init_missing_file(self):
        """Test initialization with non-existent file"""
        with pytest.raises(FileNotFoundError, match="Credentials file not found"):
            SheetsAuthenticator(credentials_path="/non/existent/file.json")
    
    @patch('auth.sheets_auth.service_account.Credentials.from_service_account_info')
    def test_load_credentials_success(self, mock_from_service_account, mock_credentials_file):
        """Test successful credentials loading"""
        mock_creds = Mock()
        mock_from_service_account.return_value = mock_creds
        
        auth = SheetsAuthenticator(credentials_path=mock_credentials_file)
        auth._load_credentials()
        
        assert auth._credentials == mock_creds
        mock_from_service_account.assert_called_once()
        
        # Check scopes were set correctly
        call_args = mock_from_service_account.call_args
        assert call_args[1]['scopes'] == ['https://www.googleapis.com/auth/spreadsheets']
