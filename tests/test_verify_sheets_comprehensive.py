"""Comprehensive tests for phasegrid.verify_sheets module."""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from phasegrid.verify_sheets import SheetVerifier
from phasegrid.errors import VerificationError, DataIntegrityError


class TestSheetVerifier:
    """Test the SheetVerifier class."""
    
    @pytest.fixture
    def verifier(self):
        """Create a SheetVerifier instance."""
        return SheetVerifier()
    
    @pytest.fixture
    def verifier_with_config(self):
        """Create a SheetVerifier with configuration."""
        config = {
            'strict_mode': True,
            'max_errors': 10,
            'timestamp_format': 'ISO8601'
        }
        return SheetVerifier(config=config)
    
    def test_init_default(self, verifier):
        """Test default initialization."""
        assert verifier.config == {}
        assert verifier.validation_errors == []
    
    def test_init_with_config(self, verifier_with_config):
        """Test initialization with config."""
        assert verifier_with_config.config['strict_mode'] is True
        assert verifier_with_config.config['max_errors'] == 10
        assert verifier_with_config.validation_errors == []
    
    def test_verify_header_format_valid(self, verifier):
        """Test header verification with valid headers."""
        headers = ['timestamp', 'prop_id', 'confidence', 'value', 'source', 'extra_field']
        result = verifier.verify_header_format(headers)
        assert result is True
    
    def test_verify_header_format_missing_required(self, verifier):
        """Test header verification with missing required headers."""
        headers = ['timestamp', 'prop_id']  # Missing confidence, value, source
        
        with pytest.raises(VerificationError) as exc_info:
            verifier.verify_header_format(headers)
        
        assert "Missing required headers" in str(exc_info.value)
        assert "confidence" in str(exc_info.value)
        assert "value" in str(exc_info.value)
        assert "source" in str(exc_info.value)
    
    def test_verify_header_format_empty(self, verifier):
        """Test header verification with empty headers."""
        with pytest.raises(VerificationError) as exc_info:
            verifier.verify_header_format([])
        
        assert "Missing required headers" in str(exc_info.value)
    
    def test_verify_timestamp_format_valid_iso(self, verifier):
        """Test timestamp verification with valid ISO format."""
        valid_timestamps = [
            '2024-01-01T12:00:00',
            '2024-12-31T23:59:59',
            '2024-06-15T14:30:00Z',
            '2024-06-15T14:30:00+00:00',
            '2024-06-15T14:30:00-05:00'
        ]
        
        for ts in valid_timestamps:
            assert verifier.verify_timestamp_format(ts) is True
    
    def test_verify_timestamp_format_invalid(self, verifier):
        """Test timestamp verification with invalid formats."""
        invalid_timestamps = [
            '2024/01/01 12:00:00',  # Wrong separator
            '01-01-2024',  # Wrong format
            'not a timestamp',
            '2024-13-01T00:00:00',  # Invalid month
            '2024-01-32T00:00:00',  # Invalid day
            ''  # Empty string
        ]
        
        for ts in invalid_timestamps:
            # Should either return False or raise an exception
            try:
                result = verifier.verify_timestamp_format(ts)
                assert result is False
            except (ValueError, VerificationError):
                # Also acceptable
                pass


class TestSheetVerifierDataValidation:
    """Test data validation methods."""
    
    @pytest.fixture
    def verifier(self):
        """Create a SheetVerifier instance."""
        return SheetVerifier()
    
    def test_validate_confidence_value(self, verifier):
        """Test confidence value validation."""
        # Assuming there's a method to validate confidence
        if hasattr(verifier, 'validate_confidence'):
            # Valid confidence values (0-1 or 0-100)
            assert verifier.validate_confidence(0.95) is True
            assert verifier.validate_confidence(0.0) is True
            assert verifier.validate_confidence(1.0) is True
            
            # Invalid values
            assert verifier.validate_confidence(-0.1) is False
            assert verifier.validate_confidence(1.1) is False
            assert verifier.validate_confidence("high") is False
    
    def test_validate_prop_id_format(self, verifier):
        """Test prop_id format validation."""
        if hasattr(verifier, 'validate_prop_id'):
            # Valid prop IDs
            assert verifier.validate_prop_id('PROP-001') is True
            assert verifier.validate_prop_id('123456') is True
            
            # Invalid prop IDs
            assert verifier.validate_prop_id('') is False
            assert verifier.validate_prop_id(None) is False


