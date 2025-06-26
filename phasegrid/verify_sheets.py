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
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return True
        except ValueError:
            raise VerificationError(f"Invalid timestamp format: {timestamp}")
    
    def verify_prop_id_format(self, prop_id: str) -> bool:
        """Verify prop ID follows expected pattern."""
        pattern = r'^[A-Z]{2,4}-\d{4,8}$'
        if not re.match(pattern, prop_id):
            raise VerificationError(f"Invalid prop ID format: {prop_id}")
        return True
    
    def verify_confidence_range(self, confidence: float) -> bool:
        """Verify confidence value is within valid range [0.0, 1.0]."""
        if not 0.0 <= confidence <= 1.0:
            raise VerificationError(f"Confidence {confidence} outside valid range [0.0, 1.0]")
        return True
    
    def verify_value_type(self, value: Any, expected_type: str) -> bool:
        """Verify value matches expected type."""
        type_map = {
            'numeric': (int, float),
            'string': str,
            'boolean': bool,
            'list': list,
            'dict': dict
        }
        expected = type_map.get(expected_type)
        if expected and not isinstance(value, expected):
            raise VerificationError(
                f"Value {value} is not of expected type {expected_type}"
            )
        return True
    
    def verify_source_validity(self, source: str) -> bool:
        """Verify source is from approved list."""
        valid_sources = ['api', 'scraper', 'manual', 'prediction', 'aggregate']
        if source not in valid_sources:
            raise VerificationError(f"Invalid source: {source}")
        return True
    
    def verify_data_consistency(self, rows: List[Dict[str, Any]]) -> bool:
        """Verify internal consistency of data rows."""
        prop_groups = {}
        for row in rows:
            prop_id = row.get('prop_id')
            if prop_id:
                if prop_id not in prop_groups:
                    prop_groups[prop_id] = []
                prop_groups[prop_id].append(row)
        
        # Check for duplicate timestamps within same prop
        for prop_id, group_rows in prop_groups.items():
            timestamps = [r['timestamp'] for r in group_rows if 'timestamp' in r]
            if len(timestamps) != len(set(timestamps)):
                raise DataIntegrityError(f"Duplicate timestamps found for prop {prop_id}")
        
        return True
    
    def verify_required_fields(self, row: Dict[str, Any]) -> bool:
        """Verify all required fields are present and non-null."""
        required = ['timestamp', 'prop_id', 'confidence', 'value']
        missing = [f for f in required if f not in row or row[f] is None]
        if missing:
            raise VerificationError(f"Missing required fields: {missing}")
        return True
    
    def verify_numeric_bounds(self, value: float, min_val: float, max_val: float) -> bool:
        """Verify numeric value is within specified bounds."""
        if not min_val <= value <= max_val:
            raise VerificationError(
                f"Value {value} outside bounds [{min_val}, {max_val}]"
            )
        return True
    
    def verify_string_pattern(self, value: str, pattern: str) -> bool:
        """Verify string matches regex pattern."""
        if not re.match(pattern, value):
            raise VerificationError(f"Value '{value}' does not match pattern '{pattern}'")
        return True
    
    def verify_enum_value(self, value: str, allowed: List[str]) -> bool:
        """Verify value is in allowed enumeration."""
        if value not in allowed:
            raise VerificationError(
                f"Value '{value}' not in allowed values: {allowed}"
            )
        return True
    
    def verify_date_range(self, date_str: str, start: str, end: str) -> bool:
        """Verify date falls within specified range."""
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
        
        if not start_date <= date <= end_date:
            raise VerificationError(
                f"Date {date_str} outside range [{start}, {end}]"
            )
        return True
    
    def verify_checksum(self, data: str, checksum: str, algorithm: str = 'sha256') -> bool:
        """Verify data checksum matches expected value."""
        import hashlib
        
        if algorithm == 'sha256':
            calculated = hashlib.sha256(data.encode()).hexdigest()
        elif algorithm == 'md5':
            calculated = hashlib.md5(data.encode()).hexdigest()
        else:
            raise VerificationError(f"Unsupported checksum algorithm: {algorithm}")
        
        if calculated != checksum:
            raise VerificationError("Checksum mismatch")
        return True
    
    def verify_row_count(self, actual: int, expected: int, tolerance: int = 0) -> bool:
        """Verify row count matches expected value within tolerance."""
        if abs(actual - expected) > tolerance:
            raise VerificationError(
                f"Row count {actual} differs from expected {expected} "
                f"by more than tolerance {tolerance}"
            )
        return True
    
    def verify_column_count(self, row: Dict[str, Any], expected: int) -> bool:
        """Verify number of columns in row matches expected."""
        actual = len(row)
        if actual != expected:
            raise VerificationError(
                f"Column count {actual} does not match expected {expected}"
            )
        return True
    
    def verify_unique_constraint(self, rows: List[Dict[str, Any]], field: str) -> bool:
        """Verify field values are unique across all rows."""
        values = [row.get(field) for row in rows if field in row]
        unique_values = set(values)
        
        if len(values) != len(unique_values):
            duplicates = [v for v in values if values.count(v) > 1]
            raise DataIntegrityError(
                f"Duplicate values found for field '{field}': {set(duplicates)}"
            )
        return True
    
    def verify_foreign_key(self, value: str, reference_table: List[str]) -> bool:
        """Verify value exists in reference table."""
        if value not in reference_table:
            raise DataIntegrityError(
                f"Foreign key violation: '{value}' not found in reference table"
            )
        return True
    
    def verify_aggregate_sum(self, 
                           rows: List[Dict[str, Any]], 
                           field: str, 
                           expected_sum: float,
                           tolerance: float = 0.01) -> bool:
        """Verify sum of field values matches expected total."""
        actual_sum = sum(float(row.get(field, 0)) for row in rows)
        if abs(actual_sum - expected_sum) > tolerance:
            raise VerificationError(
                f"Sum of '{field}' ({actual_sum}) differs from "
                f"expected ({expected_sum}) by more than {tolerance}"
            )
        return True
    
    def batch_verify(self, rows: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Perform batch verification on multiple rows.
        Returns (success, list of error messages).
        """
        errors = []
        
        for i, row in enumerate(rows):
            try:
                self.verify_required_fields(row)
                self.verify_timestamp_format(row['timestamp'])
                self.verify_prop_id_format(row['prop_id'])
                self.verify_confidence_range(row['confidence'])
                if 'source' in row:
                    self.verify_source_validity(row['source'])
            except VerificationError as e:
                errors.append(f"Row {i}: {str(e)}")
        
        try:
            self.verify_data_consistency(rows)
        except DataIntegrityError as e:
            errors.append(f"Data consistency: {str(e)}")
        
        return len(errors) == 0, errors