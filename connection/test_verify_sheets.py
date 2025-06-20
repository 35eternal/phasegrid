#!/usr/bin/env python3
"""Tests for sheet verification script."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "scripts"))

import verify_sheets


class TestVerifySheets:
    """Test suite for sheet verification functions."""
    
    @pytest.fixture
    def sample_bets_df(self):
        """Create sample bets_log DataFrame."""
        return pd.DataFrame({
            'source_id': ['BET001', 'BET002', 'BET003'],
            'date': ['2024-06-01', '2024-06-01', '2024-06-02'],
            'player': ['Wilson', 'Stewart', 'Ionescu'],
            'stat': ['points', 'rebounds', 'assists'],
            'line': [20.5, 8.5, 6.5],
            'over_under': ['over', 'over', 'under'],
            'confidence': [0.75, 0.68, 0.82],
            'phase': ['luteal', 'follicular', 'ovulation'],
            'result': [np.nan, 'W', 'L'],
            'updated': ['2024-06-01 10:00', '2024-06-01 10:00', '2024-06-02 15:00']
        })
    
    @pytest.fixture
    def sample_slips_df(self):
        """Create sample slips_log DataFrame."""
        return pd.DataFrame({
            'slip_id': ['SLP001', 'SLP002', 'SLP003'],
            'date': ['2024-06-01', '2024-06-01', '2024-06-02'],
            'type': ['POWER', 'FLEX', 'POWER'],
            'legs': ['BET001,BET002', 'BET003,BET004,BET005', 'BET006'],
            'stake': [10.00, 5.50, 25.00],
            'ev': [1.68, 1.45, 2.10],
            'phase': ['luteal', 'mixed', 'follicular'],
            'result': [np.nan, 'W', 'L'],
            'payout': [np.nan, 15.00, 0.00],
            'created': ['2024-06-01 09:00', '2024-06-01 09:30', '2024-06-02 14:00'],
            'updated': ['2024-06-01 09:00', '2024-06-01 20:00', '2024-06-02 22:00']
        })
    
    def test_verify_column_order_correct(self):
        """Test column order verification with correct order."""
        df = pd.DataFrame(columns=['col1', 'col2', 'col3'])
        expected = ['col1', 'col2', 'col3']
        
        issues = verify_sheets.verify_column_order(df, expected, 'test_sheet')
        assert len(issues) == 0
    
    def test_verify_column_order_incorrect(self):
        """Test column order verification with incorrect order."""
        df = pd.DataFrame(columns=['col2', 'col1', 'col3'])
        expected = ['col1', 'col2', 'col3']
        
        issues = verify_sheets.verify_column_order(df, expected, 'test_sheet')
        assert len(issues) == 1
        assert issues[0]['type'] == 'column_order'
        assert issues[0]['severity'] == 'HIGH'
    
    def test_verify_data_types_numeric_valid(self, sample_slips_df):
        """Test data type verification with valid numeric data."""
        issues = verify_sheets.verify_data_types(sample_slips_df, 'slips_log')
        assert len(issues) == 0
    
    def test_verify_data_types_numeric_invalid(self):
        """Test data type verification with invalid numeric data."""
        df = pd.DataFrame({
            'stake': [10.0, 'invalid', 5.5],
            'ev': [1.5, 2.0, 'bad']
        })
        
        issues = verify_sheets.verify_data_types(df, 'slips_log')
        assert len(issues) >= 1
        assert any(issue['type'] == 'data_type' for issue in issues)
    
    def test_verify_duplicates_none(self, sample_bets_df):
        """Test duplicate verification with no duplicates."""
        issues = verify_sheets.verify_duplicates(sample_bets_df, 'source_id', 'bets_log')
        assert len(issues) == 0
    
    def test_verify_duplicates_found(self):
        """Test duplicate verification with duplicates."""
        df = pd.DataFrame({
            'slip_id': ['SLP001', 'SLP002', 'SLP001', 'SLP003'],
            'stake': [10, 20, 30, 40]
        })
        
        issues = verify_sheets.verify_duplicates(df, 'slip_id', 'slips_log')
        assert len(issues) == 1
        assert issues[0]['type'] == 'duplicate_id'
        assert issues[0]['severity'] == 'HIGH'
        assert 'SLP001' in issues[0]['message']
    
    def test_verify_slips_constraints_valid(self, sample_slips_df):
        """Test slips constraints with valid data."""
        issues = verify_sheets.verify_slips_constraints(sample_slips_df)
        assert len(issues) == 0
    
    def test_verify_slips_constraints_low_stake(self):
        """Test detection of stakes below $5."""
        df = pd.DataFrame({
            'stake': [3.00, 5.00, 10.00],
            'legs': ['BET1', 'BET2', 'BET3']
        })
        
        issues = verify_sheets.verify_slips_constraints(df)
        assert any(issue['type'] == 'constraint_violation' and 
                  'Stakes below $5' in issue['message'] for issue in issues)
    
    def test_verify_slips_constraints_too_many_legs(self):
        """Test detection of slips with >3 legs."""
        df = pd.DataFrame({
            'stake': [10.00],
            'legs': ['BET1,BET2,BET3,BET4']  # 4 legs
        })
        
        issues = verify_sheets.verify_slips_constraints(df)
        assert any(issue['type'] == 'constraint_violation' and 
                  'Slips with >3 legs' in issue['message'] for issue in issues)
    
    def test_verify_slips_constraints_decimal_places(self):
        """Test detection of stakes with >2 decimal places."""
        df = pd.DataFrame({
            'stake': [10.999, 5.00, 7.5],
            'legs': ['BET1', 'BET2', 'BET3']
        })
        
        issues = verify_sheets.verify_slips_constraints(df)
        assert any(issue['type'] == 'formatting' and 
                  '>2 decimal places' in issue['message'] for issue in issues)
    
    def test_verify_settings_tab_valid(self):
        """Test settings tab verification with valid data."""
        mock_connector = Mock()
        mock_connector.read_sheet.return_value = pd.DataFrame({
            'setting': ['bankroll', 'other'],
            'value': ['1000.00', 'test']
        })
        
        issues = verify_sheets.verify_settings_tab(mock_connector)
        assert len(issues) == 0
    
    def test_verify_settings_tab_invalid_bankroll(self):
        """Test settings tab with invalid bankroll."""
        mock_connector = Mock()
        mock_connector.read_sheet.return_value = pd.DataFrame({
            'setting': ['bankroll'],
            'value': ['invalid_number']
        })
        
        issues = verify_sheets.verify_settings_tab(mock_connector)
        assert any(issue['type'] == 'data_conversion' for issue in issues)
    
    def test_verify_settings_tab_negative_bankroll(self):
        """Test settings tab with negative bankroll."""
        mock_connector = Mock()
        mock_connector.read_sheet.return_value = pd.DataFrame({
            'setting': ['bankroll'],
            'value': ['-100.00']
        })
        
        issues = verify_sheets.verify_settings_tab(mock_connector)
        assert any(issue['type'] == 'data_validation' and
                  'Invalid bankroll' in issue['message'] for issue in issues)
    
    def test_verify_settings_tab_missing_bankroll(self):
        """Test settings tab with missing bankroll."""
        mock_connector = Mock()
        mock_connector.read_sheet.return_value = pd.DataFrame({
            'setting': ['other_setting'],
            'value': ['test']
        })
        
        issues = verify_sheets.verify_settings_tab(mock_connector)
        assert any(issue['type'] == 'missing_data' and
                  'Bankroll setting not found' in issue['message'] for issue in issues)
    
    def test_verify_settings_tab_read_error(self):
        """Test settings tab read error handling."""
        mock_connector = Mock()
        mock_connector.read_sheet.side_effect = Exception("Read error")
        
        issues = verify_sheets.verify_settings_tab(mock_connector)
        assert len(issues) == 1
        assert issues[0]['severity'] == 'CRITICAL'
        assert issues[0]['type'] == 'read_error'
    
    @patch('verify_sheets.SheetConnector')
    @patch('verify_sheets.OUTPUT_DIR')
    def test_main_no_issues(self, mock_output_dir, mock_connector_class, 
                           sample_bets_df, sample_slips_df):
        """Test main function with no issues found."""
        # Setup mocks
        mock_output_dir.mkdir.return_value = None
        mock_output_dir.__truediv__.return_value = Path("test_output.csv")
        
        mock_connector = Mock()
        mock_connector_class.return_value = mock_connector
        
        # Mock sheet reads
        mock_connector.read_sheet.side_effect = lambda tab: {
            'bets_log': sample_bets_df,
            'slips_log': sample_slips_df,
            'settings': pd.DataFrame({
                'setting': ['bankroll'],
                'value': ['1000.00']
            })
        }[tab]
        
        with patch('pandas.DataFrame.to_csv'), \
             patch('builtins.print') as mock_print:
            result = verify_sheets.main()
        
        assert result == 0
        # Check for success message
        assert any('✅ Sheet verified' in str(call) for call in mock_print.call_args_list)
    
    @patch('verify_sheets.SheetConnector')
    @patch('verify_sheets.OUTPUT_DIR')
    def test_main_with_critical_issues(self, mock_output_dir, mock_connector_class):
        """Test main function with critical issues."""
        # Setup mocks
        mock_output_dir.mkdir.return_value = None
        mock_output_dir.__truediv__.return_value = Path("test_output.csv")
        
        mock_connector = Mock()
        mock_connector_class.return_value = mock_connector
        
        # Mock sheet with duplicate IDs
        mock_connector.read_sheet.side_effect = lambda tab: {
            'bets_log': pd.DataFrame({
                'source_id': ['BET001', 'BET001'],  # Duplicate
                'date': ['2024-06-01', '2024-06-01'],
                'player': ['Wilson', 'Stewart'],
                'stat': ['points', 'rebounds'],
                'line': [20.5, 8.5],
                'over_under': ['over', 'over'],
                'confidence': [0.75, 0.68],
                'phase': ['luteal', 'follicular'],
                'result': [np.nan, np.nan],
                'updated': ['2024-06-01', '2024-06-01']
            }),
            'slips_log': pd.DataFrame(columns=verify_sheets.SLIPS_LOG_COLUMNS),
            'settings': pd.DataFrame({'setting': ['bankroll'], 'value': ['1000']})
        }[tab]
        
        with patch('pandas.DataFrame.to_csv'), \
             patch('builtins.print') as mock_print:
            result = verify_sheets.main()
        
        assert result == 1  # Should return error code
        # Check for issue summary
        assert any('issues found' in str(call) for call in mock_print.call_args_list)
    
    @patch('verify_sheets.SheetConnector')
    def test_main_connection_failure(self, mock_connector_class):
        """Test main function with connection failure."""
        mock_connector_class.side_effect = Exception("Connection failed")
        
        with patch('builtins.print') as mock_print:
            verify_sheets.main()
        
        assert any('Failed to connect' in str(call) for call in mock_print.call_args_list)
