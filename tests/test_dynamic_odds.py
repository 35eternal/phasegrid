"""
Test suite for Dynamic Odds Injector
"""

import pytest
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.dynamic_odds_injector import DynamicOddsInjector


@pytest.fixture
def mock_predictions_df():
    """Create mock predictions dataframe."""
    return pd.DataFrame({
        'player_name': ['LeBron James', 'Stephen Curry', 'Kevin Durant', 'Giannis Antetokounmpo'],
        'market': ['points', 'threes', 'rebounds', 'assists'],
        'game_date': ['2025-06-24'] * 4,
        'win_probability': [0.65, 0.58, 0.45, 0.72]
    })


@pytest.fixture
def mock_odds_df():
    """Create mock odds dataframe."""
    return pd.DataFrame({
        'player_name': ['LeBron James', 'Stephen Curry', 'Kevin Durant', 'Giannis Antetokounmpo'],
        'market': ['points', 'threes', 'rebounds', 'assists'],
        'game_date': ['2025-06-24'] * 4,
        'decimal_odds': [1.85, 2.10, 2.50, 1.60]
    })


@pytest.fixture
def injector():
    """Create DynamicOddsInjector instance with test environment."""
    with patch.dict(os.environ, {
        'KELLY_FRACTION': '0.25',
        'BANKROLL': '1000',
        'MIN_EDGE': '0.02',
        'PHASE_CONFIG_PATH': 'config/phase_config.json'
    }):
        # Mock the file open to return proper phase config
        mock_config = {
            "preseason": 0.3,
            "early_season": 0.5,
            "mid_season": 0.8,
            "late_season": 1.0,
            "playoffs": 1.2,
            "default": 0.7
        }
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
            return DynamicOddsInjector()


