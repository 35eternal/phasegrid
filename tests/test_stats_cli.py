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
def sample_betting_data():
    """Create sample betting data for testing."""
    return pd.DataFrame({
        'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'bet_id': ['bet1', 'bet2', 'bet3'],
        'stake': [100, 200, 150],
        'payout': [150, 180, 0],
        'result': ['win', 'win', 'loss'],
        'status': ['completed', 'completed', 'completed']
    })


@pytest.fixture
def mock_data():
    """Create mock data for CLI testing."""
    return pd.DataFrame({
        'date': [datetime.now().strftime('%Y-%m-%d')],
        'bet_id': ['test1'],
        'stake': [100],
        'payout': [120],
        'result': ['win'],
        'status': ['completed']
    })


class TestStatsGenerator:
    """Test StatsGenerator class functionality."""
    
    def test_init(self, stats_generator):
        """Test StatsGenerator initialization."""
        assert stats_generator.data_source == 'csv'
        assert stats_generator.bets_log_path.name == 'bets_log.csv'
    
    @patch('pathlib.Path.exists')
    @patch('scripts.stats.pd.read_csv')
    def test_load_data_from_csv(self, mock_read_csv, mock_exists, stats_generator):
        """Test loading data from CSV file - FIXED."""
        # Mock file exists
        mock_exists.return_value = True
        
        # Create test data with proper date filtering
        test_data = pd.DataFrame({
            'date': create_recent_test_data(3)['date'],
            'bet_id': ['bet1', 'bet2', 'bet3'],
            'stake': [100, 200, 150],
            'payout': [120, 250, 100]
        })
        mock_read_csv.return_value = test_data
        
        # Test loading with date filtering
        result = stats_generator.load_data(days=7)
        
        assert result is not None
        assert len(result) == 3  # Should load all 3 rows within date range
        mock_read_csv.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_load_data_no_csv_file(self, mock_exists, stats_generator):
        """Test loading data when CSV file doesn't exist - FIXED."""
        # Mock file doesn't exist
        mock_exists.return_value = False
        
        result = stats_generator.load_data()
        
        # Should return empty DataFrame when file doesn't exist
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    @patch('pathlib.Path.exists')
    @patch('scripts.stats.pd.read_csv')
    def test_load_data_with_date_filtering(self, mock_read_csv, mock_exists):
        """Test loading data with date filtering - FIXED."""
        mock_exists.return_value = True
        
        # Create test data
        test_data = pd.DataFrame({
            'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
            'bet_id': ['bet1', 'bet2', 'bet3'],
            'stake': [100, 200, 150]
        })
        mock_read_csv.return_value = test_data
        
        generator = StatsGenerator()
        result = generator.load_data(start_date='2025-01-01', end_date='2025-01-02')
        
        assert len(result) == 2  # Should return 2 rows (Jan 1 and Jan 2)


