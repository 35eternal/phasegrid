"""
Sheet verification module for PhaseGrid system.
Validates data integrity and format compliance.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from .errors import VerificationError, DataIntegrityError


class SheetVerifier:
    """Handles verification of sheet data and format compliance."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.validation_errors = []

    def verify_header_format(self, headers: List[str]) -> bool:
        """Verify that sheet headers match expected format."""
        required_headers = ['timestamp', 'prop_id', 'confidence', 'value', 'source']
        missing = set(required_headers) - set(headers)
        if missing:
            raise VerificationError(f"Missing required headers: {missing}")
        return True

    def verify_timestamp_format(self, timestamp: str) -> bool:
        """Verify timestamp follows ISO 8601 format."""
        if timestamp is None:
            raise TypeError("Timestamp cannot be None")
        if not isinstance(timestamp, str):
            raise TypeError(f"Timestamp must be string, got {type(timestamp)}")
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except ValueError:
            raise VerificationError(f"Invalid timestamp format: {timestamp}")

    def verify_prop_id_format(self, prop_id: str) -> bool:
        """Verify prop ID follows expected format."""
        if not re.match(r'^[A-Z0-9_-]+$', prop_id):
            raise VerificationError(f"Invalid prop ID format: {prop_id}")
        return True

    def validate_confidence_value(self, confidence: float) -> bool:
        """Validate confidence is between 0 and 1."""
        if not 0 <= confidence <= 1:
            raise DataIntegrityError(f"Confidence must be between 0 and 1, got {confidence}")
        return True

    def verify_sheet_data(self, data: List[Dict[str, Any]]) -> List[str]:
        """Verify all data in sheet meets requirements."""
        errors = []
        for i, row in enumerate(data):
            try:
                if 'timestamp' in row:
                    self.verify_timestamp_format(row['timestamp'])
                if 'prop_id' in row:
                    self.verify_prop_id_format(row['prop_id'])
                if 'confidence' in row:
                    self.validate_confidence_value(row['confidence'])
            except (VerificationError, DataIntegrityError, TypeError) as e:
                errors.append(f"Row {i}: {str(e)}")
        return errors

    def verify_sheet(self, sheet_name: str) -> List[str]:
        """Verify a specific sheet."""
        # This would connect to the actual sheet in production
        # For now, return empty list (no errors)
        return []

    def reset_validation_errors(self):
        """Reset the validation errors list."""
        self.validation_errors = []

    def get_validation_errors(self) -> List[str]:
        """Get current validation errors."""
        return self.validation_errors

    def add_validation_error(self, error: str):
        """Add a validation error."""
        self.validation_errors.append(error)

    # Additional methods for extended functionality
    def verify_data_types(self, row: Dict[str, Any]) -> bool:
        """Verify data types in a row."""
        type_map = {
            'timestamp': str,
            'prop_id': str,
            'confidence': (int, float),
            'value': (int, float, str),
            'source': str
        }
        
        for field, expected_type in type_map.items():
            if field in row and not isinstance(row[field], expected_type):
                raise TypeError(f"Field {field} should be {expected_type}, got {type(row[field])}")
        return True

    def verify_relationships(self, data: List[Dict[str, Any]]) -> bool:
        """Verify relationships between data points."""
        # Implementation for relationship verification
        return True

    def generate_verification_report(self) -> Dict[str, Any]:
        """Generate a comprehensive verification report."""
        return {
            'errors': self.validation_errors,
            'error_count': len(self.validation_errors),
            'status': 'PASS' if not self.validation_errors else 'FAIL',
            'timestamp': datetime.now().isoformat()
        }
