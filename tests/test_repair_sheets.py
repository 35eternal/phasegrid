"""Unit tests for repair_sheets functionality."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.repair_sheets import SheetRepair, DEFAULT_BANKROLL


class TestSheetRepair:
    """Test suite for SheetRepair class."""
    
    @pytest.fixture
    def mock_service(self):
        """Create mock Google Sheets service."""
        mock = Mock()
        mock.spreadsheets.return_value = Mock()
        return mock
    
    @pytest.fixture
    def sheet_repair(self, mock_service):
        """Create SheetRepair instance with mocked service."""
        with patch('scripts.repair_sheets.service_account.Credentials'):
            with patch('scripts.repair_sheets.build', return_value=mock_service):
                repair = SheetRepair()
                repair.service = mock_service
                return repair
    
    def test_remove_duplicate_headers_no_duplicates(self, sheet_repair):
        """Test removing duplicates when none exist."""
        # Mock sheet data with no duplicates
        sheet_repair.get_sheet_data = Mock(return_value=[
            ['source_id', 'amount', 'odds'],
            ['SIM_001', '100', '1.95'],
            ['SIM_002', '150', '2.10']
        ])
        
        result = sheet_repair.remove_duplicate_headers('test_tab')
        assert result == 0
    
    def test_remove_duplicate_headers_with_duplicates(self, sheet_repair, mock_service):
        """Test removing duplicate header rows."""
        # Mock sheet data with duplicate headers
        sheet_repair.get_sheet_data = Mock(return_value=[
            ['source_id', 'amount', 'odds'],
            ['SIM_001', '100', '1.95'],
            ['source_id', 'amount', 'odds'],  # Duplicate
            ['SIM_002', '150', '2.10'],
            ['source_id', 'amount', 'odds']   # Another duplicate
        ])
        
        sheet_repair._get_sheet_id = Mock(return_value=123)
        
        # Mock the batch update
        mock_batch = Mock()
        mock_service.spreadsheets().batchUpdate = Mock(return_value=mock_batch)
        mock_batch.execute = Mock()
        
        result = sheet_repair.remove_duplicate_headers('test_tab')
        assert result == 2
        assert mock_batch.execute.call_count == 2
    
    def test_fix_column_names_no_changes(self, sheet_repair):
        """Test column name fixing when no changes needed."""
        sheet_repair.get_sheet_data = Mock(return_value=[
            ['source_id', 'amount', 'odds']
        ])
        
        result = sheet_repair.fix_column_names('test_tab')
        assert result is False
    
    def test_fix_column_names_with_bet_id(self, sheet_repair, mock_service):
        """Test replacing bet_id with source_id."""
        sheet_repair.get_sheet_data = Mock(return_value=[
            ['bet_id', 'amount', 'odds']
        ])
        
        # Mock the update
        mock_update = Mock()
        mock_service.spreadsheets().values().update = Mock(return_value=mock_update)
        mock_update.execute = Mock()
        
        result = sheet_repair.fix_column_names('test_tab')
        assert result is True
        
        # Verify the update was called with correct data
        update_call = mock_service.spreadsheets().values().update.call_args
        assert update_call[1]['body']['values'][0][0] == 'source_id'
    
    def test_ensure_bankroll_setting_exists(self, sheet_repair):
        """Test bankroll check when it already exists."""
        sheet_repair.get_sheet_data = Mock(return_value=[
            ['Parameter', 'Value'],
            ['Bankroll', '10000'],
            ['Risk_Level', 'moderate']
        ])
        
        result = sheet_repair.ensure_bankroll_setting()
        assert result is True
    
    def test_ensure_bankroll_setting_missing(self, sheet_repair, mock_service):
        """Test adding missing bankroll setting."""
        sheet_repair.get_sheet_data = Mock(return_value=[
            ['Parameter', 'Value'],
            ['Risk_Level', 'moderate']
        ])
        
        # Mock the append
        mock_append = Mock()
        mock_service.spreadsheets().values().append = Mock(return_value=mock_append)
        mock_append.execute = Mock()
        
        with patch.dict('os.environ', {'BANKROLL': '25000'}):
            result = sheet_repair.ensure_bankroll_setting()
            assert result is True
            
            # Verify append was called with correct bankroll
            append_call = mock_service.spreadsheets().values().append.call_args
            assert append_call[1]['body']['values'][0] == ['Bankroll', '25000']
    
    def test_ensure_bankroll_setting_default(self, sheet_repair, mock_service):
        """Test adding bankroll with default value."""
        sheet_repair.get_sheet_data = Mock(return_value=[])
        
        # Mock the append
        mock_append = Mock()
        mock_service.spreadsheets().values().append = Mock(return_value=mock_append)
        mock_append.execute = Mock()
        
        result = sheet_repair.ensure_bankroll_setting()
        assert result is True
        
        # Verify default value was used
        append_call = mock_service.spreadsheets().values().append.call_args
        assert append_call[1]['body']['values'][0] == ['Bankroll', str(DEFAULT_BANKROLL)]
    
    def test_repair_all_integration(self, sheet_repair):
        """Test full repair process."""
        # Mock all sub-methods
        sheet_repair.remove_duplicate_headers = Mock(side_effect=[2, 1, 0])
        sheet_repair.fix_column_names = Mock(side_effect=[True, True, False])
        sheet_repair.ensure_bankroll_setting = Mock(return_value=True)
        
        results = sheet_repair.repair_all()
        
        assert results['duplicates_removed'] == {
            'slips_log': 2,
            'bets_log': 1
        }
        assert results['columns_fixed'] == ['slips_log', 'bets_log']
        assert results['bankroll_added'] is True
        
        # Verify all methods were called for each tab
        assert sheet_repair.remove_duplicate_headers.call_count == 3
        assert sheet_repair.fix_column_names.call_count == 3
        assert sheet_repair.ensure_bankroll_setting.call_count == 1


class TestSheetConnectorIntegration:
    """Integration tests for sheet_connector updates."""
    
    def test_normalize_column_mapping(self):
        """Test bet_id to source_id normalization."""
        from modules.sheet_connector import normalize_column_mapping
        
        data = {
            'bet_id': 'TEST_001',
            'amount': 100,
            'nested': {
                'bet_id': 'NESTED_001'
            },
            'list': [
                {'bet_id': 'LIST_001'},
                {'source_id': 'LIST_002'}
            ]
        }
        
        result = normalize_column_mapping(data)
        
        assert 'bet_id' not in result
        assert result['source_id'] == 'TEST_001'
        assert result['nested']['source_id'] == 'NESTED_001'
        assert result['list'][0]['source_id'] == 'LIST_001'
        assert result['list'][1]['source_id'] == 'LIST_002'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])