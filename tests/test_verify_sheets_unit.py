"""
Unit tests for verify_sheets module
"""
import pytest
from phasegrid.verify_sheets import SheetVerifier
from phasegrid.errors import VerificationError, DataIntegrityError


class TestVerifySheetsCoverage:
    """Additional tests to boost coverage for verify_sheets module."""
    
    def test_verify_prop_id_format_various_cases(self):
        """Test prop ID validation with various formats."""
        verifier = SheetVerifier()
        
        # Valid formats
        assert verifier.verify_prop_id_format('PROP_123')
        assert verifier.verify_prop_id_format('TEST-ID')
        assert verifier.verify_prop_id_format('ABC123')
        
        # Invalid formats
        with pytest.raises(VerificationError):
            verifier.verify_prop_id_format('prop_123')  # lowercase
        
        with pytest.raises(VerificationError):
            verifier.verify_prop_id_format('PROP@123')  # invalid character
    
    def test_validate_confidence_edge_cases(self):
        """Test confidence validation edge cases."""
        verifier = SheetVerifier()
        
        # Valid values
        assert verifier.validate_confidence_value(0.0)
        assert verifier.validate_confidence_value(0.5)
        assert verifier.validate_confidence_value(1.0)
        
        # Invalid values
        with pytest.raises(DataIntegrityError):
            verifier.validate_confidence_value(-0.1)
        
        with pytest.raises(DataIntegrityError):
            verifier.validate_confidence_value(1.1)
    
    def test_verify_data_types(self):
        """Test data type verification."""
        verifier = SheetVerifier()
        
        # Valid data
        valid_row = {
            'timestamp': '2024-01-01T00:00:00',
            'prop_id': 'PROP_123',
            'confidence': 0.8,
            'value': 100,
            'source': 'test'
        }
        assert verifier.verify_data_types(valid_row)
        
        # Invalid data type
        invalid_row = {
            'timestamp': 123,  # Should be string
            'prop_id': 'PROP_123'
        }
        with pytest.raises(TypeError):
            verifier.verify_data_types(invalid_row)
    
    def test_verify_relationships(self):
        """Test relationship verification."""
        verifier = SheetVerifier()
        data = [{'id': 1}, {'id': 2}]
        assert verifier.verify_relationships(data)
    
    def test_generate_verification_report(self):
        """Test verification report generation."""
        verifier = SheetVerifier()
        
        # No errors
        report = verifier.generate_verification_report()
        assert report['status'] == 'PASS'
        assert report['error_count'] == 0
        
        # With errors
        verifier.add_validation_error('Test error 1')
        verifier.add_validation_error('Test error 2')
        
        report = verifier.generate_verification_report()
        assert report['status'] == 'FAIL'
        assert report['error_count'] == 2
        assert len(report['errors']) == 2
    
    def test_get_and_reset_validation_errors(self):
        """Test getting and resetting validation errors."""
        verifier = SheetVerifier()
        
        # Add errors
        verifier.add_validation_error('Error 1')
        verifier.add_validation_error('Error 2')
        
        errors = verifier.get_validation_errors()
        assert len(errors) == 2
        
        # Reset errors
        verifier.reset_validation_errors()
        errors = verifier.get_validation_errors()
        assert len(errors) == 0
    
    def test_verify_sheet_data_comprehensive(self):
        """Test comprehensive sheet data verification."""
        verifier = SheetVerifier()
        
        # Mix of valid and invalid data
        data = [
            {
                'timestamp': '2024-01-01T00:00:00',
                'prop_id': 'VALID_ID',
                'confidence': 0.8
            },
            {
                'timestamp': 'invalid-date',
                'prop_id': 'VALID_ID',
                'confidence': 0.9
            },
            {
                'timestamp': '2024-01-01T00:00:00',
                'prop_id': 'invalid@id',
                'confidence': 0.7
            },
            {
                'timestamp': '2024-01-01T00:00:00',
                'prop_id': 'VALID_ID',
                'confidence': 1.5  # Invalid confidence
            }
        ]
        
        errors = verifier.verify_sheet_data(data)
        assert len(errors) == 3  # Three rows with errors
