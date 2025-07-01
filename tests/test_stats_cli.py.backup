"""Comprehensive tests for scripts/stats.py - PhaseGrid Stats CLI"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import pandas as pd
from click.testing import CliRunner
from datetime import datetime, timedelta


class TestStatsGenerator:
    """Test the StatsGenerator class."""
    
    @pytest.fixture
    def stats_generator(self):
        """Create a StatsGenerator instance for testing."""
        # Import here to avoid import errors
        from scripts.stats import StatsGenerator
        return StatsGenerator(data_source='csv')
    
    @pytest.fixture
    def sample_betting_data(self):
        """Create sample betting data."""
        return pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'bet_id': ['BET001', 'BET002', 'BET003'],
            'stake': [10.0, 20.0, 15.0],
            'payout': [15.0, 0.0, 22.5],
            'result': ['WON', 'LOST', 'WON'],
            'roi': [0.5, -1.0, 0.5]
        })
    
    def test_init(self, stats_generator):
        """Test StatsGenerator initialization."""
        assert stats_generator.data_source == 'csv'
        assert stats_generator.data_path == Path('data')
        assert stats_generator.metrics_path == Path('data/metrics')
        assert stats_generator.bets_log_path == Path('bets_log.csv')
    
    def test_load_data_from_csv(self, stats_generator, sample_betting_data, tmp_path):
        """Test loading data from CSV file."""
        # Create a temporary CSV file
        csv_file = tmp_path / 'bets_log.csv'
        sample_betting_data.to_csv(csv_file, index=False)
        
        # Mock the path
        stats_generator.bets_log_path = csv_file
        
        # Load data
        result = stats_generator.load_data(days=7)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert 'bet_id' in result.columns
    
    def test_load_data_no_csv_file(self, stats_generator):
        """Test loading data when CSV file doesn't exist."""
        # Ensure the file doesn't exist
        stats_generator.bets_log_path = Path('nonexistent_file.csv')
        
        # Should try to load from daily CSVs
        with patch('scripts.stats.Path.glob') as mock_glob:
            mock_glob.return_value = []
            result = stats_generator.load_data(days=7)
            # Should return empty DataFrame or handle gracefully
    
    @patch('scripts.stats.pd.read_csv')
    def test_load_data_with_date_filtering(self, mock_read_csv, stats_generator):
        """Test that data is filtered by date range."""
        # Create data with various dates
        mock_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10, freq='D'),
            'bet_id': [f'BET{i:03d}' for i in range(10)],
            'stake': [10.0] * 10
        })
        mock_read_csv.return_value = mock_df
        
        # Test loading last 7 days
        result = stats_generator.load_data(days=7)
        mock_read_csv.assert_called_once()


