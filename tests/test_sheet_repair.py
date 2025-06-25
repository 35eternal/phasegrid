# tests/test_sheet_repair.py
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
from src.sheet_repair import SheetRepair


class TestSheetRepair(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.repair = SheetRepair()
        self.sample_sheet = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02', None, '2024-01-04'],
            'Player': ['LeBron James', 'Stephen Curry', 'Kevin Durant', None],
            'Points': [25.5, 30.2, np.nan, 22.0],
            'Rebounds': [7.5, 5.2, 8.0, None],
            'Assists': [8.0, 6.5, 4.5, 5.0]
        })
    
    def test_initialization(self):
        """Test SheetRepair initialization"""
        self.assertIsNotNone(self.repair)
        self.assertEqual(self.repair.repair_count, 0)
    
    def test_detect_missing_values(self):
        """Test detection of missing values"""
        missing = self.repair.detect_missing_values(self.sample_sheet)
        self.assertEqual(missing['Date'], 1)
        self.assertEqual(missing['Player'], 1)
        self.assertEqual(missing['Points'], 1)
        self.assertEqual(missing['Rebounds'], 1)
    
    def test_fill_missing_dates(self):
        """Test filling missing dates"""
        repaired = self.repair.fill_missing_dates(self.sample_sheet.copy())
        self.assertIsNotNone(repaired.loc[2, 'Date'])
        self.assertEqual(repaired['Date'].isna().sum(), 0)
    
    def test_fill_numeric_columns(self):
        """Test filling numeric columns with appropriate methods"""
        repaired = self.repair.fill_numeric_columns(self.sample_sheet.copy())
        self.assertFalse(repaired['Points'].isna().any())
        self.assertFalse(repaired['Rebounds'].isna().any())
    
    def test_validate_player_names(self):
        """Test player name validation and correction"""
        test_data = pd.DataFrame({
            'Player': ['LeBron James', 'S. Curry', 'K Durant', 'Giannis A.']
        })
        validated = self.repair.validate_player_names(test_data)
        # Should expand abbreviated names
        self.assertIn('Stephen Curry', validated['Player'].values)
        self.assertIn('Kevin Durant', validated['Player'].values)
    
    def test_repair_data_types(self):
        """Test data type repair"""
        test_data = pd.DataFrame({
            'Points': ['25.5', '30', 'N/A', '22.0'],
            'Game_ID': [1001, 1002, 1003, 1004]
        })
        repaired = self.repair.repair_data_types(test_data)
        self.assertEqual(repaired['Points'].dtype, np.float64)
        self.assertEqual(repaired['Game_ID'].dtype, np.int64)
    
    def test_handle_duplicates(self):
        """Test duplicate row handling"""
        test_data = pd.DataFrame({
            'Player': ['Player A', 'Player A', 'Player B'],
            'Date': ['2024-01-01', '2024-01-01', '2024-01-01'],
            'Points': [25, 25, 30]
        })
        deduped = self.repair.handle_duplicates(test_data)
        self.assertEqual(len(deduped), 2)
    
    def test_repair_full_sheet(self):
        """Test complete sheet repair process"""
        repaired = self.repair.repair_sheet(self.sample_sheet.copy())
        # No missing values after repair
        self.assertEqual(repaired.isna().sum().sum(), 0)
        # Repair count should be updated
        self.assertGreater(self.repair.repair_count, 0)
    
    def test_column_name_standardization(self):
        """Test column name standardization"""
        test_data = pd.DataFrame({
            'player name': ['A'],
            'Total Points': [25],
            'AST': [5]
        })
        standardized = self.repair.standardize_column_names(test_data)
        self.assertIn('player_name', standardized.columns)
        self.assertIn('total_points', standardized.columns)
        self.assertIn('assists', standardized.columns)
    
    def test_outlier_detection(self):
        """Test outlier detection and handling"""
        test_data = pd.DataFrame({
            'Points': [25, 30, 28, 150, 27]  # 150 is outlier
        })
        cleaned = self.repair.handle_outliers(test_data, 'Points')
        # Outlier should be capped or removed
        self.assertLess(cleaned['Points'].max(), 100)
    
    def test_date_format_repair(self):
        """Test various date format repairs"""
        test_data = pd.DataFrame({
            'Date': ['01/15/2024', '2024-01-16', '1/17/24', 'Jan 18, 2024']
        })
        repaired = self.repair.standardize_dates(test_data)
        # All dates should be in YYYY-MM-DD format
        for date in repaired['Date']:
            self.assertRegex(date, r'\d{4}-\d{2}-\d{2}')


if __name__ == '__main__':
    unittest.main()
