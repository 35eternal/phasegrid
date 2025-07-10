"""Tests for sheets_integration module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os
from sheets_integration import push_slips_to_sheets, get_sheets_service, Slip


class TestSheetsIntegration:
    """Test cases for sheets integration."""
    
    @patch('sheets_integration.build')
    @patch('sheets_integration.service_account.Credentials.from_service_account_info')
    @patch.dict(os.environ, {'GOOGLE_SA_JSON': '{"type": "service_account", "project_id": "test"}'})
    def test_get_sheets_service_with_env_var(self, mock_creds, mock_build):
        """Test service creation with environment variable."""
        mock_creds.return_value = Mock()
        mock_build.return_value = Mock()
        
        service = get_sheets_service()
        
        assert service is not None
        mock_creds.assert_called_once()
        mock_build.assert_called_once_with('sheets', 'v4', credentials=mock_creds.return_value)
    
    @patch('sheets_integration.build')
    @patch('sheets_integration.service_account.Credentials.from_service_account_info')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    @patch.dict(os.environ, {}, clear=True)
    def test_get_sheets_service_with_file(self, mock_exists, mock_open, mock_creds, mock_build):
        """Test service creation with file."""
        # Remove GOOGLE_SA_JSON from environment
        if 'GOOGLE_SA_JSON' in os.environ:
            del os.environ['GOOGLE_SA_JSON']
            
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = '{"type": "service_account"}'
        mock_creds.return_value = Mock()
        mock_build.return_value = Mock()
        
        service = get_sheets_service()
        
        assert service is not None
        mock_creds.assert_called_once()
        mock_build.assert_called_once()
    
    @patch('sheets_integration.get_sheets_service')
    def test_push_slips_to_sheets_success(self, mock_get_service):
        """Test successful push to sheets."""
        # Mock the service and its methods
        mock_service = Mock()
        mock_sheets = Mock()
        mock_values = Mock()
        mock_append = Mock()
        
        mock_service.spreadsheets.return_value = mock_sheets
        mock_sheets.values.return_value = mock_values
        mock_values.append.return_value = mock_append
        mock_append.execute.return_value = {
            'updates': {'updatedRows': 2}
        }
        
        mock_get_service.return_value = mock_service
        
        # Create test slips
        slips = [
            Slip(player_name="Player1", market_type="Points", line="20.5", 
                 pick="Over", odds=1.85, risk_amount=10, potential_payout=18.5,
                 phase="follicular", confidence_score=0.75, uuid="test-uuid-1"),
            Slip(player_name="Player2", market_type="Rebounds", line="8.5",
                 pick="Under", odds=1.90, risk_amount=10, potential_payout=19.0,
                 phase="ovulatory", confidence_score=0.80, uuid="test-uuid-2")
        ]
        
        result = push_slips_to_sheets(slips)
        
        assert result is True
        mock_values.append.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_values.append.call_args
        assert call_args[1]['spreadsheetId'] == "1-VX73hCObJKMLh66EFaR3eBr9Qi6xv-q9sGTpYH13ZM"
        assert call_args[1]['range'] == "paper_slips!A:O"
        assert len(call_args[1]['body']['values']) == 2
    
    @patch('sheets_integration.get_sheets_service')
    def test_push_slips_to_sheets_empty_list(self, mock_get_service):
        """Test push with empty slip list."""
        result = push_slips_to_sheets([])
        assert result is True
        mock_get_service.assert_not_called()
    
    @patch('sheets_integration.get_sheets_service')
    def test_push_slips_to_sheets_service_failure(self, mock_get_service):
        """Test push when service creation fails."""
        mock_get_service.return_value = None
        
        slips = [Slip(player_name="Test")]
        result = push_slips_to_sheets(slips)
        
        assert result is False
    
    @patch('sheets_integration.get_sheets_service')
    def test_push_slips_to_sheets_api_error(self, mock_get_service):
        """Test push with API error."""
        from googleapiclient.errors import HttpError
        import httplib2
        
        # Create a mock response
        resp = httplib2.Response({'status': '403'})
        resp.reason = 'Forbidden'
        
        # Mock the service to raise HttpError
        mock_service = Mock()
        mock_service.spreadsheets().values().append().execute.side_effect = HttpError(resp, b'Error')
        mock_get_service.return_value = mock_service
        
        slips = [Slip(player_name="Test")]
        result = push_slips_to_sheets(slips)
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
