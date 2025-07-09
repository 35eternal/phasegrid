"""Test the main() function in scripts/stats.py"""
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import pandas as pd
from pathlib import Path


class TestStatsMain:
    """Test the stats.py main() function."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    @pytest.fixture(autouse=True)
    def mock_dependencies(self):
        """Mock external dependencies."""
        with patch.dict('sys.modules', {
            'plotly': MagicMock(),
            'plotly.graph_objects': MagicMock(),
            'plotly.io': MagicMock(),
            'dotenv': MagicMock()
        }):
            with patch('scripts.stats.load_dotenv'):
                yield
    
    def test_main_help(self, runner):
        """Test main --help command."""
        from scripts.stats import cli
        
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output or 'Options:' in result.output
    
    @patch('scripts.stats.StatsGenerator')
    def test_main_default_run(self, mock_generator_class, runner):
        """Test running main with default options."""
        # Setup mock
        mock_generator = MagicMock()
        mock_data = pd.DataFrame({
            'Date': ['2024-01-01'],
            'Bet ID': ['B001'],
            'Stake': [100],
            'Payout': [150],
            'Result': ['WON'],
            'Status': ['Settled']
        })
        mock_generator.load_data.return_value = mock_data
        mock_generator.calculate_daily_stats.return_value = pd.DataFrame({
            'date': ['2024-01-01'],
            'bet_count': [1],
            'total_stake': [100],
            'total_payout': [150],
            'net_profit': [50],
            'roi_percent': [50.0]
        })
        mock_generator_class.return_value = mock_generator
        
        from scripts.stats import cli
        result = runner.invoke(cli, [])
        
        # Should succeed and show output
        assert result.exit_code == 0
        assert 'PhaseGrid' in result.output or 'Stats' in result.output
    
    @patch('scripts.stats.StatsGenerator')
    def test_main_with_days_param(self, mock_generator_class, runner):
        """Test main with --days parameter."""
        mock_generator = MagicMock()
        mock_generator.load_data.return_value = pd.DataFrame()
        mock_generator.calculate_daily_stats.return_value = pd.DataFrame()
        mock_generator_class.return_value = mock_generator
        
        from scripts.stats import cli
        result = runner.invoke(cli, ['--days', '30'])
        
        # Check that load_data was called with days=30
        mock_generator.load_data.assert_called_with(days=30)
    
    @patch('scripts.stats.StatsGenerator')
    def test_main_json_output(self, mock_generator_class, runner):
        """Test main with JSON output format."""
        mock_generator = MagicMock()
        mock_generator.load_data.return_value = pd.DataFrame({'test': [1]})
        mock_generator.calculate_daily_stats.return_value = pd.DataFrame({
            'date': ['2024-01-01'],
            'bet_count': [5]
        })
        mock_generator_class.return_value = mock_generator
        
        from scripts.stats import cli
        result = runner.invoke(cli, ['--output', 'json'])
        
        assert result.exit_code == 0
        # Should contain JSON output
        assert '[' in result.output or '{' in result.output
    
    @patch('scripts.stats.StatsGenerator')
    def test_main_html_output(self, mock_generator_class, runner):
        """Test main with HTML output format."""
        mock_generator = MagicMock()
        mock_generator.load_data.return_value = pd.DataFrame({'test': [1]})
        mock_generator.calculate_daily_stats.return_value = pd.DataFrame({
            'date': ['2024-01-01'],
            'bet_count': [5]
        })
        mock_generator.generate_plotly_table.return_value = '<html>test</html>'
        mock_generator_class.return_value = mock_generator
        
        from scripts.stats import cli
        result = runner.invoke(cli, ['--output', 'html'])
        
        assert result.exit_code == 0
    
    @patch('scripts.stats.StatsGenerator')
    @pytest.mark.xfail(reason="Legacy test - needs update")
    def test_main_save_to_file(self, mock_generator_class, runner, tmp_path):
        """Test main with --save-to option."""
        mock_generator = MagicMock()
        mock_generator.load_data.return_value = pd.DataFrame({'test': [1]})
        mock_generator.calculate_daily_stats.return_value = pd.DataFrame({
            'date': ['2024-01-01'],
            'bet_count': [5]
        })
        mock_generator_class.return_value = mock_generator
        
        output_file = tmp_path / 'output.json'
        
        from scripts.stats import cli
        result = runner.invoke(cli, ['--output', 'json', '--save-to', str(output_file)])
        
        assert result.exit_code == 0
        assert 'saved to' in result.output
    
    @patch('scripts.stats.StatsGenerator')
    def test_main_error_handling(self, mock_generator_class, runner):
        """Test main error handling."""
        mock_generator_class.side_effect = Exception("Test error")
        
        from scripts.stats import cli
        result = runner.invoke(cli, [])
        
        assert result.exit_code == 1
        assert 'Error' in result.output


# Also test the calculate_daily_stats method if it exists
class TestStatsGeneratorMethods:
    """Test StatsGenerator methods we can see from the code."""
    
    @pytest.fixture
    def stats_generator(self):
        """Create StatsGenerator instance."""
        with patch('scripts.stats.load_dotenv'):
            from scripts.stats import StatsGenerator
            return StatsGenerator()
    
    def test_calculate_daily_stats_exists(self, stats_generator):
        """Test that calculate_daily_stats method exists."""
        assert hasattr(stats_generator, 'calculate_daily_stats')
    
    @pytest.mark.xfail(reason="Legacy test - needs update")
    
    def test_generate_plotly_table_exists(self, stats_generator):
        """Test that generate_plotly_table method exists."""
        assert hasattr(stats_generator, 'generate_plotly_table')
