"""
Test suite for Results API client module
"""
import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout

# Import from parent directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_clients.results_api import ResultsAPIClient, ResultsAPIError, get_results_api_client

@pytest.fixture
def mock_env_vars():
    """Set up environment variables for testing"""
    original_url = os.environ.get('RESULTS_API_URL')
    original_key = os.environ.get('RESULTS_API_KEY')
    
    os.environ['RESULTS_API_URL'] = 'https://api.example.com'
    os.environ['RESULTS_API_KEY'] = 'test-api-key-123'
    
    yield
    
    # Restore original values
    if original_url:
        os.environ['RESULTS_API_URL'] = original_url
    else:
        os.environ.pop('RESULTS_API_URL', None)
    
    if original_key:
        os.environ['RESULTS_API_KEY'] = original_key
    else:
        os.environ.pop('RESULTS_API_KEY', None)

class TestResultsAPIClient:
    """Test cases for ResultsAPIClient class"""
    
    def test_init_with_params(self):
        """Test initialization with explicit parameters"""
        client = ResultsAPIClient(
            api_url='https://test.api.com',
            api_key='test-key'
        )
        assert client.api_url == 'https://test.api.com/'
        assert client.api_key == 'test-key'
        assert 'Authorization' in client.session.headers
        assert client.session.headers['Authorization'] == 'Bearer test-key'
    
    def test_init_with_env_vars(self, mock_env_vars):
        """Test initialization using environment variables"""
        client = ResultsAPIClient()
        assert client.api_url == 'https://api.example.com/'
        assert client.api_key == 'test-api-key-123'
    
    def test_init_no_url(self):
        """Test initialization without API URL raises error"""
        os.environ.pop('RESULTS_API_URL', None)
        with pytest.raises(ValueError, match="No API URL provided"):
            ResultsAPIClient(api_key='test-key')
    
    def test_init_no_key(self):
        """Test initialization without API key raises error"""
        os.environ.pop('RESULTS_API_KEY', None)
        with pytest.raises(ValueError, match="No API key provided"):
            ResultsAPIClient(api_url='https://test.com')
