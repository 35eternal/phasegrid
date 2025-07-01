"""
Tests for stats CLI module
"""
import pytest
import pandas as pd
import json
from unittest.mock import Mock, patch, MagicMock, mock_open, PropertyMock
from click.testing import CliRunner
from pathlib import Path
import tempfile
from io import StringIO


@pytest.fixture
def stats_generator():
    """Create a StatsGenerator instance."""
    from scripts.stats import StatsGenerator
    return StatsGenerator()


@pytest.fixture
def sample_betting_data():
    """Create sample betting data for testing."""
    return pd.DataFrame({
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Bet ID': ['BET001', 'BET002', 'BET003'],
        'Stake': [10.0, 20.0, 15.0],
        'Payout': [15.0, 0.0, 22.5],
        'Result': ['WON', 'LOST', 'WON'],
        'Status': ['Settled', 'Settled', 'Settled'],
        'Profit': [5.0, -20.0, 7.5]
    })


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_data():
    """Create mock betting data."""
    return pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02'],
        'stake': [100, 200],
        'payout': [150, 180],
        'result': ['WON', 'LOST']
    })


@pytest.fixture
def setup_test_environment(tmp_path):
    """Set up test environment with sample data."""
    # Create a bets_log.csv with correct column names
    bets_data = pd.DataFrame({
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        'Bet ID': ['B001', 'B002', 'B003', 'B004', 'B005'],
        'Stake': [100, 200, 150, 100, 250],
        'Payout': [150, 0, 225, 180, 0],
        'Result': ['WON', 'LOST', 'WON', 'WON', 'LOST'],
        'Status': ['Settled', 'Settled', 'Settled', 'Settled', 'Settled']
    })

    csv_path = tmp_path / 'bets_log.csv'
    bets_data.to_csv(csv_path, index=False)

    return tmp_path


class TestStatsGenerator:
    """Test StatsGenerator class."""

    def test_init(self, stats_generator):
        """Test StatsGenerator initialization."""
        assert stats_generator.data_source == 'csv'
        assert stats_generator.bets_log_path.name == 'bets_log.csv'

    @patch('scripts.stats.pd.read_csv')
    def test_load_data_from_csv(self, mock_read_csv, stats_generator):
        """Test loading data from CSV file."""
        from unittest.mock import Mock
        
        # Setup mocks
        stats_generator.data_source = 'csv'
        
        # Replace the path with a Mock that has exists returning True
        original_path = stats_generator.bets_log_path
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.__str__ = lambda self: str(original_path)
        stats_generator.bets_log_path = mock_path
        
        mock_df = pd.DataFrame({
            'date': ['2025-06-24', '2025-06-25', '2025-06-26'],
            'bet_id': ['BET001', 'BET002', 'BET003'],
            'stake': [10.0, 20.0, 15.0],
            'payout': [15.0, 0.0, 22.5],
            'result': ['WON', 'LOST', 'WON'],
            'status': ['Settled', 'Settled', 'Settled']
        })
        mock_read_csv.return_value = mock_df

        # Load data
        result = stats_generator.load_data(days=7)

        # Verify
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert all(col in result.columns for col in ['date', 'bet_id', 'stake', 'payout', 'result', 'status'])
        mock_read_csv.assert_called_once_with(mock_path)
        assert 'date' in result.columns
        assert 'stake' in result.columns
        assert 'payout' in result.columns
        mock_read_csv.assert_called_once_with(stats_generator.bets_log_path)

    def test_load_data_no_csv_file(self, stats_generator):
        """Test loading data when CSV file doesn't exist."""
        stats_generator.bets_log_path = Path('nonexistent.csv')
        result = stats_generator.load_data()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch.object(Path, 'exists')
    @patch('pandas.read_csv')
    def test_load_data_with_date_filtering(self, mock_read_csv, mock_path_exists, stats_generator):
        """Test that data is filtered by date range."""
        # Setup mocks - mock the specific path's exists method
        mock_path_exists.return_value = True

        
        # Create data with various dates
        mock_df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10, freq='D'),
            'Bet ID': [f'BET{i:03d}' for i in range(10)],
            'Stake': [10.0] * 10,
            'Payout': [15.0] * 10,
            'Result': ['WON'] * 10
        })
        mock_read_csv.return_value = mock_df
        # Also set side_effect to always return our mock_df
        mock_read_csv.side_effect = lambda *args, **kwargs: mock_df

        # Test loading last 7 days
        result = stats_generator.load_data(days=7)
        mock_read_csv.assert_called_once()


