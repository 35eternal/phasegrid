"""
Tests for the anomaly filter that removes PrizePicks Demons and Goblins.
"""
import pytest
from datetime import datetime
from phasegrid.anomaly_filter import AnomalyFilter


class TestAnomalyFilter:
    """Test suite for AnomalyFilter class."""
    
    @pytest.fixture
    def sample_slips_with_demons_goblins(self):
        """Create sample slips with demon and goblin variations."""
        return [
            # LeBron James - Points (Standard: 27.5, Goblin: 22.5, Demon: 32.5)
            {
                'slip_id': 'PP_001_20250708',
                'player': 'LeBron James',
                'team': 'LAL',
                'prop_type': 'points',
                'line': 27.5,
                'over_odds': -110,
                'under_odds': -110
            },
            {
                'slip_id': 'PP_002_20250708',
                'player': 'LeBron James',
                'team': 'LAL',
                'prop_type': 'points',
                'line': 22.5,  # Goblin (easier)
                'over_odds': -140,
                'under_odds': +120
            },
            {
                'slip_id': 'PP_003_20250708',
                'player': 'LeBron James',
                'team': 'LAL',
                'prop_type': 'points',
                'line': 32.5,  # Demon (harder)
                'over_odds': +150,
                'under_odds': -170
            },
            # Steph Curry - Threes Made (Standard: 4.5, Demon: 5.5)
            {
                'slip_id': 'PP_004_20250708',
                'player': 'Stephen Curry',
                'team': 'GSW',
                'prop_type': 'three_pointers_made',
                'line': 4.5,
                'over_odds': -110,
                'under_odds': -110
            },
            {
                'slip_id': 'PP_005_20250708',
                'player': 'Stephen Curry',
                'team': 'GSW',
                'prop_type': 'three_pointers_made',
                'line': 5.5,  # Demon
                'over_odds': +140,
                'under_odds': -160
            },
            # Nikola Jokic - Rebounds (only standard)
            {
                'slip_id': 'PP_006_20250708',
                'player': 'Nikola Jokic',
                'team': 'DEN',
                'prop_type': 'rebounds',
                'line': 11.5,
                'over_odds': -115,
                'under_odds': -105
            }
        ]
    
    @pytest.fixture
    def filter_instance(self):
        """Create AnomalyFilter instance."""
        return AnomalyFilter(tolerance_percentage=15.0)
    
    def test_filter_removes_demons_and_goblins(self, filter_instance, sample_slips_with_demons_goblins):
        """Test that filter correctly removes demon and goblin projections."""
        filtered = filter_instance.filter_anomalies(sample_slips_with_demons_goblins)
        
        # Should have 3 slips remaining (one for each player/prop combo)
        assert len(filtered) == 3
        
        # Check LeBron's points - should keep the middle value (27.5)
        lebron_points = [s for s in filtered if s['player'] == 'LeBron James' and s['prop_type'] == 'points']
        assert len(lebron_points) == 1
        assert lebron_points[0]['line'] == 27.5
        
        # Check Curry's threes - should keep the lower value (4.5) when only 2 options
        curry_threes = [s for s in filtered if s['player'] == 'Stephen Curry']
        assert len(curry_threes) == 1
        assert curry_threes[0]['line'] == 4.5
        
        # Check Jokic's rebounds - should remain unchanged
        jokic_rebounds = [s for s in filtered if s['player'] == 'Nikola Jokic']
        assert len(jokic_rebounds) == 1
        assert jokic_rebounds[0]['line'] == 11.5
    
    def test_empty_slips_list(self, filter_instance):
        """Test handling of empty slips list."""
        result = filter_instance.filter_anomalies([])
        assert result == []
    
    def test_single_projection_per_player(self, filter_instance):
        """Test that single projections are kept unchanged."""
        slips = [
            {
                'slip_id': 'PP_001',
                'player': 'Player A',
                'prop_type': 'points',
                'line': 20.5
            },
            {
                'slip_id': 'PP_002',
                'player': 'Player B',
                'prop_type': 'rebounds',
                'line': 8.5
            }
        ]
        
        filtered = filter_instance.filter_anomalies(slips)
        assert len(filtered) == 2
        assert filtered == slips
    
    def test_tolerance_percentage(self, filter_instance):
        """Test that tolerance percentage correctly identifies anomalies."""
        slips = [
            # Small difference (10%) - not anomalies
            {
                'slip_id': 'PP_001',
                'player': 'Player A',
                'prop_type': 'points',
                'line': 20.0
            },
            {
                'slip_id': 'PP_002',
                'player': 'Player A',
                'prop_type': 'points',
                'line': 22.0  # 10% difference
            },
            # Large difference (30%) - anomalies
            {
                'slip_id': 'PP_003',
                'player': 'Player B',
                'prop_type': 'points',
                'line': 20.0
            },
            {
                'slip_id': 'PP_004',
                'player': 'Player B',
                'prop_type': 'points',
                'line': 26.0  # 30% difference
            }
        ]
        
        filtered = filter_instance.filter_anomalies(slips)
        
        # Player A should have both slips (within tolerance)
        player_a_slips = [s for s in filtered if s['player'] == 'Player A']
        assert len(player_a_slips) == 2
        
        # Player B should have only one slip (outside tolerance)
        player_b_slips = [s for s in filtered if s['player'] == 'Player B']
        assert len(player_b_slips) == 1
        assert player_b_slips[0]['line'] == 20.0  # Should keep lower one
    
    def test_identify_anomaly_type(self, filter_instance, sample_slips_with_demons_goblins):
        """Test identification of demon/goblin/standard types."""
        # Get LeBron's slips
        lebron_slips = [s for s in sample_slips_with_demons_goblins 
                       if s['player'] == 'LeBron James']
        
        types = filter_instance.identify_anomaly_type(lebron_slips)
        
        # Check that types are correctly identified
        assert len(types) == 3
        
        # Find which slip has which line
        for slip in lebron_slips:
            if slip['line'] == 22.5:
                assert types[slip['slip_id']] == 'goblin'
            elif slip['line'] == 27.5:
                assert types[slip['slip_id']] == 'standard'
            elif slip['line'] == 32.5:
                assert types[slip['slip_id']] == 'demon'
    
    def test_custom_tolerance(self):
        """Test filter with custom tolerance percentage."""
        # Create filter with 5% tolerance
        strict_filter = AnomalyFilter(tolerance_percentage=5.0)
        
        slips = [
            {
                'slip_id': 'PP_001',
                'player': 'Player A',
                'prop_type': 'points',
                'line': 20.0
            },
            {
                'slip_id': 'PP_002',
                'player': 'Player A',
                'prop_type': 'points',
                'line': 21.5  # 7.5% difference
            }
        ]
        
        filtered = strict_filter.filter_anomalies(slips)
        
        # With 5% tolerance, 7.5% difference should be filtered
        assert len(filtered) == 1
        assert filtered[0]['line'] == 20.0
    
    def test_real_world_scenario(self, filter_instance):
        """Test with realistic WNBA data."""
        slips = [
            # A'ja Wilson points variations
            {'slip_id': 'PP_101', 'player': "A'ja Wilson", 'prop_type': 'points', 
             'line': 18.5, 'team': 'LV'},  # Goblin
            {'slip_id': 'PP_102', 'player': "A'ja Wilson", 'prop_type': 'points', 
             'line': 22.5, 'team': 'LV'},  # Standard
            {'slip_id': 'PP_103', 'player': "A'ja Wilson", 'prop_type': 'points', 
             'line': 26.5, 'team': 'LV'},  # Demon
            # Breanna Stewart rebounds
            {'slip_id': 'PP_104', 'player': 'Breanna Stewart', 'prop_type': 'rebounds', 
             'line': 8.5, 'team': 'NY'},
            {'slip_id': 'PP_105', 'player': 'Breanna Stewart', 'prop_type': 'rebounds', 
             'line': 10.5, 'team': 'NY'},
            # Sabrina Ionescu assists (only standard)
            {'slip_id': 'PP_106', 'player': 'Sabrina Ionescu', 'prop_type': 'assists', 
             'line': 5.5, 'team': 'NY'},
        ]
        
        filtered = filter_instance.filter_anomalies(slips)
        
        # Should have 3 player/prop combinations
        assert len(filtered) == 3
        
        # Check specific values
        aja_points = next(s for s in filtered if s['player'] == "A'ja Wilson")
        assert aja_points['line'] == 22.5  # Middle value
        
        breanna_rebounds = next(s for s in filtered if s['player'] == 'Breanna Stewart')
        assert breanna_rebounds['line'] == 8.5  # Lower value for 2-slip case
        
        sabrina_assists = next(s for s in filtered if s['player'] == 'Sabrina Ionescu')
        assert sabrina_assists['line'] == 5.5  # Unchanged
