"""Unit tests for phase_modifier functionality in SlipOptimizer."""

import pytest
from slip_optimizer import SlipOptimizer, Bet, Slip


class TestPhaseModifier:
    """Test suite for phase_modifier parameter in optimize_slips."""
    
    @pytest.fixture
    def sample_bets(self):
        """Create a small, deterministic set of bets for testing."""
        # Use better odds and higher confidence for reliable slip generation
        return [
            {
                'player': 'LeBron James',
                'prop_type': 'points',
                'line': 25.5,
                'over_under': 'over',
                'odds': -110,  # Better odds
                'confidence': 0.75,  # Higher confidence
                'projection': 28.2,
                'game': 'Lakers vs Warriors'
            },
            {
                'player': 'Stephen Curry',
                'prop_type': 'threes',
                'line': 4.5,
                'over_under': 'over',
                'odds': -105,
                'confidence': 0.80,  # Higher confidence
                'projection': 5.3,
                'game': 'Warriors vs Lakers'
            },
            {
                'player': 'Anthony Davis',
                'prop_type': 'rebounds',
                'line': 10.5,
                'over_under': 'under',
                'odds': 100,  # Positive odds
                'confidence': 0.70,
                'projection': 9.8,
                'game': 'Lakers vs Warriors'
            },
            {
                'player': 'Draymond Green',
                'prop_type': 'assists',
                'line': 6.5,
                'over_under': 'over',
                'odds': 110,  # Positive odds
                'confidence': 0.72,
                'projection': 7.1,
                'game': 'Warriors vs Lakers'
            },
            {
                'player': 'Klay Thompson',
                'prop_type': 'points',
                'line': 18.5,
                'over_under': 'over',
                'odds': -115,
                'confidence': 0.68,
                'projection': 20.1,
                'game': 'Warriors vs Lakers'
            },
            {
                'player': 'Austin Reaves',
                'prop_type': 'assists',
                'line': 3.5,
                'over_under': 'over',
                'odds': -120,
                'confidence': 0.66,
                'projection': 4.2,
                'game': 'Lakers vs Warriors'
            }
        ]
    
    @pytest.fixture
    def optimizer(self):
        """Create a SlipOptimizer instance."""
        return SlipOptimizer()
    
    def test_default_phase_modifier_unchanged_behavior(self, optimizer, sample_bets):
        """Test that phase_modifier=1.0 (default) produces identical results to omitting the parameter."""
        # Run optimization without phase_modifier (using default)
        slips_default = optimizer.optimize_slips(
            available_bets=sample_bets,
            target_slips=3,  # Increased from 2
            slip_types=['Power'],  # Just Power for more predictable results
        )
        
        # Run optimization with explicit phase_modifier=1.0
        slips_explicit = optimizer.optimize_slips(
            available_bets=sample_bets,
            target_slips=3,
            slip_types=['Power'],
            phase_modifier=1.0
        )
        
        # Verify we got some slips
        assert len(slips_default) > 0, "No slips generated with default settings"
        
        # Verify identical results
        assert len(slips_default) == len(slips_explicit)
        
        for slip_d, slip_e in zip(slips_default, slips_explicit):
            # Check that all slip properties are identical
            assert slip_d.slip_type == slip_e.slip_type
            assert slip_d.expected_value == slip_e.expected_value
            assert slip_d.total_odds == slip_e.total_odds
            assert slip_d.confidence == slip_e.confidence
            assert len(slip_d.bets) == len(slip_e.bets)
            
            # Check that bets are identical
            for bet_d, bet_e in zip(slip_d.bets, slip_e.bets):
                assert bet_d.player == bet_e.player
                assert bet_d.prop_type == bet_e.prop_type
                assert bet_d.line == bet_e.line
                assert bet_d.over_under == bet_e.over_under
    
    def test_phase_modifier_increases_expected_value(self, optimizer, sample_bets):
        """Test that phase_modifier > 1.0 increases expected values."""
        # Run with default modifier
        slips_base = optimizer.optimize_slips(
            available_bets=sample_bets,
            target_slips=2,
            slip_types=['Power'],  # Just Power for simplicity
            phase_modifier=1.0
        )
        
        # Skip test if no slips generated
        if not slips_base:
            pytest.skip("No slips generated with test data")
        
        # Run with increased modifier (e.g., 1.5x boost during optimal phase)
        slips_boosted = optimizer.optimize_slips(
            available_bets=sample_bets,
            target_slips=2,
            slip_types=['Power'],
            phase_modifier=1.5
        )
        
        # Verify we got slips
        assert len(slips_base) > 0
        assert len(slips_boosted) == len(slips_base)
        
        # Verify expected values are increased
        for slip_base, slip_boosted in zip(slips_base, slips_boosted):
            assert slip_boosted.expected_value > slip_base.expected_value
            # Expected value should be exactly 1.5x the base
            assert abs(slip_boosted.expected_value - (slip_base.expected_value * 1.5)) < 0.001
    
    def test_phase_modifier_decreases_expected_value(self, optimizer, sample_bets):
        """Test that phase_modifier < 1.0 decreases expected values."""
        # Run with default modifier
        slips_base = optimizer.optimize_slips(
            available_bets=sample_bets,
            target_slips=2,
            slip_types=['Power'],
            phase_modifier=1.0
        )
        
        # Skip test if no slips generated
        if not slips_base:
            pytest.skip("No slips generated with test data")
        
        # Run with decreased modifier (e.g., 0.7x penalty during suboptimal phase)
        slips_penalized = optimizer.optimize_slips(
            available_bets=sample_bets,
            target_slips=2,
            slip_types=['Power'],
            phase_modifier=0.7
        )
        
        # Verify expected values are decreased
        for slip_base, slip_penalized in zip(slips_base, slips_penalized):
            assert slip_penalized.expected_value < slip_base.expected_value
            # Expected value should be exactly 0.7x the base
            assert abs(slip_penalized.expected_value - (slip_base.expected_value * 0.7)) < 0.001
    
    def test_phase_modifier_zero_edge_case(self, optimizer, sample_bets):
        """Test edge case where phase_modifier=0.0."""
        slips = optimizer.optimize_slips(
            available_bets=sample_bets,
            target_slips=2,
            slip_types=['Power'],
            phase_modifier=0.0
        )
        
        # With zero modifier, expected values should be zero or no slips generated
        # (because EV <= 0 slips are filtered out)
        if slips:
            for slip in slips:
                assert slip.expected_value == 0.0
    
    def test_phase_modifier_with_different_slip_types(self, optimizer, sample_bets):
        """Test that phase_modifier applies correctly to all slip types."""
        modifier = 1.25
        
        for slip_type in ['Power', 'Flex']:
            slips_base = optimizer.optimize_slips(
                available_bets=sample_bets,
                target_slips=2,
                slip_types=[slip_type],
                phase_modifier=1.0
            )
            
            # Skip if no slips generated for this type
            if not slips_base:
                continue
                
            slips_modified = optimizer.optimize_slips(
                available_bets=sample_bets,
                target_slips=2,
                slip_types=[slip_type],
                phase_modifier=modifier
            )
            
            if slips_base and slips_modified:  # If slips were generated
                for base, modified in zip(slips_base, slips_modified):
                    assert modified.expected_value == pytest.approx(
                        base.expected_value * modifier, 
                        rel=1e-5
                    )