# tests/test_prediction_engine.py
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
from src.prediction_engine import PredictionEngine


class TestPredictionEngine(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.engine = PredictionEngine()
        self.sample_data = pd.DataFrame({
            'player': ['Player A', 'Player B', 'Player C'],
            'stat': ['points', 'rebounds', 'assists'],
            'projection': [25.5, 8.5, 6.5],
            'line': [24.5, 9.5, 5.5],
            'confidence': [0.75, 0.65, 0.80]
        })
    
    def test_initialization(self):
        """Test PredictionEngine initialization"""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.model_version, "1.0")
    
    def test_load_projections(self):
        """Test loading projections from file"""
        with patch('pandas.read_csv') as mock_read:
            mock_read.return_value = self.sample_data
            result = self.engine.load_projections('test.csv')
            self.assertTrue(result)
            mock_read.assert_called_once_with('test.csv')
    
    def test_calculate_edge(self):
        """Test edge calculation"""
        projection = 25.5
        line = 24.5
        expected_edge = ((projection - line) / line) * 100
        actual_edge = self.engine.calculate_edge(projection, line)
        self.assertAlmostEqual(actual_edge, expected_edge, places=2)
    
    def test_filter_high_confidence(self):
        """Test filtering high confidence predictions"""
        self.engine.data = self.sample_data
        filtered = self.engine.filter_high_confidence(threshold=0.70)
        self.assertEqual(len(filtered), 2)  # Only Player A and C
    
    def test_generate_predictions(self):
        """Test generating predictions"""
        self.engine.data = self.sample_data
        predictions = self.engine.generate_predictions()
        self.assertEqual(len(predictions), 3)
        self.assertIn('edge', predictions.columns)
        self.assertIn('recommendation', predictions.columns)
    
    def test_validate_data(self):
        """Test data validation"""
        # Test with valid data
        self.engine.data = self.sample_data
        self.assertTrue(self.engine.validate_data())
        
        # Test with missing columns
        invalid_data = pd.DataFrame({'player': ['A'], 'stat': ['points']})
        self.engine.data = invalid_data
        self.assertFalse(self.engine.validate_data())
    
    def test_calculate_kelly_criterion(self):
        """Test Kelly Criterion calculation"""
        probability = 0.60
        odds = 1.85
        expected_kelly = (probability * odds - 1) / (odds - 1)
        actual_kelly = self.engine.calculate_kelly_criterion(probability, odds)
        self.assertAlmostEqual(actual_kelly, expected_kelly, places=4)
    
    def test_handle_empty_data(self):
        """Test handling empty data"""
        self.engine.data = pd.DataFrame()
        predictions = self.engine.generate_predictions()
        self.assertTrue(predictions.empty)
    
    def test_confidence_scoring(self):
        """Test confidence score calculation"""
        # Mock historical accuracy
        with patch.object(self.engine, 'get_historical_accuracy', return_value=0.65):
            score = self.engine.calculate_confidence_score('Player A', 'points')
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
    
    def test_edge_threshold_filtering(self):
        """Test filtering by edge threshold"""
        self.engine.data = self.sample_data
        self.engine.min_edge_threshold = 2.0
        predictions = self.engine.generate_predictions()
        # All predictions should have edge > 2.0 or be marked as 'skip'
        for _, row in predictions.iterrows():
            if row['recommendation'] != 'skip':
                self.assertGreaterEqual(row['edge'], 2.0)


if __name__ == '__main__':
    unittest.main()
