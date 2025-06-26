"""Fixed tests for phasegrid CLI module based on actual implementation."""
import pytest
from unittest.mock import patch, MagicMock, Mock
import argparse
from phasegrid import cli


class TestPhaseGridCLIFixed:
    """Test the CLI functionality with correct implementation."""
    
    def test_cli_main_function_exists(self):
        """Test that main function exists in CLI."""
        assert hasattr(cli, 'main')
        assert callable(cli.main)
    
    def test_cli_setup_logging(self):
        """Test setup_logging function."""
        assert hasattr(cli, 'setup_logging')
        # Call with default level
        cli.setup_logging('INFO')
        # Just verify it doesn't crash
    
    def test_cli_create_parser(self):
        """Test create_parser function."""
        assert hasattr(cli, 'create_parser')
        parser = cli.create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
    
    def test_cli_process_command_exists(self):
        """Test process_command function exists."""
        assert hasattr(cli, 'process_command')
        assert callable(cli.process_command)
    
    def test_cli_stats_command_exists(self):
        """Test stats_command function exists."""
        assert hasattr(cli, 'stats_command')
        assert callable(cli.stats_command)
    
    def test_cli_config_command_exists(self):
        """Test config_command function exists."""
        assert hasattr(cli, 'config_command')
        assert callable(cli.config_command)
    
    @patch('phasegrid.cli.create_parser')
    def test_cli_main_with_mock_parser(self, mock_create_parser):
        """Test main function with mocked parser."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser
        
        with patch('phasegrid.cli.process_command') as mock_process:
            cli.main()
            mock_create_parser.assert_called_once()
            mock_parser.parse_args.assert_called_once()