"""
Guard-rail tests for WNBA Predictor safety mechanisms.
Tests the slip count validation guard-rail.
"""
import pytest
from unittest.mock import Mock, patch


@pytest.mark.xfail(reason="guard-rail pending: Slip count validation not yet implemented")
class TestGuardRails:
    """Test suite for guard-rail safety mechanisms."""
    
    def test_slip_count_guard_rail_throws_exception(self):
        """Test that guard-rail throws exception when slip count < 5 without bypass flag."""
        # Import the module that should contain guard-rail logic
        from phasegrid.guard_rails import SlipCountValidator
        
        # Create validator instance
        validator = SlipCountValidator()
        
        # Test case 1: Should raise exception for slip count < 5 without bypass
        with pytest.raises(ValueError, match="Slip count must be >= 5"):
            validator.validate_slip_count(slip_count=3, bypass=False)
        
        # Test case 2: Should raise exception for slip count = 0
        with pytest.raises(ValueError, match="Slip count must be >= 5"):
            validator.validate_slip_count(slip_count=0, bypass=False)
        
        # Test case 3: Should NOT raise exception when bypass=True
        result = validator.validate_slip_count(slip_count=3, bypass=True)
        assert result is True
        
        # Test case 4: Should NOT raise exception for slip count >= 5
        result = validator.validate_slip_count(slip_count=5, bypass=False)
        assert result is True
        
        result = validator.validate_slip_count(slip_count=10, bypass=False)
        assert result is True
    
    def test_slip_count_guard_rail_logging(self):
        """Test that guard-rail logs warnings appropriately."""
        from phasegrid.guard_rails import SlipCountValidator
        
        validator = SlipCountValidator()
        
        # Mock the logger
        with patch('phasegrid.guard_rails.logger') as mock_logger:
            # Test warning when using bypass
            validator.validate_slip_count(slip_count=2, bypass=True)
            mock_logger.warning.assert_called_with(
                "Guard-rail bypassed: slip count 2 is below minimum threshold of 5"
            )
            
            # Test no warning for normal operation
            mock_logger.reset_mock()
            validator.validate_slip_count(slip_count=8, bypass=False)
            mock_logger.warning.assert_not_called()
    
    def test_slip_count_boundary_conditions(self):
        """Test guard-rail behavior at boundary conditions."""
        from phasegrid.guard_rails import SlipCountValidator
        
        validator = SlipCountValidator()
        
        # Test exactly at threshold
        assert validator.validate_slip_count(slip_count=5, bypass=False) is True
        
        # Test just below threshold
        with pytest.raises(ValueError):
            validator.validate_slip_count(slip_count=4, bypass=False)
        
        # Test negative values
        with pytest.raises(ValueError, match="Slip count cannot be negative"):
            validator.validate_slip_count(slip_count=-1, bypass=False)
        
        # Test with bypass on negative (should still fail)
        with pytest.raises(ValueError, match="Slip count cannot be negative"):
            validator.validate_slip_count(slip_count=-1, bypass=True)


@pytest.mark.xfail(reason="guard-rail pending: Integration with main pipeline not complete")
def test_guard_rail_integration():
    """Test guard-rail integration with main pipeline."""
    from phasegrid.pipeline import PhaseGridPipeline
    from phasegrid.guard_rails import GuardRailConfig
    
    # Configure pipeline with guard-rails enabled
    config = GuardRailConfig(
        slip_count_validation=True,
        minimum_slip_count=5,
        allow_bypass=False
    )
    
    pipeline = PhaseGridPipeline(guard_rail_config=config)
    
    # Test that pipeline respects guard-rail
    test_data = {"slip_count": 3, "other_params": {}}
    
    with pytest.raises(ValueError, match="Guard-rail violation"):
        pipeline.process(test_data)