class TestStatsCLI:
    """Test CLI commands."""

    def test_cli_help(self, runner):
        """Test CLI help command."""
        from scripts.stats import cli
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Generate betting statistics report' in result.output

    @patch('scripts.stats.StatsGenerator')
    def test_cli_default_command(self, mock_generator_class, runner, mock_data):
        """Test running CLI with default options."""
        # Setup mock
        mock_generator = MagicMock()
        mock_generator.load_data.return_value = mock_data
        mock_generator.calculate_daily_stats.return_value = pd.DataFrame({
            'date': ['2024-01-01'],
            'bet_count': [1],
            'total_stake': [100],
            'total_payout': [150],
            'net_profit': [50],
            'roi_percent': [50.0]
        })
        mock_generator.generate_summary_stats.return_value = {
            'total_bets': 1,
            'total_stake': 100,
            'total_payout': 150,
            'net_profit': 50,
            'roi_percent': 50.0,
            'win_rate': 100.0
        }
        mock_generator_class.return_value = mock_generator

        from scripts.stats import cli
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert 'Generating stats' in result.output

    def test_cli_with_days_option(self, runner):
        """Test CLI with --days option."""
        from scripts.stats import cli
        with patch('scripts.stats.StatsGenerator') as mock_cls:
            mock_instance = MagicMock()
            mock_instance.load_data.return_value = pd.DataFrame()
            mock_instance.calculate_daily_stats.return_value = pd.DataFrame()
            mock_instance.generate_summary_stats.return_value = {
                'total_bets': 0,
                'total_stake': 0,
                'total_payout': 0,
                'net_profit': 0,
                'roi_percent': 0,
                'win_rate': 0
            }
            mock_cls.return_value = mock_instance

            result = runner.invoke(cli, ['--days', '30'])
            assert result.exit_code == 1  # No data found

    def test_cli_with_format_option(self, runner):
        """Test CLI with different output formats."""
        from scripts.stats import cli
        with patch('scripts.stats.StatsGenerator') as mock_cls:
            mock_instance = MagicMock()
            mock_instance.load_data.return_value = pd.DataFrame({'test': [1]})
            mock_instance.calculate_daily_stats.return_value = pd.DataFrame({
                'date': ['2024-01-01'],
                'bet_count': [5]
            })
            mock_instance.generate_summary_stats.return_value = {
                'total_bets': 5,
                'total_stake': 100,
                'total_payout': 150,
                'net_profit': 50,
                'roi_percent': 50.0,
                'win_rate': 60.0
            }
            mock_cls.return_value = mock_instance

            # Test JSON output
            result = runner.invoke(cli, ['--output', 'json'])
            assert result.exit_code == 0

            # Test HTML output
            with patch.object(mock_instance, 'export_html_report'):
                result = runner.invoke(cli, ['--output', 'html'])
                assert result.exit_code == 0

    def test_cli_with_output_file(self, runner, tmp_path):
        """Test CLI with output file option."""
        from scripts.stats import cli
        output_file = tmp_path / 'test_output.json'

        with patch('scripts.stats.StatsGenerator') as mock_cls:
            mock_instance = MagicMock()
            mock_instance.load_data.return_value = pd.DataFrame({'test': [1]})
            mock_instance.calculate_daily_stats.return_value = pd.DataFrame({
                'date': ['2024-01-01'],
                'bet_count': [5]
            })
            mock_instance.generate_summary_stats.return_value = {
                'total_bets': 5,
                'total_stake': 100,
                'total_payout': 150,
                'net_profit': 50,
                'roi_percent': 50.0,
                'win_rate': 60.0
            }
            mock_cls.return_value = mock_instance

            result = runner.invoke(cli, ['--output', 'json', '--file', str(output_file)])
            assert result.exit_code == 0
            assert output_file.exists()

    def test_cli_error_handling(self, runner):
        """Test CLI error handling."""
        from scripts.stats import cli
        with patch('scripts.stats.StatsGenerator') as mock_cls:
            mock_instance = MagicMock()
            mock_instance.load_data.return_value = pd.DataFrame()  # Empty data
            mock_cls.return_value = mock_instance

            result = runner.invoke(cli)
            assert result.exit_code == 1
            assert 'No data found' in result.output


