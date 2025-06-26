"""Basic tests for phasegrid module imports and initialization."""
import pytest


class TestPhasegridImports:
    """Test basic imports from phasegrid package."""
    
    def test_phasegrid_imports(self):
        """Test that phasegrid package can be imported."""
        import phasegrid
        assert hasattr(phasegrid, '__version__')
    
    def test_errors_module(self):
        """Test that errors module can be imported."""
        from phasegrid import errors
        assert hasattr(errors, 'PhaseGridError')
    
    def test_slip_optimizer_imports(self):
        """Test that slip_optimizer can be imported."""
        from phasegrid import slip_optimizer
        assert hasattr(slip_optimizer, 'SlipOptimizer')
    
    def test_slip_processor_imports(self):
        """Test that slip_processor can be imported."""
        from phasegrid import slip_processor
        # Check for any expected class or function
        assert slip_processor is not None
    
    def test_verify_sheets_imports(self):
        """Test that verify_sheets can be imported."""
        from phasegrid import verify_sheets
        assert hasattr(verify_sheets, 'SheetVerifier')
    
    def test_cli_imports(self):
        """Test that CLI module can be imported."""
        from phasegrid import cli
        assert hasattr(cli, 'main') or hasattr(cli, 'cli')
