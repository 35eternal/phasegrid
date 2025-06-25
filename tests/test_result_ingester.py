# tests/test_result_ingester.py
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import pandas as pd
from datetime import datetime, timedelta
import requests
from src.result_ingester import ResultIngester


class TestResultIngester(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.ingester = ResultIngester()
        self.sample_api_response = {
            "games": [
                {
                    "game_id": "001",
                    "date": "2024-01-15",
                    "home_team": "Lakers",
                    "away_team": "Celtics",
                    "players": [
                        {
                            "name": "LeBron James",
                            "team": "Lakers",
                            "stats": {
                                "points": 28,
                                "rebounds": 8,
                                "assists": 9
                            }
                        }
                    ]
                }
            ]
        }
        self.sample_csv_data = """Date,Player,Points,Rebounds,Assists
2024-01-15,LeBron James,28,8,9
2024-01-15,Stephen Curry,32,5,7"""
    
    def test_initialization(self):
        """Test ResultIngester initialization"""
        self.assertIsNotNone(self.ingester)
        self.assertEqual(self.ingester.source_type, 'api')
        self.assertIsNone(self.ingester.last_ingestion_time)
    
    @patch('requests.get')
    def test_fetch_from_api(self, mock_get):
        """Test fetching results from API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_api_response
        mock_get.return_value = mock_response
        
        results = self.ingester.fetch_from_api('http://test.com/api')
        self.assertEqual(len(results['games']), 1)
        self.assertEqual(results['games'][0]['game_id'], '001')
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_api_error_handling(self, mock_get):
        """Test API error handling"""
        # Test 404 error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with self.assertRaises(Exception):
            self.ingester.fetch_from_api('http://test.com/api')
        
        # Test connection error
        mock_get.side_effect = requests.ConnectionError()
        with self.assertRaises(requests.ConnectionError):
            self.ingester.fetch_from_api('http://test.com/api')
    
    def test_parse_api_response(self):
        """Test parsing API response to DataFrame"""
        df = self.ingester.parse_api_response(self.sample_api_response)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['player'], 'LeBron James')
        self.assertEqual(df.iloc[0]['points'], 28)
    
    @patch('builtins.open', new_callable=mock_open, read_data='')
    def test_read_csv_results(self, mock_file):
        """Test reading results from CSV"""
        mock_file.return_value.read.return_value = self.sample_csv_data
        df = self.ingester.read_csv_results('test.csv')
        self.assertEqual(len(df), 2)
        self.assertIn('LeBron James', df['Player'].values)
    
    def test_validate_results(self):
        """Test result validation"""
        valid_df = pd.DataFrame({
            'Date': ['2024-01-15'],
            'Player': ['Test Player'],
            'Points': [25],
            'Rebounds': [5],
            'Assists': [5]
        })
        self.assertTrue(self.ingester.validate_results(valid_df))
        
        # Test with missing columns
        invalid_df = pd.DataFrame({
            'Date': ['2024-01-15'],
            'Player': ['Test Player']
        })
        self.assertFalse(self.ingester.validate_results(invalid_df))
    
    def test_merge_results(self):
        """Test merging new results with existing data"""
        existing = pd.DataFrame({
            'Date': ['2024-01-14'],
            'Player': ['Player A'],
            'Points': [20]
        })
        new = pd.DataFrame({
            'Date': ['2024-01-15'],
            'Player': ['Player A'],
            'Points': [25]
        })
        merged = self.ingester.merge_results(existing, new)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged.iloc[-1]['Points'], 25)
    
    @patch('pandas.DataFrame.to_csv')
    def test_save_results(self, mock_to_csv):
        """Test saving results to file"""
        df = pd.DataFrame({'test': [1, 2, 3]})
        self.ingester.save_results(df, 'output.csv')
        mock_to_csv.assert_called_once_with('output.csv', index=False)
    
    def test_filter_date_range(self):
        """Test filtering results by date range"""
        df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10),
            'Value': range(10)
        })
        start_date = '2024-01-03'
        end_date = '2024-01-07'
        filtered = self.ingester.filter_date_range(df, start_date, end_date)
        self.assertEqual(len(filtered), 5)
    
    @patch('requests.get')
    def test_retry_logic(self, mock_get):
        """Test retry logic for API calls"""
        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = self.sample_api_response
        
        mock_get.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]
        
        results = self.ingester.fetch_with_retry('http://test.com/api', max_retries=3)
        self.assertEqual(mock_get.call_count, 3)
        self.assertIsNotNone(results)
    
    def test_incremental_ingestion(self):
        """Test incremental data ingestion"""
        # Set last ingestion time
        self.ingester.last_ingestion_time = datetime.now() - timedelta(days=1)
        
        all_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=5),
            'Value': range(5)
        })
        
        # Should only get data after last ingestion
        new_data = self.ingester.get_incremental_data(all_data)
        self.assertLess(len(new_data), len(all_data))


if __name__ == '__main__':
    unittest.main()