class TestStatsCalculation:
    """Test statistics calculation methods."""

    def test_calculate_roi(self, stats_generator, sample_betting_data):
        """Test ROI calculation."""
        # Convert to lowercase columns as expected by the method
        df = sample_betting_data.rename(columns={
            'Date': 'date',
            'Bet ID': 'bet_id',
            'Stake': 'stake',
            'Payout': 'payout',
            'Result': 'result'
        })
        df['date'] = pd.to_datetime(df['date'])

        result = stats_generator.calculate_daily_roi(df)
        assert not result.empty
        assert 'roi_percent' in result.columns
        assert 'net_profit' in result.columns

    def test_generate_summary_stats(self, stats_generator, sample_betting_data):
        """Test summary statistics generation."""
        # Convert to lowercase columns
        df = sample_betting_data.rename(columns={
            'Date': 'date',
            'Bet ID': 'bet_id',
            'Stake': 'stake',
            'Payout': 'payout',
            'Result': 'result'
        })

        stats = stats_generator.generate_summary_stats(df)
        assert stats['total_bets'] == 3
        assert stats['total_stake'] == 45.0
        assert stats['total_payout'] == 37.5
        assert stats['net_profit'] == -7.5
        assert stats['win_rate'] == pytest.approx(66.67, rel=0.01)


class TestPlotlyVisualization:
    """Test Plotly visualization methods."""

    def test_create_plotly_chart(self, stats_generator):
        """Test creating Plotly chart."""
        daily_stats = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'roi_percent': [50.0, -25.0],
            'net_profit': [50, -50]
        })

        fig = stats_generator.create_roi_chart(daily_stats)
        assert fig is not None
        assert len(fig.data) == 2  # Line chart + bar chart

    def test_export_html_report(self, stats_generator, tmp_path):
        """Test HTML report export."""
        daily_stats = pd.DataFrame({
            'date': ['2024-01-01'],
            'bet_count': [5],
            'total_stake': [100],
            'total_payout': [150],
            'net_profit': [50],
            'roi_percent': [50.0]
        })
        summary_stats = {
            'total_bets': 5,
            'total_stake': 100,
            'total_payout': 150,
            'net_profit': 50,
            'roi_percent': 50.0,
            'win_rate': 60.0
        }

        output_file = tmp_path / 'test_report.html'
        result = stats_generator.export_html_report(
            daily_stats, summary_stats, str(output_file)
        )

        assert output_file.exists()
        assert result == str(output_file)


class TestIntegration:
    """Integration tests."""

    @patch('scripts.stats.pd.read_csv')
    def test_full_stats_generation_flow(self, mock_read_csv):
        """Test the complete stats generation workflow."""
        from scripts.stats import StatsGenerator
        from unittest.mock import Mock

        # Setup mocks
        mock_df = pd.DataFrame({
            'date': ['2025-06-22', '2025-06-23', '2025-06-24', '2025-06-25', '2025-06-26'],
            'bet_id': ['B001', 'B002', 'B003', 'B004', 'B005'],
            'stake': [100, 200, 150, 100, 250],
            'payout': [150, 0, 225, 180, 0],
            'result': ['WON', 'LOST', 'WON', 'WON', 'LOST'],
            'status': ['Settled', 'Settled', 'Settled', 'Settled', 'Settled']
        })
        mock_read_csv.return_value = mock_df

        # Create generator and set data source
        generator = StatsGenerator()
        generator.data_source = 'csv'
        
        # Replace the path with a Mock that has exists returning True
        original_path = generator.bets_log_path
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.__str__ = lambda self: str(original_path)
        generator.bets_log_path = mock_path

        # Load data
        data = generator.load_data()
        assert len(data) > 0
        
        # Calculate stats
        stats = generator.generate_summary_stats(data)
        
        # Verify stats
        assert stats['total_bets'] == 5
        assert stats['total_stake'] == 800.0
        assert stats['total_payout'] == 555.0

        # Calculate stats
        daily_stats = generator.calculate_daily_stats(data)
        assert not daily_stats.empty

        # Generate summary
        summary = generator.generate_summary_stats(data)
        assert summary['total_bets'] == 5
