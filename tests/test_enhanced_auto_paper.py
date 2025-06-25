#!/usr/bin/env python3
"""Test suite for enhanced auto paper functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_paper import EnhancedAutoPaper, StateManager


class TestStateManager(unittest.TestCase):
    """Test state persistence functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_manager = StateManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_state_file_naming(self):
        """Test that state files are named correctly"""
        state_file = self.state_manager.get_state_file("2025-06-26", "2025-07-05")
        expected = os.path.join(self.temp_dir, "dry_run_2025-06-26_to_2025-07-05.json")
        self.assertEqual(state_file, expected)
    
    def test_load_nonexistent_state(self):
        """Test loading state when file doesn't exist"""
        state = self.state_manager.load_state("2025-06-26", "2025-07-05")
        
        self.assertEqual(state["start_date"], "2025-06-26")
        self.assertEqual(state["end_date"], "2025-07-05")
        self.assertEqual(state["completed_dates"], [])
        self.assertEqual(state["total_slips_generated"], 0)
    
    def test_save_and_load_state(self):
        """Test saving and loading state"""
        test_state = {
            "start_date": "2025-06-26",
            "end_date": "2025-06-27",
            "completed_dates": ["2025-06-26"],
            "total_slips_generated": 15,
            "errors": []
        }
        
        self.state_manager.save_state(test_state, "2025-06-26", "2025-06-27")
        loaded_state = self.state_manager.load_state("2025-06-26", "2025-06-27")
        
        self.assertEqual(loaded_state["completed_dates"], ["2025-06-26"])
        self.assertEqual(loaded_state["total_slips_generated"], 15)
        self.assertIn("last_updated", loaded_state)


