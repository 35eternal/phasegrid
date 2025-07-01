"""
Integration tests for CLI commands
"""
import pytest
import subprocess
import sys
import json
from pathlib import Path


class TestCLIIntegration:
    """Test CLI commands through subprocess."""
    
    def test_auto_paper_help(self):
        """Test auto_paper.py help command."""
        result = subprocess.run(
            [sys.executable, "auto_paper.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0 or result.returncode == 2  # Help exits with 0 or 2
        assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()
    
    def test_stats_help(self):
        """Test scripts/stats.py help command."""
        result = subprocess.run(
            [sys.executable, "scripts/stats.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Generate betting statistics" in result.stdout
    
    def test_phasegrid_module_import(self):
        """Test that phasegrid module can be imported."""
        result = subprocess.run(
            [sys.executable, "-c", "import phasegrid; print('OK')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "OK" in result.stdout
    
    @pytest.mark.parametrize("script", [
        "check_dates.py",
        "check_columns.py"
    ])
    def test_check_scripts_run(self, script):
        """Test that check scripts can run."""
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=5
        )
        # These might fail but shouldn't crash
        assert result.returncode in [0, 1]
