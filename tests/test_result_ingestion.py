"""
Unit tests for result ingestion and status updates.
Tests CSV parsing, slip status updates, payout calculations, and idempotency.
"""

import pytest
import pandas as pd
import json
import csv
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.update_results import ResultIngester


class TestResultIngestion:
    """Test suite for result ingestion functionality."""
    
    @pytest.fixture
    def mock_sheet_connector(self):
        """Create mock sheet connector."""
        mock = Mock()
        mock.worksheet = Mock()
        mock.worksheet.update = Mock(return_value=True)
        
        # Sample slips data
        slips_data = pd.DataFrame([
            {
                'slip_id': 'POWER_20250618_120000_001',
                'timestamp': '2025-06-18T12:00:00',
                'ticket_type': 'POWER',
                'props': json.dumps([
                    {'prop_id': 'P001', 'player': 'Player1', 'phase': 'follicular'},
                    {'prop_id': 'P002', 'player': 'Player2', 'phase': 'follicular'},
                    {'prop_id': 'P003', 'player': 'Player3', 'phase': 'follicular'}
                ]),
                'n_props': 3,
                'ev': 0.05,
                'stake': 25.0,
                'odds': 10.0,
                'status': 'pending',
                'payout': 0.0,
                'settled_at': ''
            },
            {
                'slip_id': 'FLEX_20250618_120000_001',
                'timestamp': '2025-06-18T12:00:00',
                'ticket_type': 'FLEX',
                'props': json.dumps([
                    {'prop_id': 'P004', 'player': 'Player4', 'phase': 'ovulatory'},
                    {'prop_id': 'P005', 'player': 'Player5', 'phase': 'ovulatory'},
                    {'prop_id': 'P006', 'player': 'Player6', 'phase': 'ovulatory'},
                    {'prop_id': 'P007', 'player': 'Player7', 'phase': 'ovulatory'}
                ]),
                'n_props': 4,
                'ev': 0.08,
                'stake': 30.0,
                'odds': 5.0,
                'status': 'pending',
                'payout': 0.0,
                'settled_at': ''
            },
            {
                'slip_id': 'POWER_20250618_110000_001',
                'timestamp': '2025-06-18T11:00:00',
                'ticket_type': 'POWER',
                'props': json.dumps([
                    {'prop_id': 'P008', 'player': 'Player8', 'phase': 'luteal'},
                    {'prop_id': 'P009', 'player': 'Player9', 'phase': 'luteal'},
                    {'prop_id': 'P010', 'player': 'Player10', 'phase': 'luteal'}
                ]),
                'n_props': 3,
                'ev': 0.03,
                'stake': 20.0,
                'odds': 10.0,
                'status': 'won',  # Already settled
                'payout': 200.0,
                'settled_at': '2025-06-18T13:00:00'
            }
        ])
        
        mock.fetch_slips_log = Mock(return_value=slips_data)
        
        return mock
    
    @pytest.fixture
    def ingester(self, mock_sheet_connector, tmp_path):
        """Create ResultIngester with mocked sheet connector."""
        ingester = ResultIngester(mock_sheet_connector)
        ingester.results_tracker_path = tmp_path / "phase_results_tracker.csv"
        return ingester
    
    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample results CSV."""
        csv_path = tmp_path / "results.csv"
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['prop_id', 'result'])
            writer.writeheader()
            writer.writerows([
                {'prop_id': 'P001', 'result': 'hit'},
                {'prop_id': 'P002', 'result': 'hit'},
                {'prop_id': 'P003', 'result': 'hit'},
                {'prop_id': 'P004', 'result': 'hit'},
                {'prop_id': 'P005', 'result': 'miss'},
                {'prop_id': 'P006', 'result': 'hit'},
                {'prop_id': 'P007', 'result': 'hit'},
                {'prop_id': 'P008', 'result': 'miss'},
                {'prop_id': 'P009', 'result': 'hit'},
                {'prop_id': 'P010', 'result': 'hit'},
            ])
        
        return csv_path
    
    def test_csv_ingestion(self, ingester, sample_csv):
        """Test loading prop results from CSV."""
        results = ingester.ingest_from_csv(str(sample_csv))
        
        assert len(results) == 10
        assert results['P001'] == True
        assert results['P002'] == True
        assert results['P003'] == True
        assert results['P004'] == True
        assert results['P005'] == False
        assert results['P006'] == True
        assert results['P007'] == True
        
    def test_power_slip_win(self, ingester, mock_sheet_connector):
        """Test POWER slip marked as won when all props hit."""
        prop_results = {
            'P001': True,
            'P002': True,
            'P003': True
        }
        
        n_updated = ingester.update_slip_statuses(prop_results)
        
        # Should update 1 slip (the pending POWER slip)
        assert n_updated == 1
        
        # Verify the slip was marked as won with correct payout
        updated_df = mock_sheet_connector.worksheet.update.call_args[0][0]
        power_slip = None
        
        for row in updated_df[1:]:  # Skip header
            if row[0] == 'POWER_20250618_120000_001':
                power_slip = row
                break
        
        assert power_slip is not None
        slip_dict = dict(zip(updated_df[0], power_slip))
        assert slip_dict['status'] == 'won'
        assert float(slip_dict['payout']) == 250.0  # 25 stake * 10 odds
    
    def test_power_slip_loss(self, ingester, mock_sheet_connector):
        """Test POWER slip marked as lost when any prop misses."""
        prop_results = {
            'P001': True,
            'P002': False,  # One miss
            'P003': True
        }
        
        n_updated = ingester.update_slip_statuses(prop_results)
        
        assert n_updated == 1
        
        # Verify the slip was marked as lost
        updated_df = mock_sheet_connector.worksheet.update.call_args[0][0]
        for row in updated_df[1:]:
            if row[0] == 'POWER_20250618_120000_001':
                slip_dict = dict(zip(updated_df[0], row))
                assert slip_dict['status'] == 'lost'
                assert float(slip_dict['payout']) == 0.0
                break
    
    def test_flex_slip_partial_win(self, ingester, mock_sheet_connector):
        """Test FLEX slip with partial hits."""
        prop_results = {
            'P004': True,   # 3 of 4 hit
            'P005': False,
            'P006': True,
            'P007': True
        }
        
        # Mock payout table access
        with patch('builtins.open', create_mock_open({
            'flex': {
                '3_of_4': 2.5,
                '4_of_4': 10.0
            }
        })):
            n_updated = ingester.update_slip_statuses(prop_results)
        
        assert n_updated == 1
        
        # Verify correct payout for 3/4 FLEX
        updated_df = mock_sheet_connector.worksheet.update.call_args[0][0]
        for row in updated_df[1:]:
            if row[0] == 'FLEX_20250618_120000_001':
                slip_dict = dict(zip(updated_df[0], row))
                assert slip_dict['status'] == 'won'
                assert float(slip_dict['payout']) == 75.0  # 30 stake * 2.5 multiplier
                break
    
    def test_idempotency(self, ingester, mock_sheet_connector):
        """Test that already settled slips are not updated again."""
        prop_results = {
            'P008': False,
            'P009': True,
            'P010': True
        }
        
        n_updated = ingester.update_slip_statuses(prop_results)
        
        # Should not update the already settled slip
        assert n_updated == 0
    
    def test_partial_results_handling(self, ingester, mock_sheet_connector):
        """Test handling when only some props have results."""
        # Only partial results available
        prop_results = {
            'P001': True,
            'P002': True,
            # P003 missing - slip should not be updated
        }
        
        n_updated = ingester.update_slip_statuses(prop_results)
        
        # Should not update any slips since not all props are settled
        assert n_updated == 0
    
    def test_phase_results_tracking(self, ingester, mock_sheet_connector, tmp_path):
        """Test that results are tracked in phase_results_tracker.csv."""
        prop_results = {
            'P001': True,
            'P002': True,
            'P003': True
        }
        
        n_updated = ingester.update_slip_statuses(prop_results)
        
        # Check that tracker file was created
        tracker_path = ingester.results_tracker_path
        assert tracker_path.exists()
        
        # Load and verify content
        tracker_df = pd.read_csv(tracker_path)
        assert len(tracker_df) == 1
        assert tracker_df.iloc[0]['slip_id'] == 'POWER_20250618_120000_001'
        assert tracker_df.iloc[0]['phase'] == 'follicular'
        assert tracker_df.iloc[0]['won'] == True
        assert tracker_df.iloc[0]['payout'] == 250.0
    
    def test_empty_results_handling(self, ingester, mock_sheet_connector):
        """Test handling of empty results."""
        n_updated = ingester.update_slip_statuses({})
        assert n_updated == 0
    
    def test_api_scraping_stub(self, ingester):
        """Test that API scraping returns empty dict (stub)."""
        results = ingester.scrape_results_api("2025-06-18")
        assert isinstance(results, dict)
        assert len(results) == 0
    
    def test_invalid_csv_handling(self, ingester, tmp_path):
        """Test handling of invalid CSV file."""
        # Create invalid CSV
        bad_csv = tmp_path / "bad.csv"
        with open(bad_csv, 'w') as f:
            f.write("invalid,csv,content\n")
        
        results = ingester.ingest_from_csv(str(bad_csv))
        assert len(results) == 0  # Should handle gracefully
    
    def test_settled_timestamp(self, ingester, mock_sheet_connector):
        """Test that settled_at timestamp is set correctly."""
        prop_results = {
            'P001': True,
            'P002': True,
            'P003': True
        }
        
        # Capture time before update
        before_time = datetime.now()
        
        n_updated = ingester.update_slip_statuses(prop_results)
        
        # Verify timestamp was set
        updated_df = mock_sheet_connector.worksheet.update.call_args[0][0]
        for row in updated_df[1:]:
            if row[0] == 'POWER_20250618_120000_001':
                slip_dict = dict(zip(updated_df[0], row))
                settled_time = datetime.fromisoformat(slip_dict['settled_at'])
                assert settled_time >= before_time
                break


def create_mock_open(payout_data):
    """Helper to create mock for open() that returns JSON data."""
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_file.read.return_value = json.dumps({'flex': payout_data['flex']})
    mock_open.return_value = mock_file
    return mock_open


if __name__ == "__main__":
    pytest.main([__file__, "-v"])