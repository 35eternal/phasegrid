"""
Central error definitions for PhaseGrid system.
"""


class PhaseGridError(Exception):
    """Base exception for all PhaseGrid errors."""
    pass


class InsufficientSlipsError(PhaseGridError):
    """
    Raised when the number of generated slips falls below the minimum threshold.
    
    This error enforces the guard-rail requirement that at least 5 slips
    must be generated per day for the system to function properly.
    """
    def __init__(self, slip_count, minimum_required=5):
        self.slip_count = slip_count
        self.minimum_required = minimum_required
        super().__init__(
            f"Insufficient slips generated: {slip_count} slips found, "
            f"minimum {minimum_required} required. Use --bypass-guard-rail to override."
        )


class VerificationError(PhaseGridError):
    """Raised when sheet verification fails."""
    pass


class ConfigurationError(PhaseGridError):
    """Raised when configuration values are invalid."""
    pass


class DataIntegrityError(PhaseGridError):
    """Raised when data integrity checks fail."""
    pass