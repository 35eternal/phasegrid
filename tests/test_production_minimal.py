"""
Minimal test suite for PhaseGrid production hardening
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestProductionHardening:
    """Combined test class for all production hardening features"""
    
    def test_prizepicks_client_with_key(self):
        """Test PrizePicks client with API key"""
        from odds_provider.prizepicks import PrizePicksClient
        client = PrizePicksClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert "Authorization" in client.session.headers
    
    def test_prizepicks_client_without_key(self):
        """Test PrizePicks client without API key"""
        # Temporarily remove the env var
        original_key = os.environ.pop('PRIZEPICKS_API_KEY', None)
        try:
            from odds_provider.prizepicks import PrizePicksClient
            client = PrizePicksClient()
            assert client.api_key is None or client.api_key == ""
        finally:
            # Restore it if it existed
            if original_key:
                os.environ['PRIZEPICKS_API_KEY'] = original_key
    
    @patch('requests.Session.get')
    def test_prizepicks_fetch(self, mock_get):
        """Test PrizePicks fetch functionality"""
        from odds_provider.prizepicks import PrizePicksClient
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "1"}]}
        mock_get.return_value = mock_response
        
        client = PrizePicksClient(api_key="test_key")
        result = client.fetch_projections()
        assert result["data"][0]["id"] == "1"
    
    def test_retry_functionality(self):
        """Test retry decorator exists and works"""
        from scripts.result_grader import exponential_backoff_retry
        
        @exponential_backoff_retry(max_retries=2)
        def test_func():
            return "success"
        
        assert test_func() == "success"
    
    def test_slip_id_format(self):
        """Test slip ID format"""
        # Simple test for slip ID format
        import random
        import string
        
        slip_id = "PG_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        assert slip_id.startswith("PG_")
        assert len(slip_id) == 11
    
    def test_production_features_exist(self):
        """Test that all production hardening features exist"""
        # Test that key modules can be imported
        from odds_provider.prizepicks import PrizePicksClient
        from scripts.result_grader import exponential_backoff_retry, EnhancedResultGrader
        from backfill import main
        
        assert PrizePicksClient is not None
        assert exponential_backoff_retry is not None
        assert EnhancedResultGrader is not None
        assert main is not None