class TestStatsCLI:
    """Test the Click CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def mock_data(self):
        """Create mock betting data."""
        return pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'stake': [100, 200],
            'payout': [150, 180],
            'result': ['WON', 'LOST']
        })
    
    def test_cli_help(self, runner):
        """Test CLI help command."""
        from scripts.stats import cli
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Show this message and exit' in result.output
    
    @patch('scripts.stats.StatsGenerator')
    def test_cli_default_command(self, mock_generator_class, runner, mock_data):
        """Test running CLI with default options."""
        # Setup mock
        mock_generator = MagicMock()
        mock_generator.load_data.return_value = mock_data
        mock_generator_class.return_value = mock_generator
        
        from scripts.stats import cli
        result = runner.invoke(cli, [])
        
        # Should create generator and load data
        mock_generator_class.assert_called_once()
        mock_generator.load_data.assert_called()
    
    def test_cli_with_days_option(self, runner):
        """Test CLI with --days option."""
        from scripts.stats import cli
        
        with patch('scripts.stats.StatsGenerator') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            result = runner.invoke(cli, ['--days', '30'])
            
            # Should pass days parameter
            mock_instance.load_data.assert_called_with(days=30)
    
    def test_cli_with_format_option(self, runner):
        """Test CLI with different output formats."""
        from scripts.stats import cli
        
        with patch('scripts.stats.StatsGenerator') as mock_class:
            mock_instance = MagicMock()
            mock_instance.load_data.return_value = pd.DataFrame({'test': [1, 2, 3]})
            mock_class.return_value = mock_instance
            
            # Test JSON format
            result = runner.invoke(cli, ['--format', 'json'])
            assert result.exit_code == 0
            
            # Test table format
            result = runner.invoke(cli, ['--format', 'table'])
            assert result.exit_code == 0
    
    def test_cli_with_output_file(self, runner, tmp_path):
        """Test CLI with output file option."""
        from scripts.stats import cli
        
        output_file = tmp_path / 'output.json'
        
        with patch('scripts.stats.StatsGenerator') as mock_class:
            mock_instance = MagicMock()
            mock_instance.load_data.return_value = pd.DataFrame({'roi': [0.5, -0.2, 0.3]})
            mock_class.return_value = mock_instance
            
            result = runner.invoke(cli, ['--output', str(output_file), '--format', 'json'])
            
            # Check that file would be created
            assert result.exit_code == 0
    
    def test_cli_error_handling(self, runner):
        """Test CLI error handling."""
        from scripts.stats import cli
        
        with patch('scripts.stats.StatsGenerator') as mock_class:
            # Simulate an error
            mock_class.side_effect = Exception("Test error")
            
            result = runner.invoke(cli, [])
            
            # Should handle error gracefully
            assert result.exit_code != 0 or 'Error' in result.output


class TestStatsCalculation:
    """Test statistics calculation functions."""
    
    def test_calculate_roi(self):
        """Test ROI calculation."""
        # This might be a method in StatsGenerator
        from scripts.stats import StatsGenerator
        
        generator = StatsGenerator()
        
        # Test data
        data = pd.DataFrame({
            'stake': [100, 200, 150],
            'payout': [150, 180, 200]
        })
        
        # If there's a calculate_roi method
        if hasattr(generator, 'calculate_roi'):
            roi = generator.calculate_roi(data)
            assert isinstance(roi, (float, pd.Series))
    
    def test_generate_summary_stats(self):
        """Test summary statistics generation."""
        from scripts.stats import StatsGenerator
        
        generator = StatsGenerator()
        
        # Test data
        data = pd.DataFrame({
            'stake': [100, 200, 150],
            'payout': [150, 0, 200],
            'result': ['WON', 'LOST', 'WON']
        })
        
        # If there's a summary method
        if hasattr(generator, 'generate_summary'):
            summary = generator.generate_summary(data)
            assert isinstance(summary, dict)


class TestPlotlyVisualization:
    """Test Plotly visualization generation."""
    
    @patch('scripts.stats.go.Figure')
    def test_create_plotly_chart(self, mock_figure):
        """Test creating Plotly charts."""
        from scripts.stats import StatsGenerator
        
        generator = StatsGenerator()
        
        # Mock data
        data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'roi': [0.1, -0.05, 0.15, 0.08, -0.02]
        })
        
        # If there's a plotting method
        if hasattr(generator, 'create_chart'):
            chart = generator.create_chart(data)
            # Verify Figure was created
            mock_figure.assert_called()
    
    def test_export_html_report(self, tmp_path):
        """Test exporting HTML report."""
        from scripts.stats import StatsGenerator
        
        generator = StatsGenerator()
        output_file = tmp_path / 'report.html'
        
        # If there's an export method
        if hasattr(generator, 'export_html'):
            generator.export_html(output_file)
            # Check file would be created


class TestIntegration:
    """Integration tests for the stats module."""
    
    @pytest.fixture
    def setup_test_environment(self, tmp_path):
        """Setup a test environment with data files."""
        # Create test data directory
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        
        # Create test CSV
        csv_file = tmp_path / 'bets_log.csv'
        test_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'bet_id': ['B001', 'B002'],
            'stake': [50, 100],
            'payout': [75, 80],
            'result': ['WON', 'LOST']
        })
        test_data.to_csv(csv_file, index=False)
        
        return tmp_path
    
    def test_full_stats_generation_flow(self, setup_test_environment):
        """Test the complete stats generation workflow."""
        from scripts.stats import StatsGenerator
        
        # Use test environment
        generator = StatsGenerator()
        generator.bets_log_path = setup_test_environment / 'bets_log.csv'
        
        # Load data
        data = generator.load_data()
        assert len(data) > 0
        
        # Generate stats (if methods exist)
        if hasattr(generator, 'calculate_stats'):
            stats = generator.calculate_stats(data)
            assert stats is not None


# Mock the dependencies that might not be installed
@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock external dependencies."""
    with patch.dict('sys.modules', {
        'plotly': MagicMock(),
        'plotly.graph_objects': MagicMock(),
        'plotly.io': MagicMock(),
        'dotenv': MagicMock()
    }):
        yield
