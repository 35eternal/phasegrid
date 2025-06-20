"""
Unit tests for slip optimizer with POWER and FLEX support.
Tests unique IDs, positive EV constraint, prop usage limits, and FLEX EV calculations.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.slip_optimizer import SlipOptimizer


class TestSlipOptimizer:
    """Test suite for SlipOptimizer functionality."""
    
    @pytest.fixture
    def optimizer(self, tmp_path):
        """Create optimizer with test payout config."""
        # Create test payout config
        payout_config = {
            "power": {
                "3": 10.0,
                "4": 20.0,
                "5": 40.0,
                "6": 100.0
            },
            "flex": {
                "3_of_3": 5.0,
                "3_of_4": 2.5,
                "4_of_4": 10.0,
                "4_of_5": 4.0,
                "5_of_5": 20.0,
                "5_of_6": 10.0,
                "6_of_6": 40.0
            }
        }
        
        config_path = tmp_path / "test_payouts.json"
        with open(config_path, 'w') as f:
            json.dump(payout_config, f)
        
        return SlipOptimizer(config_path)
    
    @pytest.fixture
    def sample_props(self):
        """Generate sample props DataFrame."""
        np.random.seed(42)  # For reproducibility
        
        props = pd.DataFrame({
            'prop_id': [f'P{i:03d}' for i in range(20)],
            'player': [f'Player_{i}' for i in range(20)],
            'type': ['points'] * 10 + ['rebounds'] * 10,
            'line': np.random.uniform(15, 30, 20),
            'implied_prob': np.random.uniform(0.45, 0.65, 20),
            'phase': np.random.choice(['follicular', 'ovulatory', 'luteal', 'menstrual'], 20)
        })
        
        return props
    
    def test_power_ev_calculation(self, optimizer):
        """Test POWER play EV calculation."""
        # Test case 1: 3-leg parlay
        props = [
            {'implied_prob': 0.5},
            {'implied_prob': 0.5},
            {'implied_prob': 0.5}
        ]
        ev = optimizer.calculate_power_ev(props)
        expected_ev = (10.0 * 0.125) - 1.0  # 10x payout, 0.125 win prob
        assert abs(ev - expected_ev) < 0.001
        
        # Test case 2: 4-leg parlay
        props = [
            {'implied_prob': 0.6},
            {'implied_prob': 0.6},
            {'implied_prob': 0.6},
            {'implied_prob': 0.6}
        ]
        ev = optimizer.calculate_power_ev(props)
        expected_ev = (20.0 * (0.6**4)) - 1.0
        assert abs(ev - expected_ev) < 0.001
        
        # Test invalid sizes
        assert optimizer.calculate_power_ev([]) == -1.0
        assert optimizer.calculate_power_ev([{'implied_prob': 0.5}] * 7) == -1.0
    
    def test_flex_ev_calculation(self, optimizer):
        """Test FLEX play EV calculation with tiered payouts."""
        # Test case: 3-leg FLEX
        props = [
            {'implied_prob': 0.6},
            {'implied_prob': 0.6},
            {'implied_prob': 0.6}
        ]
        
        ev = optimizer.calculate_flex_ev(props)
        
        # Calculate expected value manually
        # P(3 hits) = 0.6^3 = 0.216, payout = 5x
        # P(2 hits) = 3 * 0.6^2 * 0.4 = 0.432, payout = 0x
        expected_ev = (5.0 * 0.216) - 1.0
        
        assert abs(ev - expected_ev) < 0.001
        
        # Test 4-leg FLEX
        props = [{'implied_prob': 0.5}] * 4
        ev = optimizer.calculate_flex_ev(props)
        
        # P(4/4) = 0.5^4 = 0.0625, payout = 10x
        # P(3/4) = 4 * 0.5^3 * 0.5 = 0.25, payout = 2.5x
        expected_ev = (10.0 * 0.0625) + (2.5 * 0.25) - 1.0
        
        assert abs(ev - expected_ev) < 0.001
    
    def test_unique_slip_ids(self, optimizer, sample_props):
        """Test that all generated slips have unique IDs."""
        slips = optimizer.generate_slips(sample_props, "power", target_slips=10)
        
        slip_ids = [slip['slip_id'] for slip in slips]
        assert len(slip_ids) == len(set(slip_ids))  # All unique
        
        # Test ID format
        for slip_id in slip_ids:
            assert slip_id.startswith("POWER_")
            assert len(slip_id.split('_')) == 4  # POWER_YYYYMMDD_HHMMSS_NNN
    
    def test_positive_ev_constraint(self, optimizer, sample_props):
        """Test that all generated slips have positive EV."""
        # Generate slips with both types
        power_slips = optimizer.generate_slips(sample_props, "power", target_slips=5)
        flex_slips = optimizer.generate_slips(sample_props, "flex", target_slips=5)
        
        # Check all EVs are positive
        for slip in power_slips + flex_slips:
            assert slip['ev'] > 0, f"Slip {slip['slip_id']} has non-positive EV: {slip['ev']}"
    
    def test_max_prop_usage(self, optimizer, sample_props):
        """Test that no prop appears in more than max_per_prop slips."""
        slips = optimizer.generate_slips(sample_props, "power", target_slips=10)
        
        # Count prop usage
        prop_usage = {}
        for slip in slips:
            for prop in slip['props']:
                prop_id = prop['prop_id']
                prop_usage[prop_id] = prop_usage.get(prop_id, 0) + 1
        
        # Check max usage
        for prop_id, usage in prop_usage.items():
            assert usage <= optimizer.max_per_prop, f"Prop {prop_id} used {usage} times"
    
    def test_props_are_lists_not_tuples(self, optimizer, sample_props):
        """Test that props in slips are lists, not tuples (bug fix verification)."""
        slips = optimizer.generate_slips(sample_props, "power", target_slips=5)
        
        for slip in slips:
            assert isinstance(slip['props'], list), f"Props should be list, got {type(slip['props'])}"
            # Also check it's JSON serializable
            json.dumps(slip['props'])  # Should not raise
    
    def test_beam_search_efficiency(self, optimizer, sample_props):
        """Test that beam search controls combinatorial explosion."""
        # With beam_width=50, should complete quickly even with many props
        import time
        
        start = time.time()
        slips = optimizer.generate_slips(sample_props, "power", target_slips=5, beam_width=50)
        elapsed = time.time() - start
        
        assert elapsed < 2.0, f"Beam search took too long: {elapsed}s"
        assert len(slips) > 0, "Should generate at least some slips"
    
    def test_portfolio_generation(self, optimizer, sample_props):
        """Test portfolio generation with both ticket types."""
        portfolio = optimizer.optimize_portfolio(sample_props, power_target=3, flex_target=3)
        
        assert 'power' in portfolio
        assert 'flex' in portfolio
        assert len(portfolio['power']) <= 3
        assert len(portfolio['flex']) <= 3
        
        # Check ticket types are correct
        for slip in portfolio['power']:
            assert slip['ticket_type'] == 'POWER'
        
        for slip in portfolio['flex']:
            assert slip['ticket_type'] == 'FLEX'
    
    def test_slip_size_constraints(self, optimizer, sample_props):
        """Test that all slips have between 3-6 props."""
        slips = optimizer.generate_slips(sample_props, "power", target_slips=10)
        
        for slip in slips:
            assert 3 <= slip['n_props'] <= 6
            assert len(slip['props']) == slip['n_props']
    
    def test_empty_props_handling(self, optimizer):
        """Test handling of empty props DataFrame."""
        empty_props = pd.DataFrame(columns=['prop_id', 'player', 'type', 'line', 'implied_prob', 'phase'])
        
        slips = optimizer.generate_slips(empty_props, "power", target_slips=5)
        assert len(slips) == 0  # Should return empty list, not error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])