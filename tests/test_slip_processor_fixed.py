"""Fixed tests for slip_processor based on actual implementation."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from phasegrid.slip_processor import SlipProcessor
from phasegrid.errors import InsufficientSlipsError


class TestSlipProcessorFixed:
    """Tests that match actual SlipProcessor implementation."""
    
    def test_processor_initialization(self):
        """Test SlipProcessor initialization."""
        processor = SlipProcessor()
        assert processor is not None
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'minimum_slips')
        assert processor.minimum_slips == 5  # Default value
    
    def test_processor_with_bypass_guard_rail(self):
        """Test processor with guard rail bypassed."""
        processor = SlipProcessor(bypass_guard_rail=True)
        assert processor.bypass_guard_rail is True
        
        # Should not raise error even with 0 slips
        with patch.object(processor.optimizer, 'optimize') as mock_optimize:
            mock_optimize.return_value = []
            result = processor.process([])
            assert result == []
    
    def test_processor_guard_rail_enforcement(self):
        """Test guard rail enforcement."""
        processor = SlipProcessor(bypass_guard_rail=False)
        
        # Should raise InsufficientSlipsError with < 5 slips
        with patch.object(processor.optimizer, 'optimize') as mock_optimize:
            mock_optimize.return_value = []  # 0 slips
            
            with pytest.raises(InsufficientSlipsError) as exc_info:
                processor.process([])
            
            assert "0 slips found" in str(exc_info.value)
            assert "minimum 5 required" in str(exc_info.value)
    
    def test_processor_with_sufficient_slips(self):
        """Test processor with sufficient slips."""
        processor = SlipProcessor()
        
        # Mock to return 5+ slips
        mock_slips = [{'id': i} for i in range(6)]
        with patch.object(processor.optimizer, 'optimize') as mock_optimize:
            mock_optimize.return_value = mock_slips
            result = processor.process([])
            assert result == mock_slips
            assert len(result) >= processor.minimum_slips
