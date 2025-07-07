"""
Test suite for PhaseGrid stats CLI
Updated to fix schema mismatches and properly categorize legacy tests
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, mock_open
import pandas as pd
from click.testing import CliRunner

# Import the module we're testing
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.stats import StatsGenerator, cli

# Add this at the top of test_stats_cli.py after imports
import pandas as pd
from datetime import datetime, timedelta

# Helper to create recent test data
def create_recent_test_data(num_days=3):
    """Create test data with recent dates."""
    end_date = datetime.now().date()
    dates = pd.date_range(end=end_date, periods=num_days, freq='D')
    return pd.DataFrame({
        'date': dates,
        'bet_id': [f'bet{i+1}' for i in range(num_days)],
        'stake': [100 * (i+1) for i in range(num_days)],
        'payout': [120 * (i+1) if i < 2 else 0 for i in range(num_days)],
        'result': ['win' if i < 2 else 'loss' for i in range(num_days)]
    })

@pytest.fixture
def stats_generator():
    """Create a StatsGenerator instance for testing."""
    return StatsGenerator()

@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()

@pytest.fixture
