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
        processor = SlipProcessor({'bypass_guard_rail': False})
        
        # Create props that will generate < 5 slips
        props = [
            {
                'prop_id': 'TEST-001',
                'confidence': 0.8,
                'value': 100,
                'timestamp': datetime.now().isoformat(),
                'source': 'api'
            },
            {
                'prop_id': 'TEST-002',
                'confidence': 0.6,  # Below threshold
                'value': 200,
                'timestamp': datetime.now().isoformat(),
                'source': 'api'
            }
        ]
        
        # Should raise InsufficientSlipsError
        with pytest.raises(InsufficientSlipsError) as exc_info:
            processor.process(props)
        
        assert exc_info.value.slip_count < 5
        assert exc_info.value.minimum_required == 5
        assert "Use --bypass-guard-rail" in str(exc_info.value)
    
    def test_guard_rail_passes_with_sufficient_slips(self):
        """Test that processing succeeds when slips >= 5."""
        processor = SlipProcessor({'bypass_guard_rail': False})
        
        # Create props that will generate >= 5 slips
        props = []
        for i in range(8):
            props.append({
                'prop_id': f'VALID-{i:03d}',
                'confidence': 0.85,
                'value': 100 + i * 10,
                'timestamp': datetime.now().isoformat(),
                'source': 'api'
            })
        
        # Should process successfully
        slips = processor.process(props)
        assert len(slips) >= 5
        
        # Verify slip structure
        for slip in slips:
            assert 'slip_id' in slip
            assert 'prop_id' in slip
            assert 'confidence' in slip
            assert slip['confidence'] >= 0.75
    
    def test_guard_rail_bypass(self):
        """Test that guard-rail can be bypassed when flag is set."""
        processor = SlipProcessor({'bypass_guard_rail': True})
        
        # Create props that will generate < 5 slips
        props = [
            {
                'prop_id': 'BYPASS-001',
                'confidence': 0.9,
                'value': 500,
                'timestamp': datetime.now().isoformat(),
                'source': 'manual'
            }
        ]
        
        # Should process successfully despite < 5 slips
        slips = processor.process(props)
        assert len(slips) < 5
        assert len(slips) == 1
    
    def test_set_bypass_guard_rail_method(self):
        """Test the set_bypass_guard_rail method."""
        processor = SlipProcessor({'bypass_guard_rail': False})
        
        props = [{
            'prop_id': 'METHOD-001',
            'confidence': 0.9,
            'value': 100,
            'timestamp': datetime.now().isoformat()
        }]
        
        # Should fail initially
        with pytest.raises(InsufficientSlipsError):
            processor.process(props)
        
        # Enable bypass
        processor.set_bypass_guard_rail(True)
        
        # Should now succeed
        slips = processor.process(props)
        assert len(slips) == 1
    
    def test_confidence_threshold_adjustment(self):
        """Test adjusting confidence threshold affects slip generation."""
        processor = SlipProcessor({'bypass_guard_rail': True})
        
        # Create props with varied confidence levels
        props = []
        for i in range(10):
            props.append({
                'prop_id': f'CONF-{i:03d}',
                'confidence': 0.5 + i * 0.05,  # 0.5 to 0.95
                'value': 100 + i,
                'timestamp': datetime.now().isoformat()
            })
        
        # Default threshold (0.75)
        slips_default = processor.process(props)
        default_count = len(slips_default)
        
        # Lower threshold to get more slips
        processor.adjust_confidence_threshold(0.6)
        slips_lower = processor.process(props)
        lower_count = len(slips_lower)
        
        assert lower_count > default_count
        assert all(s['confidence'] >= 0.6 for s in slips_lower)
    
    def test_optimization_stats_tracking(self):
        """Test that optimization statistics are properly tracked."""
        processor = SlipProcessor({'bypass_guard_rail': True})
        
        props = [
            # Will pass
            {'prop_id': 'STAT-001', 'confidence': 0.9, 'value': 100, 
             'timestamp': datetime.now().isoformat()},
            # Low confidence
            {'prop_id': 'STAT-002', 'confidence': 0.3, 'value': 200,
             'timestamp': datetime.now().isoformat()},
            # Duplicate
            {'prop_id': 'STAT-001', 'confidence': 0.9, 'value': 100,
             'timestamp': datetime.now().isoformat()},
            # Edge case (test prop)
            {'prop_id': 'TEST-EDGE', 'confidence': 0.9, 'value': 300,
             'timestamp': datetime.now().isoformat()},
            # Missing required field
            {'prop_id': 'STAT-003', 'confidence': 0.9}  # No value/timestamp
        ]
        
        slips = processor.process(props)
        stats = processor.get_optimization_stats()
        
        assert stats['total_props'] == 5
        assert stats['filtered_by_confidence'] == 1
        assert stats['filtered_by_duplicate'] == 1
        assert stats['filtered_by_edge'] == 1
        assert stats['filtered_by_validity'] == 1
        assert stats['generated_slips'] == 1
        assert len(slips) == 1
    
    def test_edge_case_filtering(self):
        """Test that edge cases are properly filtered."""
        processor = SlipProcessor({'bypass_guard_rail': True})
        
        props = [
            # Extreme values
            {'prop_id': 'EDGE-001', 'confidence': 0.9, 'value': 10000000,
             'timestamp': datetime.now().isoformat()},
            # Test prop
            {'prop_id': 'TEST-123', 'confidence': 0.9, 'value': 100,
             'timestamp': datetime.now().isoformat()},
            # Demo prop
            {'prop_id': 'DEMO-456', 'confidence': 0.9, 'value': 200,
             'timestamp': datetime.now().isoformat()},
            # Valid prop
            {'prop_id': 'PROD-789', 'confidence': 0.9, 'value': 300,
             'timestamp': datetime.now().isoformat()}
        ]
        
        slips = processor.process(props)
        
        # Only the valid prop should generate a slip
        assert len(slips) == 1
        assert slips[0]['prop_id'] == 'PROD-789'