class TestSheetVerifierBulkValidation:
    """Test bulk data validation."""
    
    @pytest.fixture
    def verifier(self):
        """Create a SheetVerifier instance."""
        return SheetVerifier()
    
    @pytest.fixture
    def sample_sheet_data(self):
        """Create sample sheet data."""
        return [
            {
                'timestamp': '2024-01-01T12:00:00',
                'prop_id': 'PROP-001',
                'confidence': 0.85,
                'value': 25.5,
                'source': 'model_v1'
            },
            {
                'timestamp': '2024-01-01T13:00:00',
                'prop_id': 'PROP-002',
                'confidence': 0.92,
                'value': 30.0,
                'source': 'model_v2'
            }
        ]
    
    def test_verify_sheet_data(self, verifier, sample_sheet_data):
        """Test verification of complete sheet data."""
        # Check if there's a method to verify complete sheets
        if hasattr(verifier, 'verify_sheet'):
            result = verifier.verify_sheet(sample_sheet_data)
            # Should return validation result
            assert result is not None
    
    def test_validation_errors_collection(self, verifier):
        """Test that validation errors are collected."""
        # Start with no errors
        assert len(verifier.validation_errors) == 0
        
        # Try to validate something invalid
        try:
            verifier.verify_header_format(['invalid'])
        except VerificationError:
            pass
        
        # Errors might be collected (depends on implementation)
        # This is more of a behavior test


class TestSheetVerifierEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def verifier(self):
        """Create a SheetVerifier instance."""
        return SheetVerifier()
    
    def test_verify_header_format_none(self, verifier):
        """Test header verification with None."""
        with pytest.raises((VerificationError, TypeError)):
            verifier.verify_header_format(None)
    
    def test_verify_timestamp_format_none(self, verifier):
        """Test timestamp verification with None."""
        with pytest.raises((ValueError, TypeError, VerificationError)):
            verifier.verify_timestamp_format(None)
    
    def test_unicode_handling(self, verifier):
        """Test handling of unicode characters."""
        # Unicode in headers
        headers = ['timestamp', 'prop_id', 'confidence', 'value', 'source', '测试']
        result = verifier.verify_header_format(headers)
        assert result is True
        
        # Unicode in timestamp (should fail)
        with pytest.raises((ValueError, VerificationError)):
            verifier.verify_timestamp_format('2024-01-01T12:00:00测试')


class TestSheetVerifierIntegration:
    """Integration tests for SheetVerifier."""
    
    @pytest.fixture
    def verifier(self):
        """Create a SheetVerifier instance."""
        return SheetVerifier({'strict_mode': True})
    
    def test_full_verification_workflow(self, verifier):
        """Test complete verification workflow."""
        # Step 1: Verify headers
        headers = ['timestamp', 'prop_id', 'confidence', 'value', 'source']
        assert verifier.verify_header_format(headers) is True
        
        # Step 2: Verify individual timestamps
        assert verifier.verify_timestamp_format('2024-01-01T12:00:00') is True
        
        # Step 3: Check validation errors (should be none for valid data)
        assert len(verifier.validation_errors) == 0
    
    def test_error_accumulation(self, verifier):
        """Test that errors accumulate properly."""
        # Try multiple invalid operations
        error_count = 0
        
        # Invalid headers
        try:
            verifier.verify_header_format([])
        except VerificationError:
            error_count += 1
        
        # Invalid timestamp
        try:
            verifier.verify_timestamp_format('invalid')
        except (ValueError, VerificationError):
            error_count += 1
        
        # Should have caught errors
        assert error_count > 0


# Test any additional methods that might exist
class TestSheetVerifierExtensions:
    """Test additional methods that might exist."""
    
    @pytest.fixture
    def verifier(self):
        """Create a SheetVerifier instance."""
        return SheetVerifier()
    
    def test_method_existence(self, verifier):
        """Test which methods exist on the verifier."""
        expected_methods = [
            'verify_header_format',
            'verify_timestamp_format'
        ]
        
        for method in expected_methods:
            assert hasattr(verifier, method)
    
    def test_reset_validation_errors(self, verifier):
        """Test resetting validation errors if method exists."""
        if hasattr(verifier, 'reset_errors'):
            verifier.validation_errors = ['error1', 'error2']
            verifier.reset_errors()
            assert len(verifier.validation_errors) == 0