class TestDynamicOddsInjector:
    """Test cases for Dynamic Odds Injector."""
    
    def test_kelly_calculation(self, injector):
        """Test Kelly percentage calculation."""
        # Test case 1: Positive edge
        win_prob = 0.6
        odds = 2.0
        kelly = injector.calculate_kelly_percentage(win_prob, odds)
        
        # Full Kelly: (0.6 * 1 - 0.4) / 1 = 0.2
        # Fractional Kelly: 0.2 * 0.25 = 0.05
        assert abs(kelly - 0.05) < 0.001
        
        # Test case 2: No edge
        win_prob = 0.5
        odds = 2.0
        kelly = injector.calculate_kelly_percentage(win_prob, odds)
        assert kelly == 0.0
        
        # Test case 3: Invalid odds
        kelly = injector.calculate_kelly_percentage(0.6, 0.5)
        assert kelly == 0.0
        
        # Test case 4: Cap at 10%
        win_prob = 0.9
        odds = 2.0
        kelly = injector.calculate_kelly_percentage(win_prob, odds)
        assert kelly <= 0.1
    
    def test_phase_detection(self, injector):
        """Test season phase detection."""
        # Mock different months
        test_cases = [
            (4, "preseason"),
            (6, "mid_season"),
            (8, "late_season"),
            (9, "playoffs"),
            (12, "default")  # Off-season
        ]
        
        for month, expected_phase in test_cases:
            with patch('scripts.dynamic_odds_injector.datetime') as mock_datetime:
                mock_datetime.now.return_value.month = month
                mock_datetime.now.return_value.day = 15
                assert injector.get_current_phase() == expected_phase
    
    def test_edge_calculation(self, injector, mock_predictions_df, mock_odds_df):
        """Test edge calculation and filtering."""
        merged_df = injector.merge_and_calculate_edges(mock_predictions_df, mock_odds_df)
        
        # Check edge calculations
        assert 'edge' in merged_df.columns
        assert 'implied_prob' in merged_df.columns
        
        # Verify edge = win_prob - implied_prob
        for idx, row in merged_df.iterrows():
            expected_edge = row['win_probability'] - (1 / row['decimal_odds'])
            assert abs(row['edge'] - expected_edge) < 0.001
        
        # Check that only positive edges above threshold are kept
        assert all(merged_df['edge'] >= injector.min_edge)
    
    def test_bankroll_constraint(self, injector):
        """Test bankroll constraint enforcement."""
        # Create scenario where total wagers exceed bankroll
        large_bets_df = pd.DataFrame({
            'player_name': [f'Player{i}' for i in range(20)],  # More players to ensure we exceed bankroll
            'market': ['points'] * 20,
            'win_probability': [0.85] * 20,  # Higher win prob
            'decimal_odds': [1.5] * 20,
            'edge': [0.217] * 20,  # Higher edge (0.85 - 0.633)
            'implied_prob': [0.667] * 20
        })
        
        with patch.object(injector, 'get_current_phase', return_value='playoffs'):  # Use playoffs multiplier (1.2)
            result_df = injector.calculate_wagers(large_bets_df)
        
        total_wager = result_df['recommended_wager'].sum()
        assert total_wager <= injector.bankroll
        assert total_wager > injector.bankroll * 0.9  # Should use most of bankroll
    
    def test_output_format(self, injector, mock_predictions_df, mock_odds_df):
        """Test output CSV format."""
        merged_df = injector.merge_and_calculate_edges(mock_predictions_df, mock_odds_df)
        
        with patch.object(injector, 'get_current_phase', return_value='mid_season'):
            result_df = injector.calculate_wagers(merged_df)
        
        # Check required columns
        required_columns = [
            'slip_id', 'player_name', 'market', 'recommended_wager',
            'kelly_percentage', 'phase_multiplier'
        ]
        for col in required_columns:
            assert col in result_df.columns
        
        # Verify slip_id format
        assert all(result_df['slip_id'].str.match(r'SLIP_\d{8}_\d{4}'))
        
        # Check that wagers are positive numbers
        assert all(result_df['recommended_wager'] >= 0)
        assert result_df['recommended_wager'].dtype == float
    
    def test_empty_predictions(self, injector):
        """Test handling of no positive edge bets."""
        empty_df = pd.DataFrame()
        
        with patch.object(injector, 'load_data', return_value=(empty_df, empty_df)):
            with patch.object(injector, 'merge_and_calculate_edges', return_value=empty_df):
                output_file = injector.run()
        
        # Should create empty output file without crashing
        assert output_file.startswith('bets_')
        assert output_file.endswith('.csv')
    
    def test_phase_multiplier_application(self, injector):
        """Test that phase multipliers are correctly applied."""
        test_df = pd.DataFrame({
            'player_name': ['Test Player'],
            'market': ['points'],
            'win_probability': [0.6],
            'decimal_odds': [2.0],
            'edge': [0.1],
            'implied_prob': [0.5]
        })
        
        # Need to reload phase config for each test
        phases = ['preseason', 'mid_season', 'playoffs']
        expected_multipliers = [0.3, 0.8, 1.2]
        
        for phase, expected_mult in zip(phases, expected_multipliers):
            # Create a fresh injector with mocked config for each test
            mock_config = {
                "preseason": 0.3,
                "early_season": 0.5,
                "mid_season": 0.8,
                "late_season": 1.0,
                "playoffs": 1.2,
                "default": 0.7
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
                with patch.dict(os.environ, {
                    'KELLY_FRACTION': '0.25',
                    'BANKROLL': '1000',
                    'MIN_EDGE': '0.02',
                    'PHASE_CONFIG_PATH': 'config/phase_config.json'
                }):
                    test_injector = DynamicOddsInjector()
                    with patch.object(test_injector, 'get_current_phase', return_value=phase):
                        result_df = test_injector.calculate_wagers(test_df.copy())
                        assert float(result_df['phase_multiplier'].iloc[0]) == expected_mult
    
    @patch('scripts.dynamic_odds_injector.pd.read_csv')
    def test_full_pipeline(self, mock_read_csv, injector, mock_predictions_df, mock_odds_df):
        """Test full pipeline execution."""
        # Mock CSV reads
        mock_read_csv.side_effect = [mock_predictions_df, mock_odds_df]
        
        with patch.object(injector, 'get_current_phase', return_value='mid_season'):
            with patch('scripts.dynamic_odds_injector.pd.DataFrame.to_csv') as mock_to_csv:
                output_file = injector.run()
        
        # Verify CSV was saved
        mock_to_csv.assert_called_once()
        assert output_file.startswith('bets_')
        
        # Check that logger was used
        assert mock_read_csv.call_count == 2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_missing_files(self, injector):
        """Test handling of missing input files."""
        with pytest.raises(FileNotFoundError):
            injector.load_data()
    
    def test_negative_kelly(self, injector):
        """Test that negative Kelly values are handled."""
        # Low win probability should give negative Kelly
        kelly = injector.calculate_kelly_percentage(0.3, 2.5)
        assert kelly == 0.0  # Should be capped at 0
    
    def test_extreme_odds(self, injector):
        """Test handling of extreme odds values."""
        # Very high odds
        kelly = injector.calculate_kelly_percentage(0.55, 100.0)
        assert 0 <= kelly <= 0.1  # Should be within valid range
        
        # Very low odds with high win prob should still bet something
        kelly = injector.calculate_kelly_percentage(0.95, 1.05)
        # Full Kelly: (0.95 * 0.05 - 0.05) / 0.05 = -0.05 / 0.05 = -1
        # But since 0.95 * 0.05 = 0.0475 and q = 0.05, it's actually negative
        # So it should be capped at 0
        assert kelly == 0.0
        
        # Better test: reasonable odds with high win prob
        kelly = injector.calculate_kelly_percentage(0.8, 1.5)
        # Full Kelly: (0.8 * 0.5 - 0.2) / 0.5 = 0.2 / 0.5 = 0.4
        # Fractional: 0.4 * 0.25 = 0.1
        # Should be capped at 0.1 (10%)
        assert kelly == 0.1
    
    def test_invalid_phase_config(self):
        """Test fallback when phase config is invalid."""
        with patch.dict(os.environ, {'PHASE_CONFIG_PATH': 'nonexistent.json'}):
            injector = DynamicOddsInjector()
            # Should use default multipliers
            assert 'default' in injector.phase_multipliers
            assert injector.phase_multipliers['default'] == 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])