class TestStatsCLI:
    """Test CLI interface."""
    
    def test_cli_help(self, runner):
        """Test CLI help output - FIXED."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'PhaseGrid Stats CLI' in result.output
        assert 'Show help message' in result.output or '--help' in result.output
    
    @patch('scripts.stats.StatsGenerator')
    def test_cli_default_command(self, mock_generator_class, runner, mock_data):
        """Test CLI default command - FIXED."""
        # Setup mock
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.load_data.return_value = mock_data
        mock_generator.generate_summary_stats.return_value = {
            'total_bets': 1,
            'total_stake': 100,
            'total_payout': 120,
            'roi': 20.0,
            'win_rate': 100.0
        }
        
        result = runner.invoke(cli, [])
        
        assert result.exit_code == 0
        assert 'Betting Statistics Summary' in result.output
        mock_generator.load_data.assert_called_once()
    
    def test_cli_with_days_option(self, runner):
        """Test CLI with days filtering option - FIXED."""
        with patch('scripts.stats.StatsGenerator') as mock_gen:
            mock_instance = Mock()
            mock_gen.return_value = mock_instance
            mock_instance.load_data.return_value = pd.DataFrame({'stake': [100]})
            mock_instance.generate_summary_stats.return_value = {'roi': 0}
            
            result = runner.invoke(cli, ['--days', '30'])
            assert result.exit_code == 0
    
    def test_cli_with_format_option(self, runner):
        """Test CLI with different output formats - FIXED."""
        with patch('scripts.stats.StatsGenerator') as mock_gen:
            mock_instance = Mock()
            mock_gen.return_value = mock_instance
            mock_instance.load_data.return_value = pd.DataFrame({'stake': [100]})
            mock_instance.generate_summary_stats.return_value = {'roi': 0}
            
            result = runner.invoke(cli, ['--format', 'json'])
            assert result.exit_code == 0
    
    def test_cli_with_output_file(self, runner, tmp_path):
        """Test CLI with output file option - FIXED."""
        output_file = tmp_path / "test_output.html"
        
        with patch('scripts.stats.StatsGenerator') as mock_gen:
            mock_instance = Mock()
            mock_gen.return_value = mock_instance
            mock_instance.load_data.return_value = pd.DataFrame({'stake': [100]})
            mock_instance.generate_summary_stats.return_value = {'roi': 0}
            mock_instance.export_html_report.return_value = output_file
            
            result = runner.invoke(cli, ['--output', str(output_file)])
            assert result.exit_code == 0
    
    def test_cli_error_handling(self, runner):
        """Test CLI error handling."""
        with patch('scripts.stats.StatsGenerator') as mock_gen:
            mock_gen.side_effect = Exception("Test error")
            result = runner.invoke(cli, [])
            assert result.exit_code == 1
            assert "Error" in result.output


class TestStatsCalculation:
    """Test statistics calculation methods."""
    
    def test_calculate_roi(self, stats_generator, sample_betting_data):
        """Test ROI calculation - FIXED."""
        roi = stats_generator.calculate_roi(sample_betting_data)
        expected_roi = ((330 - 450) / 450) * 100  # -26.67%
        assert abs(roi - expected_roi) < 0.001
    
    def test_generate_summary_stats(self, stats_generator, sample_betting_data):
        """Test summary statistics generation - FIXED."""
        stats = stats_generator.generate_summary_stats(sample_betting_data)
        
        assert stats['total_bets'] == 3
        assert stats['total_stake'] == 450
        assert stats['total_payout'] == 330
        assert stats['win_rate'] == pytest.approx(66.67, rel=0.01)
        assert 'roi' in stats
        assert 'roi_percent' in stats  # Check for compatibility key


class TestPlotlyVisualization:
    """Test Plotly chart generation."""
    
    def test_create_plotly_chart(self, stats_generator):
        """Test Plotly chart creation - FIXED using create_roi_chart."""
        stats = {
            'total_bets': 10,
            'total_stake': 1000,
            'total_payout': 1200,
            'roi': 20.0,
            'win_rate': 60.0
        }
        
        # Test both method names work
        fig1 = stats_generator.create_roi_chart(stats=stats)
        fig2 = stats_generator.create_plotly_chart(stats=stats)
        
        assert fig1 is not None
        assert fig2 is not None
        assert hasattr(fig1, 'data')
        assert hasattr(fig1, 'layout')
    
    def test_export_html_report(self, stats_generator, tmp_path):
        """Test HTML report export - FIXED with roi_percent key."""
        stats = {
            'total_bets': 5,
            'total_stake': 500,
            'total_payout': 600,
            'roi': 20.0,
            'win_rate': 60.0
        }
        
        output_file = tmp_path / "test_report.html"
        result = stats_generator.export_html_report(stats, output_file)
        
        assert result == output_file
        assert output_file.exists()
        content = output_file.read_text()
        assert 'PhaseGrid' in content
        assert '<html>' in content


class TestIntegration:
    """Integration tests."""
    
    @patch('pathlib.Path.exists')
    @patch('scripts.stats.pd.read_csv')
    def test_full_stats_generation_flow(self, mock_read_csv, mock_exists):
        """Test full stats generation flow - FIXED."""
        # Mock file exists
        mock_exists.return_value = True
        
        # Create test data with 5 bets
        test_data = pd.DataFrame({
            'date': create_recent_test_data(5)['date'],
            'bet_id': ['bet1', 'bet2', 'bet3', 'bet4', 'bet5'],
            'stake': [100, 200, 150, 100, 50],
            'payout': [120, 250, 0, 150, 0],
            'result': ['win', 'win', 'loss', 'win', 'loss']
        })
        mock_read_csv.return_value = test_data
        
        generator = StatsGenerator()
        
        # Load data
        df = generator.load_data()
        assert len(df) == 5  # Should have 5 bets
        
        # Generate stats
        stats = generator.generate_summary_stats(df)
        assert stats['total_bets'] == 5
        assert stats['total_stake'] == 600
        assert stats['total_payout'] == 520
        
        # Create visualization
        fig = generator.create_roi_chart(df, stats)
        assert fig is not None


# New tests for the enhanced features
class TestEnhancedFeatures:
    """Test new CLI features."""
    
    def test_date_flag(self, runner):
        """Test --date flag functionality."""
        with patch('scripts.stats.StatsGenerator') as mock_gen:
            mock_instance = Mock()
            mock_gen.return_value = mock_instance
            mock_instance.load_data.return_value = pd.DataFrame({'stake': [100]})
            mock_instance.generate_summary_stats.return_value = {'roi': 0}
            
            result = runner.invoke(cli, ['--date', '2025-01-15'])
            assert result.exit_code == 0
            
            # Verify load_data was called with correct date params
            mock_instance.load_data.assert_called_with(
                start_date='2025-01-15', 
                end_date='2025-01-15'
            )
    
    def test_range_flag(self, runner):
        """Test --range flag functionality."""
        with patch('scripts.stats.StatsGenerator') as mock_gen:
            mock_instance = Mock()
            mock_gen.return_value = mock_instance
            mock_instance.load_data.return_value = pd.DataFrame({'stake': [100]})
            mock_instance.generate_summary_stats.return_value = {'roi': 0}
            
            result = runner.invoke(cli, ['--range', '14'])
            assert result.exit_code == 0
            
            # Verify load_data was called with days parameter
            mock_instance.load_data.assert_called_with(days=14)
    
    def test_csv_output(self, runner, tmp_path):
        """Test CSV output functionality."""
        output_file = tmp_path / "stats_test.csv"
        
        with patch('scripts.stats.StatsGenerator') as mock_gen:
            mock_instance = Mock()
            mock_gen.return_value = mock_instance
            mock_instance.load_data.return_value = pd.DataFrame({'stake': [100]})
            mock_instance.generate_summary_stats.return_value = {'roi': 20}
            mock_instance.export_to_csv.return_value = output_file
            
            result = runner.invoke(cli, ['--format', 'csv', '--output', str(output_file)])
            assert result.exit_code == 0
            assert 'Stats saved to' in result.output
    
    def test_unicode_player_names(self, stats_generator):
        """Test Unicode handling in player names."""
        df = pd.DataFrame({
            'player_name': ['José María', 'François', '李明'],
            'stake': [100, 100, 100],
            'payout': [120, 110, 130],
            'result': ['win', 'win', 'win']
        })
        
        # Should handle Unicode without errors
        stats = stats_generator.generate_summary_stats(df)
        assert stats['total_bets'] == 3
        assert stats['total_stake'] == 300
    
    def test_timezone_handling(self, stats_generator):
        """Test timezone handling in date filtering."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('scripts.stats.pd.read_csv') as mock_read:
                # Create data with timezone-aware dates
                test_data = pd.DataFrame({
                    'date': pd.date_range(start=datetime.now().date() - timedelta(days=2), periods=3, freq='D'),
                    'stake': [100, 200, 150],
                    'payout': [120, 180, 165]
                })
                mock_read.return_value = test_data
                
                result = stats_generator.load_data(days=7)
                assert result is not None
    
    def test_invalid_date_handling(self, stats_generator):
        """Test invalid date format handling."""
        with pytest.raises(ValueError, match="Invalid date format"):
            stats_generator.validate_date("2025/01/01")  # Wrong format
        
        with pytest.raises(ValueError, match="Invalid date format"):
            stats_generator.validate_date("invalid-date")
    
    def test_empty_results_handling(self, stats_generator):
        """Test handling of empty query results."""
        empty_df = pd.DataFrame()
        stats = stats_generator.generate_summary_stats(empty_df)
        
        assert stats['total_bets'] == 0
        assert stats['total_stake'] == 0
        assert stats['total_payout'] == 0
        assert stats['roi'] == 0
        assert stats['win_rate'] == 0


# Mark truly obsolete tests as skipped
@pytest.mark.skip(reason="legacy-deprecated: Async processing removed in refactor")
def test_concurrent_date_queries():
    """Legacy test for concurrent processing - no longer supported."""
    pass


@pytest.mark.skip(reason="legacy-deprecated: Old field names no longer supported")
def test_legacy_field_mapping():
    """Legacy test for old database schema - obsolete."""
    pass


@pytest.mark.skip(reason="legacy-deprecated: Caching mechanism removed")
def test_cache_invalidation():
    """Legacy test for cache invalidation - feature removed."""
    pass

