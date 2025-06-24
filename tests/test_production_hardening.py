"""
Comprehensive test suite for PhaseGrid production hardening
Run with: pytest tests/test_production_hardening.py -v
"""

import os
import sys
import json
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odds_provider.prizepicks import PrizePicksClient, exponential_backoff_retry
from auto_paper import EnhancedAutoPaper
from scripts.result_grader import EnhancedResultGrader
from backfill import HistoricalBackfill


# Test fixtures
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up test environment variables"""
    env_vars = {
        'SHEET_ID': 'test_sheet_123',
        'GOOGLE_SA_JSON': json.dumps({
            'type': 'service_account',
            'project_id': 'test-project',
            'private_key': 'test-key',
            'client_email': 'test@test.iam.gserviceaccount.com'
        }),
        'PRIZEPICKS_API_KEY': 'test_api_key',
        'RESULTS_API_URL': 'https://api.test.com/results',
        'RESULTS_API_KEY': 'test_results_key',
        'TWILIO_SID': 'test_sid',
        'TWILIO_AUTH': 'test_auth',
        'TWILIO_FROM': '+15551234567',
        'PHONE_TO': '+15559876543',
        'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/test',
        'RETRY_MAX': '3'
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def mock_sheets_service():
    """Mock Google Sheets service"""
    service = MagicMock()
    
    # Mock spreadsheets().values().get()
    service.spreadsheets().values().get().execute.return_value = {
        'values': [
            ['slip_id', 'date', 'player', 'prop_type', 'line', 'pick', 'graded', 'result'],
            ['PG_12345678', '2024-01-01', 'LeBron James', 'Points', '25.5', 'OVER', '', ''],
            ['PG_87654321', '2024-01-01', 'Stephen Curry', '3PT Made', '4.5', 'UNDER', '', '']
        ]
    }
    
    # Mock spreadsheets().values().append()
    service.spreadsheets().values().append().execute.return_value = {
        'updates': {'updatedCells': 16}
    }
    
    # Mock spreadsheets().values().batchUpdate()
    service.spreadsheets().values().batchUpdate().execute.return_value = {
        'totalUpdatedCells': 4
    }
    
    return service


# Test PrizePicks Client
class TestPrizePicksClient:
    """Test PrizePicks API client"""
    
    def test_client_initialization(self, mock_env_vars):
        """Test client initialization with API key"""
        client = PrizePicksClient()
        assert client.api_key == 'test_api_key'
        assert 'Authorization' in client.session.headers
        assert client.session.headers['Authorization'] == 'Bearer test_api_key'
    
    def test_client_without_api_key(self, monkeypatch):
        """Test client initialization without API key"""
        monkeypatch.delenv('PRIZEPICKS_API_KEY', raising=False)
        client = PrizePicksClient()
        assert client.api_key is None
        assert 'Authorization' not in client.session.headers
    
    @patch('requests.Session.get')
    def test_fetch_projections_success(self, mock_get, mock_env_vars):
        """Test successful projection fetching"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': '123',
                    'type': 'projection',
                    'attributes': {'line_score': 25.5, 'is_active': True}
                }
            ],
            'included': []
        }
        mock_get.return_value = mock_response
        
        client = PrizePicksClient()
        result = client.fetch_projections(league='NBA')
        
        assert 'data' in result
        assert len(result['data']) == 1
        mock_get.assert_called_once()


# Test Auto Paper
class TestEnhancedAutoPaper:
    """Test enhanced auto paper script"""
    
    @patch('google.oauth2.service_account.Credentials.from_service_account_info')
    @patch('googleapiclient.discovery.build')
    def test_initialization(self, mock_build, mock_creds, mock_env_vars):
        """Test auto paper initialization"""
        mock_build.return_value = MagicMock()
        
        auto_paper = EnhancedAutoPaper(sheet_id='test_sheet_123')
        auto_paper.initialize_sheets()
        
        assert auto_paper.sheet_id == 'test_sheet_123'
        assert auto_paper.dry_run is True
        assert auto_paper.sheet_service is not None
    
    def test_generate_slip_id(self, mock_env_vars):
        """Test slip ID generation"""
        auto_paper = EnhancedAutoPaper(sheet_id='test_sheet_123')
        
        slip_data = {
            'player': 'LeBron James',
            'prop_type': 'Points',
            'line': 25.5,
            'game_id': 'LAL_vs_BOS'
        }
        
        slip_id = auto_paper.generate_slip_id(slip_data)
        
        assert slip_id.startswith('PG_')
        assert len(slip_id) == 11  # PG_ + 8 hex chars
        
        # Same data should generate same ID
        slip_id2 = auto_paper.generate_slip_id(slip_data)
        assert slip_id == slip_id2


# Test Result Grader
class TestEnhancedResultGrader:
    """Test enhanced result grader"""
    
    @patch('google.oauth2.service_account.Credentials.from_service_account_info')
    @patch('googleapiclient.discovery.build')
    @patch('twilio.rest.Client')
    def test_initialization(self, mock_twilio, mock_build, mock_creds, mock_env_vars):
        """Test grader initialization"""
        mock_build.return_value = MagicMock()
        mock_twilio.return_value = MagicMock()
        
        grader = EnhancedResultGrader()
        grader.initialize()
        
        assert grader.sheet_service is not None
        assert grader.twilio_client is not None
    
    def test_grade_slip_player_prop(self, mock_env_vars):
        """Test grading player prop slips"""
        grader = EnhancedResultGrader()
        
        slip = {
            'slip_id': 'PG_12345678',
            'player': 'LeBron James',
            'prop_type': 'Points',
            'line': 25.5,
            'pick': 'OVER'
        }
        
        results = {
            'LeBron James_Points': {
                'actual_value': 28.0,
                'prop_type': 'Points',
                'player': 'LeBron James'
            }
        }
        
        grade, details, metadata = grader.grade_slip(slip, results)
        
        assert grade == 'WIN'
        assert '28.0 vs 25.5' in details
        assert metadata['actual_value'] == 28.0


# Test Backfill Script
class TestHistoricalBackfill:
    """Test historical backfill functionality"""
    
    @patch('auto_paper.EnhancedAutoPaper')
    @patch('scripts.result_grader.EnhancedResultGrader')
    def test_backfill_single_day(self, mock_grader_class, mock_paper_class, mock_env_vars):
        """Test backfilling a single day"""
        # Mock auto paper
        mock_paper = MagicMock()
        mock_paper.run.return_value = {
            'new_slips': 10,
            'total_slips': 10
        }
        mock_paper_class.return_value = mock_paper
        
        # Mock grader
        mock_grader = MagicMock()
        mock_grader.run.return_value = None
        mock_grader_class.return_value = mock_grader
        
        backfill = HistoricalBackfill(sheet_id='test_sheet_123')
        result = backfill.backfill_day('2024-01-01')
        
        assert result['date'] == '2024-01-01'
        assert result['slips_generated'] == 10
        assert result['slips_graded'] == 10
        assert len(result['errors']) == 0


# Test Retry Decorator
class TestRetryDecorator:
    """Test exponential backoff retry decorator"""
    
    def test_successful_call(self):
        """Test decorator with successful function call"""
        @exponential_backoff_retry(max_retries=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    @patch('time.sleep')
    def test_retry_on_failure(self, mock_sleep):
        """Test retry logic on failures"""
        call_count = 0
        
        @exponential_backoff_retry(max_retries=3, base_delay=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Test error")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert call_count == 3
        assert mock_sleep.call_count == 2  # Two retries


if __name__ == "__main__":
    pytest.main([__file__, '-v'])