class TestEnhancedAutoPaper(unittest.TestCase):
    """Test enhanced auto paper functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ['GOOGLE_SA_JSON'] = json.dumps({
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com"
        })
        
        # Mock the auto paper instance
        with patch('auto_paper.build'):
            self.auto_paper = EnhancedAutoPaper("test-sheet-id", dry_run=True)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation"""
        # Test with edge factor
        slip_data = {
            'confidence': 0.6,
            'edge': 0.1
        }
        score = self.auto_paper.calculate_confidence_score(slip_data)
        self.assertGreater(score, 0.1)  # Should be 0.12 (0.6 * 0.2)
        self.assertLess(score, 0.2)     # But less than 0.2
        
        # Test with model variance
        slip_data = {
            'confidence': 0.5,
            'model_variance': 0.2
        }
        score = self.auto_paper.calculate_confidence_score(slip_data)
        self.assertLess(score, 0.5)  # Model variance reduces confidence
        
        # Test with no factors
        slip_data = {'confidence': 0.7}
        score = self.auto_paper.calculate_confidence_score(slip_data)
        self.assertEqual(score, 0.7)
    
    def test_closing_line_format(self):
        """Test closing line formatting"""
        slip_data = {
            'prop_type': 'points',
            'line': 25.5
        }
        closing_line = self.auto_paper.get_closing_line(slip_data)
        self.assertEqual(closing_line, "points 25.5")
        
        # Test with missing data
        slip_data = {}
        closing_line = self.auto_paper.get_closing_line(slip_data)
        self.assertEqual(closing_line, " N/A")
    
    def test_generate_slip_id(self):
        """Test slip ID generation"""
        slip_data = {
            'player': 'Test Player',
            'prop_type': 'points',
            'line': 25.5,
            'game_id': 'GAME123'
        }
        
        slip_id = self.auto_paper.generate_slip_id(slip_data)
        
        # Check format
        self.assertTrue(slip_id.startswith('PG_'))
        self.assertEqual(len(slip_id), 11)  # PG_ + 8 hex chars
        
        # Check deterministic
        slip_id2 = self.auto_paper.generate_slip_id(slip_data)
        self.assertEqual(slip_id[:10], slip_id2[:10])  # Should be same except date part
    
    @patch('auto_paper.AlertManager')
    def test_guard_rails_alert(self, mock_alert_manager):
        """Test guard rail alert triggering"""
        mock_alert = Mock()
        mock_alert_manager.return_value = mock_alert
        
        # Reinitialize with mocked alert manager
        with patch('auto_paper.build'):
            auto_paper = EnhancedAutoPaper("test-sheet-id")
        
        # Test with too few slips
        slips = [{'id': i} for i in range(3)]  # Only 3 slips
        result = auto_paper.check_guard_rails(slips, "2025-06-26", min_slips=5)
        
        self.assertFalse(result)
        mock_alert.send_critical_alert.assert_called_once()
        
        # Test with enough slips
        slips = [{'id': i} for i in range(10)]  # 10 slips
        result = auto_paper.check_guard_rails(slips, "2025-06-26", min_slips=5)
        
        self.assertTrue(result)
    
    @patch('auto_paper.csv.DictWriter')
    @patch('builtins.open', create=True)
    def test_save_slips_to_csv(self, mock_open, mock_csv_writer):
        """Test saving slips to CSV with new fields"""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_writer = MagicMock()
        mock_csv_writer.return_value = mock_writer
        
        slips = [{
            'slip_id': 'PG_TEST123',
            'confidence_score': 0.75,
            'closing_line': 'points 25.5',
            'player': 'Test Player'
        }]
        
        self.auto_paper.save_slips_to_csv(slips, "2025-06-26")
        
        # Check that new fields are in fieldnames
        call_args = mock_csv_writer.call_args
        fieldnames = call_args[1]['fieldnames']
        self.assertIn('confidence_score', fieldnames)
        self.assertIn('closing_line', fieldnames)
    
    @patch('auto_paper.sqlite3.connect')
    def test_database_migration(self, mock_connect):
        """Test database schema migration"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock existing columns without new fields
        mock_cursor.fetchall.return_value = [
            (0, 'id', 'INTEGER', 0, None, 1),
            (1, 'slip_id', 'TEXT', 0, None, 0),
            (2, 'date', 'TEXT', 0, None, 0),
            (3, 'confidence', 'REAL', 0, None, 0)
        ]
        
        self.auto_paper._init_database()
        
        # Should have attempted to add both new columns
        alter_calls = [call[0][0] for call in mock_cursor.execute.call_args_list 
                      if 'ALTER TABLE' in str(call)]
        self.assertEqual(len(alter_calls), 2)
    
    def test_emit_daily_metrics(self):
        """Test daily metrics emission"""
        slips = [
            {'confidence_score': 0.8},
            {'confidence_score': 0.6},
            {'confidence_score': 0.2},
            {'confidence_score': 0.9}
        ]
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            metrics = self.auto_paper.emit_daily_metrics("2025-06-26", slips)
            
            self.assertEqual(metrics['slip_count'], 4)
            self.assertAlmostEqual(metrics['average_confidence'], 0.625, places=3)
            self.assertEqual(metrics['high_confidence_count'], 2)
            self.assertEqual(metrics['low_confidence_count'], 1)


class TestMultiDayRun(unittest.TestCase):
    """Test multi-day run functionality"""
    
    @patch('auto_paper.EnhancedAutoPaper.run_single_day')
    @patch('auto_paper.build')
    def test_multi_day_iteration(self, mock_build, mock_run_single):
        """Test that multi-day run iterates correctly"""
        # Mock successful runs
        mock_run_single.return_value = (True, 10)
        
        auto_paper = EnhancedAutoPaper("test-sheet-id")
        state = auto_paper.run_multi_day("2025-06-26", "2025-06-28", resume=False)
        
        # Should have called run_single_day 3 times
        self.assertEqual(mock_run_single.call_count, 3)
        
        # Check dates called
        dates_called = [call[0][0] for call in mock_run_single.call_args_list]
        self.assertEqual(dates_called, ["2025-06-26", "2025-06-27", "2025-06-28"])
        
        # Check final state
        self.assertEqual(len(state['completed_dates']), 3)
        self.assertEqual(state['total_slips_generated'], 30)  # 3 days * 10 slips
    
    @patch('auto_paper.EnhancedAutoPaper.run_single_day')
    @patch('auto_paper.build')
    def test_multi_day_resume(self, mock_build, mock_run_single):
        """Test resuming a multi-day run"""
        mock_run_single.return_value = (True, 10)
        
        auto_paper = EnhancedAutoPaper("test-sheet-id")
        
        # Mock existing state with first day completed
        with patch.object(auto_paper.state_manager, 'load_state') as mock_load:
            mock_load.return_value = {
                "start_date": "2025-06-26",
                "end_date": "2025-06-28",
                "completed_dates": ["2025-06-26"],
                "total_slips_generated": 10,
                "errors": []
            }
            
            state = auto_paper.run_multi_day("2025-06-26", "2025-06-28", resume=True)
        
        # Should only process 2 days (27th and 28th)
        self.assertEqual(mock_run_single.call_count, 2)
        dates_called = [call[0][0] for call in mock_run_single.call_args_list]
        self.assertEqual(dates_called, ["2025-06-27", "2025-06-28"])


if __name__ == '__main__':
    unittest.main()
