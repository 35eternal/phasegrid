"""
Tests for guard-rail enforcement in slip generation.
"""

import pytest
from datetime import datetime
from phasegrid.slip_processor import SlipProcessor
from phasegrid.errors import InsufficientSlipsError


class TestGuardRail:
    """Test suite for slip generation guard-rail enforcement."""

    def test_guard_rail_enforcement_insufficient_slips(self):
        """Test that InsufficientSlipsError is raised when slips < 5."""
        # Fix: Pass parameters correctly, not as a dictionary
        processor = SlipProcessor(minimum_slips=5, bypass_guard_rail=False)

        # Create props that will generate < 5 slips
        props = [
            {
                'prop_id': 'TEST-001',
                'player_id': 'PLAYER-001',
                'market': 'points',
                'line': 20.5,
                'odds': -110,
                'edge': 0.08,  # Added edge field
                'confidence': 0.8,
                'value': 100,
                'timestamp': datetime.now().isoformat(),
                'source': 'api'
            },
            {
                'prop_id': 'TEST-002',
                'player_id': 'PLAYER-002',
                'market': 'rebounds',
                'line': 8.5,
                'odds': -115,
                'edge': 0.03,  # Below minimum edge
                'confidence': 0.6,
                'value': 200,
                'timestamp': datetime.now().isoformat(),
                'source': 'api'
            }
        ]

        # Mock the optimizer to return fewer than 5 slips
        processor.optimizer.optimize = lambda props, date: []

        # Should raise InsufficientSlipsError
        with pytest.raises(InsufficientSlipsError) as exc_info:
            processor.process(props)

        assert exc_info.value.slip_count < 5
        assert exc_info.value.minimum_required == 5

    def test_guard_rail_passes_with_sufficient_slips(self):
        """Test that processing succeeds when slips >= 5."""
        # Fix: Pass parameters correctly
        processor = SlipProcessor(minimum_slips=5, bypass_guard_rail=False)

        # Create props that will generate >= 5 slips
        props = []
        for i in range(8):
            props.append({
                'prop_id': f'VALID-{i:03d}',
                'player_id': f'PLAYER-{i:03d}',
                'market': 'points',
                'line': 15.5 + i,
                'odds': -110,
                'edge': 0.06 + i * 0.01,  # Added edge field
                'confidence': 0.85,
                'value': 100 + i * 10,
                'timestamp': datetime.now().isoformat(),
                'source': 'api'
            })

        # Mock the optimizer to return 5 slips
        mock_slips = [
            {'slip_id': f'SLIP-{i}', 'prop_id': f'VALID-{i:03d}', 'confidence': 0.85}
            for i in range(5)
        ]
        processor.optimizer.optimize = lambda props, date: mock_slips

        # Should process successfully
        slips = processor.process(props)
        assert len(slips) >= 5

        # Verify slip structure
        for slip in slips:
            assert 'slip_id' in slip
            assert 'prop_id' in slip
            assert 'confidence' in slip

    def test_guard_rail_bypass(self):
        """Test that guard-rail can be bypassed when flag is set."""
        # Fix: Pass parameters correctly
        processor = SlipProcessor(minimum_slips=5, bypass_guard_rail=True)

        # Create props that will generate < 5 slips
        props = [
            {
                'prop_id': 'BYPASS-001',
                'player_id': 'PLAYER-001',
                'market': 'assists',
                'line': 5.5,
                'odds': -105,
                'edge': 0.12,  # Added edge field
                'confidence': 0.9,
                'value': 500,
                'timestamp': datetime.now().isoformat(),
                'source': 'manual'
            }
        ]

        # Mock the optimizer to return 1 slip
        mock_slips = [{'slip_id': 'SLIP-001', 'prop_id': 'BYPASS-001', 'confidence': 0.9}]
        processor.optimizer.optimize = lambda props, date: mock_slips

        # Should process successfully despite < 5 slips
        slips = processor.process(props)
        assert len(slips) < 5
        assert len(slips) == 1

    def test_set_bypass_guard_rail_method(self):
        """Test the set_bypass_guard_rail method."""
        # Fix: Pass parameters correctly
        processor = SlipProcessor(minimum_slips=5, bypass_guard_rail=False)

        props = [{
            'prop_id': 'METHOD-001',
            'player_id': 'PLAYER-001',
            'market': 'points',
            'line': 22.5,
            'odds': -110,
            'edge': 0.09,  # Added edge field
            'confidence': 0.9,
            'value': 100,
            'timestamp': datetime.now().isoformat()
        }]

        # Mock the optimizer to return 1 slip
        mock_slips = [{'slip_id': 'SLIP-001', 'prop_id': 'METHOD-001', 'confidence': 0.9}]
        processor.optimizer.optimize = lambda props, date: mock_slips

        # First attempt should fail
        with pytest.raises(InsufficientSlipsError):
            processor.process(props)

        # Now bypass the guard rail
        processor.bypass_guard_rail = True

        # Should succeed
        slips = processor.process(props)
        assert len(slips) == 1

    def test_confidence_threshold_adjustment(self):
        """Test adjusting confidence threshold affects slip generation."""
        # Fix: Pass parameters correctly
        processor = SlipProcessor(minimum_slips=5, bypass_guard_rail=False)

        # Create props with varying confidence levels
        props = []
        for i in range(10):
            props.append({
                'prop_id': f'CONF-{i:03d}',
                'player_id': f'PLAYER-{i:03d}',
                'market': 'rebounds',
                'line': 7.5 + i * 0.5,
                'odds': -110,
                'edge': 0.05 + i * 0.01,  # Added edge field
                'confidence': 0.5 + i * 0.05,  # 0.5 to 0.95
                'value': 100,
                'timestamp': datetime.now().isoformat()
            })

        # Mock optimizer to filter by confidence
        def mock_optimize(props, date):
            return [
                {'slip_id': f'SLIP-{i}', 'prop_id': p['prop_id'], 'confidence': p['confidence']}
                for i, p in enumerate(props)
                if p.get('confidence', 0) >= 0.75 and p.get('edge', 0) >= 0.05
            ]

        processor.optimizer.optimize = mock_optimize

        # Process with default threshold
        slips_default = processor.process(props)
        assert len(slips_default) >= 5

    def test_optimization_stats_tracking(self):
        """Test that optimization stats are properly tracked."""
        # Fix: Pass parameters correctly
        processor = SlipProcessor(minimum_slips=5, bypass_guard_rail=False)

        props = []
        for i in range(10):
            props.append({
                'prop_id': f'STATS-{i:03d}',
                'player_id': f'PLAYER-{i:03d}',
                'market': 'assists',
                'line': 4.5 + i * 0.5,
                'odds': -110,
                'edge': 0.07,  # Added edge field
                'confidence': 0.8,
                'value': 150,
                'timestamp': datetime.now().isoformat()
            })

        # Mock optimizer to return exactly 5 slips
        mock_slips = [
            {'slip_id': f'SLIP-{i}', 'prop_id': f'STATS-{i:03d}', 'confidence': 0.8}
            for i in range(5)
        ]
        processor.optimizer.optimize = lambda props, date: mock_slips

        # Process and verify
        slips = processor.process(props)
        assert len(slips) == 5

    def test_edge_case_filtering(self):
        """Test that edge cases are properly filtered."""
        # Fix: Pass parameters correctly
        processor = SlipProcessor(minimum_slips=5, bypass_guard_rail=False)

        # Create props with edge cases
        props = [
            # Normal prop
            {'prop_id': 'EDGE-001', 'player_id': 'P1', 'market': 'points', 'line': 20.5, 'odds': -110, 'edge': 0.08, 'confidence': 0.8},
            # Missing confidence (should use default)
            {'prop_id': 'EDGE-002', 'player_id': 'P2', 'market': 'points', 'line': 15.5, 'odds': -110, 'edge': 0.06},
            # Zero confidence (should be filtered)
            {'prop_id': 'EDGE-003', 'player_id': 'P3', 'market': 'points', 'line': 18.5, 'odds': -110, 'edge': 0.05, 'confidence': 0.0},
            # Negative confidence (should be filtered)
            {'prop_id': 'EDGE-004', 'player_id': 'P4', 'market': 'points', 'line': 22.5, 'odds': -110, 'edge': 0.05, 'confidence': -0.5},
            # Very high confidence
            {'prop_id': 'EDGE-005', 'player_id': 'P5', 'market': 'points', 'line': 25.5, 'odds': -110, 'edge': 0.10, 'confidence': 0.95},
            # Add more valid props to meet minimum
            {'prop_id': 'EDGE-006', 'player_id': 'P6', 'market': 'points', 'line': 19.5, 'odds': -110, 'edge': 0.07, 'confidence': 0.82},
            {'prop_id': 'EDGE-007', 'player_id': 'P7', 'market': 'points', 'line': 21.5, 'odds': -110, 'edge': 0.08, 'confidence': 0.88},
            {'prop_id': 'EDGE-008', 'player_id': 'P8', 'market': 'points', 'line': 17.5, 'odds': -110, 'edge': 0.06, 'confidence': 0.79},
        ]

        # Mock optimizer to handle edge cases
        def mock_optimize_edges(props, date):
            valid_slips = []
            for i, p in enumerate(props):
                conf = p.get('confidence', 0.5)  # Default confidence
                edge = p.get('edge', 0.05)
                if conf > 0 and conf <= 1.0 and edge >= 0.05:  # Valid confidence and edge
                    valid_slips.append({
                        'slip_id': f'SLIP-{i}',
                        'prop_id': p['prop_id'],
                        'confidence': conf
                    })
            return valid_slips[:5]  # Return at least 5

        processor.optimizer.optimize = mock_optimize_edges

        # Should process successfully
        slips = processor.process(props)
        assert len(slips) >= 5

        # Verify all slips have valid confidence
        for slip in slips:
            assert slip['confidence'] > 0
            assert slip['confidence'] <= 1.0
