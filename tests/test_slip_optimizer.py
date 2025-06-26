# tests/test_slip_optimizer.py
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime
from src.slip_optimizer import SlipOptimizer


class TestSlipOptimizer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.optimizer = SlipOptimizer()
        self.sample_predictions = pd.DataFrame({
            'player': ['Player A', 'Player B', 'Player C', 'Player D'],
            'stat': ['points', 'rebounds', 'assists', 'points'],
            'projection': [25.5, 8.5, 6.5, 30.0],
            'line': [24.5, 9.5, 5.5, 28.5],
            'edge': [4.08, -10.53, 18.18, 5.26],
            'confidence': [0.75, 0.45, 0.85, 0.70],
            'ev': [1.08, 0.89, 1.18, 1.05]
        })
    
    def test_initialization(self):
        """Test SlipOptimizer initialization"""
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(self.optimizer.max_entries, 6)
        self.assertEqual(self.optimizer.min_edge, 5.0)
    
    def test_calculate_correlation_matrix(self):
        """Test correlation matrix calculation"""
        corr_matrix = self.optimizer.calculate_correlation_matrix(self.sample_predictions)
        self.assertEqual(corr_matrix.shape, (4, 4))
        # Diagonal should be 1s
        np.testing.assert_array_almost_equal(np.diag(corr_matrix), np.ones(4))
    
    def test_optimize_single_entry(self):
        """Test single entry optimization"""
        result = self.optimizer.optimize_single_entry(self.sample_predictions)
        # Should return the highest EV entry
        self.assertEqual(result['player'], 'Player C')
        self.assertEqual(result['ev'], 1.18)
    
    def test_optimize_parlay(self):
        """Test parlay optimization"""
        parlay = self.optimizer.optimize_parlay(self.sample_predictions, legs=3)
        self.assertEqual(len(parlay), 3)
        # Should be sorted by EV descending
        evs = [p['ev'] for p in parlay]
        self.assertEqual(evs, sorted(evs, reverse=True))
    
    def test_apply_kelly_sizing(self):
        """Test Kelly criterion sizing"""
        bankroll = 1000
        probability = 0.60
        odds = 1.91
        size = self.optimizer.apply_kelly_sizing(bankroll, probability, odds)
        expected_kelly = (probability * odds - 1) / (odds - 1)
        expected_size = bankroll * expected_kelly * self.optimizer.kelly_fraction
        self.assertAlmostEqual(size, expected_size, places=2)
    
    def test_filter_by_constraints(self):
        """Test filtering by constraints"""
        # Add sport column for testing
        self.sample_predictions['sport'] = ['NBA', 'NBA', 'NFL', 'NBA']
        
        constraints = {
            'min_edge': 5.0,
            'sports': ['NBA'],
            'max_players_per_game': 2
        }
        filtered = self.optimizer.filter_by_constraints(self.sample_predictions, constraints)
        # Should only have Player A and D (NBA with edge > 5)
        self.assertEqual(len(filtered), 2)
        self.assertTrue(all(filtered['sport'] == 'NBA'))
        self.assertTrue(all(filtered['edge'] >= 5.0))
    
    def test_calculate_parlay_ev(self):
        """Test parlay EV calculation"""
        legs = [
            {'ev': 1.10, 'probability': 0.55},
            {'ev': 1.15, 'probability': 0.58},
            {'ev': 1.08, 'probability': 0.54}
        ]
        parlay_ev = self.optimizer.calculate_parlay_ev(legs)
        expected_ev = 1.10 * 1.15 * 1.08
        self.assertAlmostEqual(parlay_ev, expected_ev, places=4)
    
    def test_diversification_check(self):
        """Test portfolio diversification"""
        entries = [
            {'player': 'Player A', 'sport': 'NBA', 'team': 'Lakers'},
            {'player': 'Player B', 'sport': 'NBA', 'team': 'Lakers'},
            {'player': 'Player C', 'sport': 'NFL', 'team': 'Chiefs'}
        ]
        diversity_score = self.optimizer.calculate_diversity_score(entries)
        # Score should be between 0 and 1
        self.assertGreaterEqual(diversity_score, 0.0)
        self.assertLessEqual(diversity_score, 1.0)
    
    def test_optimize_with_correlation(self):
        """Test optimization considering correlations"""
        # Mock correlation matrix
        with patch.object(self.optimizer, 'calculate_correlation_matrix') as mock_corr:
            mock_corr.return_value = np.array([
                [1.0, 0.8, 0.2, 0.1],
                [0.8, 1.0, 0.3, 0.2],
                [0.2, 0.3, 1.0, 0.1],
                [0.1, 0.2, 0.1, 1.0]
            ])
            
            result = self.optimizer.optimize_with_correlation(self.sample_predictions, max_correlation=0.5)
            # Should avoid highly correlated picks
            self.assertGreater(len(result), 0)
    
    def test_bankroll_management(self):
        """Test bankroll management rules"""
        bankroll = 1000
        current_exposure = 200
        
        # Test max exposure limit
        max_bet = self.optimizer.calculate_max_bet(bankroll, current_exposure)
        self.assertLessEqual(max_bet + current_exposure, bankroll * 0.25)
        
        # Test stop loss
        self.optimizer.daily_loss = -100
        should_stop = self.optimizer.check_stop_loss()
        self.assertTrue(should_stop)
    
    def test_slip_generation(self):
        """Test complete slip generation"""
        slip = self.optimizer.generate_optimal_slip(
            predictions=self.sample_predictions,
            bankroll=1000,
            strategy='balanced'
        )
        
        self.assertIn('entries', slip)
        self.assertIn('total_stake', slip)
        self.assertIn('expected_return', slip)
        self.assertIn('strategy', slip)
        self.assertEqual(slip['strategy'], 'balanced')
        
        # Stake should not exceed bankroll limits
        self.assertLessEqual(slip['total_stake'], 1000 * 0.10)  # 10% max per slip


if __name__ == '__main__':
    unittest.main()
