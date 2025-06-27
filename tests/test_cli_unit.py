"""
Unit tests for CLI module to boost coverage
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import argparse
from phasegrid import cli


class TestCLIFunctions:
    """Test individual CLI functions."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        with patch('logging.basicConfig') as mock_config:
            cli.setup_logging('DEBUG')
            mock_config.assert_called_once()
            
    def test_create_parser(self):
        """Test parser creation."""
        parser = cli.create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        
        # Test parsing process command
        args = parser.parse_args(['process', '--date', '2024-01-01'])
        assert args.command == 'process'
        assert args.date == '2024-01-01'
        
        # Test parsing verify command
        args = parser.parse_args(['verify', '--sheet', 'test_sheet'])
        assert args.command == 'verify'
        assert args.sheet == 'test_sheet'
        
        # Test parsing optimize command
        args = parser.parse_args(['optimize', '--bankroll', '5000'])
        assert args.command == 'optimize'
        assert args.bankroll == 5000.0
    
    @patch('phasegrid.cli.SlipProcessor')
    def test_process_data(self, mock_processor_class):
        """Test process_data function."""
        mock_processor = Mock()
        mock_processor.process.return_value = [{'slip': 1}, {'slip': 2}]
        mock_processor_class.return_value = mock_processor
        
        props = [{'prop': 'test'}]
        result = cli.process_data(props, '2024-01-01', bypass_guard_rail=True)
        
        assert len(result) == 2
        assert mock_processor.process.called
        
    @patch('phasegrid.cli.SheetVerifier')
    def test_verify_sheets(self, mock_verifier_class):
        """Test verify_sheets function."""
        mock_verifier = Mock()
        mock_verifier.verify_sheet.return_value = []
        mock_verifier_class.return_value = mock_verifier
        
        result = cli.verify_sheets('test_sheet')
        assert result is True
        
        # Test with errors
        mock_verifier.verify_sheet.return_value = ['Error 1', 'Error 2']
        result = cli.verify_sheets('test_sheet', fix=True)
        assert result is False
    
    def test_optimize_slips(self):
        """Test optimize_slips function."""
        with patch('phasegrid.cli.SlipOptimizer'):
            # Test conservative
            params = cli.optimize_slips(1000, 'conservative')
            assert params['bankroll'] == 1000
            assert params['max_bet_pct'] == 0.02
            assert params['min_edge'] == 0.10
            
            # Test aggressive
            params = cli.optimize_slips(5000, 'aggressive')
            assert params['bankroll'] == 5000
            assert params['max_bet_pct'] == 0.10
            assert params['min_edge'] == 0.03
            
            # Test moderate (default)
            params = cli.optimize_slips(2000, 'moderate')
            assert params['bankroll'] == 2000
            assert params['max_bet_pct'] == 0.05
            assert params['min_edge'] == 0.05
    
    @patch('phasegrid.cli.process_data')
    @patch('builtins.open', create=True)
    @patch('json.dump')
    @patch('json.load')
    def test_process_command_process(self, mock_load, mock_dump, mock_open, mock_process_data):
        """Test process_command with process command."""
        mock_load.return_value = [{'prop': 'test'}]
        mock_process_data.return_value = [{'slip': 1}]
        
        args = Mock()
        args.command = 'process'
        args.props_file = 'props.json'
        args.date = '2024-01-01'
        args.bypass_guard_rail = False
        args.output = 'output.json'
        args.log_level = 'INFO'
        
        with patch('sys.exit'):
            cli.process_command(args)
        
        mock_process_data.assert_called_once()
        mock_dump.assert_called_once()
    
    @patch('phasegrid.cli.verify_sheets')
    def test_process_command_verify(self, mock_verify):
        """Test process_command with verify command."""
        mock_verify.return_value = True
        
        args = Mock()
        args.command = 'verify'
        args.sheet = 'test_sheet'
        args.fix = False
        
        with patch('sys.exit') as mock_exit:
            cli.process_command(args)
            mock_exit.assert_called_with(0)
    
    @patch('phasegrid.cli.optimize_slips')
    def test_process_command_optimize(self, mock_optimize):
        """Test process_command with optimize command."""
        mock_optimize.return_value = {'test': 'params'}
        
        args = Mock()
        args.command = 'optimize'
        args.bankroll = 1000
        args.risk_level = 'moderate'
        
        cli.process_command(args)
        mock_optimize.assert_called_once_with(1000, 'moderate')
    
    def test_process_command_no_command(self):
        """Test process_command with no command."""
        args = Mock()
        args.command = None
        
        with patch('sys.exit') as mock_exit:
            cli.process_command(args)
            mock_exit.assert_called_with(1)
    
    @patch('phasegrid.cli.create_parser')
    @patch('phasegrid.cli.setup_logging')
    @patch('phasegrid.cli.process_command')
    def test_main(self, mock_process, mock_logging, mock_parser):
        """Test main function."""
        mock_args = Mock()
        mock_args.log_level = 'INFO'
        mock_parser_instance = Mock()
        mock_parser_instance.parse_args.return_value = mock_args
        mock_parser.return_value = mock_parser_instance
        
        cli.main()
        
        mock_parser.assert_called_once()
        mock_logging.assert_called_once_with('INFO')
        mock_process.assert_called_once_with(mock_args)
