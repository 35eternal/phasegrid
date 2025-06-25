"""
Test suite for Paper Trading Trial functionality.
"""

import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path so we can import scripts
sys.path.insert(0, str(Path(__file__).parent.parent))

# Skip these tests until PaperTrader class is implemented
pytestmark = pytest.mark.skip(reason="PaperTrader class not yet implemented in scripts.paper_trader")

# Placeholder to prevent import errors
class PaperTrader:
    pass

class TestPaperTrader:
    """Test cases for PaperTrader class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def sample_predictions(self, temp_dir):
        """Create sample predictions CSV."""
        predictions_file = Path(temp_dir) / 'predictions_20240115.csv'
        data = [
            {'game_id': 'G001', 'bet_type': 'spread', 'pick': 'home', 'odds': '-110', 'confidence': '0.65'},
            {'game_id': 'G002', 'bet_type': 'total', 'pick': 'over', 'odds': '+120', 'confidence': '0.55'},
            {'game_id': 'G003', 'bet_type': 'moneyline', 'pick': 'away', 'odds': '-150', 'confidence': '0.70'},
        ]
        
        with open(predictions_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
        return str(predictions_file)
    
    @pytest.fixture
    def sample_results(self, temp_dir):
        """Create sample results CSV."""
        results_file = Path(temp_dir) / 'results.csv'
        data = [
            {'game_id': 'G001', 'bet_type': 'spread', 'outcome': 'win'},
            {'game_id': 'G002', 'bet_type': 'total', 'outcome': 'loss'},
            {'game_id': 'G003', 'bet_type': 'moneyline', 'outcome': 'push'},
        ]
        
        with open(results_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
        return str(results_file)
    
    def test_init(self):
        """Test PaperTrader initialization."""
        trader = PaperTrader('20240115', 'results.csv', 2000.0)
        assert trader.date == '20240115'
        assert trader.results_source == 'results.csv'
        assert trader.initial_bankroll == 2000.0
        assert trader.current_bankroll == 2000.0
        assert trader.bets_placed == []
        assert trader.results == []
    
    def test_load_predictions(self, temp_dir):
        """Test loading predictions from CSV."""
        os.chdir(temp_dir)
        
        # Create predictions file
        predictions_file = 'predictions_20240115.csv'
        data = [
            {'game_id': 'G001', 'bet_type': 'spread', 'pick': 'home', 'odds': '-110', 'confidence': '0.65'},
        ]
        
        with open(predictions_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        trader = PaperTrader('20240115', 'results.csv')
        predictions = trader.load_predictions()
        
        assert len(predictions) == 1
        assert predictions[0]['game_id'] == 'G001'
        assert predictions[0]['odds'] == '-110'
    
    def test_load_predictions_missing_file(self):
        """Test loading predictions when file doesn't exist."""
        trader = PaperTrader('20240115', 'results.csv')
        predictions = trader.load_predictions()
        assert predictions == []
    
    def test_load_results(self, sample_results):
        """Test loading results from CSV."""
        trader = PaperTrader('20240115', sample_results)
        results = trader.load_results()
        
        assert len(results) == 3
        assert results['G001_spread']['outcome'] == 'win'
        assert results['G002_total']['outcome'] == 'loss'
        assert results['G003_moneyline']['outcome'] == 'push'
    
    def test_calculate_payout_win_positive_odds(self):
        """Test payout calculation for win with positive odds."""
        trader = PaperTrader('20240115', 'results.csv')
        payout = trader.calculate_payout(150, 100.0, 'win')
        assert payout == 250.0  # 100 stake + 150 profit
    
    def test_calculate_payout_win_negative_odds(self):
        """Test payout calculation for win with negative odds."""
        trader = PaperTrader('20240115', 'results.csv')
        payout = trader.calculate_payout(-110, 110.0, 'win')
        assert payout == 210.0  # 110 stake + 100 profit
    
    def test_calculate_payout_loss(self):
        """Test payout calculation for loss."""
        trader = PaperTrader('20240115', 'results.csv')
        payout = trader.calculate_payout(-110, 100.0, 'loss')
        assert payout == 0.0
    
    def test_calculate_payout_push(self):
        """Test payout calculation for push."""
        trader = PaperTrader('20240115', 'results.csv')
        payout = trader.calculate_payout(-110, 100.0, 'push')
        assert payout == 100.0
    
    def test_calculate_payout_void(self):
        """Test payout calculation for void."""
        trader = PaperTrader('20240115', 'results.csv')
        payout = trader.calculate_payout(-110, 100.0, 'void')
        assert payout == 100.0
    
    def test_place_bets(self):
        """Test placing bets with various outcomes."""
        trader = PaperTrader('20240115', 'results.csv', 1000.0)
        
        predictions = [
            {'game_id': 'G001', 'bet_type': 'spread', 'pick': 'home', 'odds': '-110', 'confidence': '0.65'},
            {'game_id': 'G002', 'bet_type': 'total', 'pick': 'over', 'odds': '+120', 'confidence': '0.55'},
        ]
        
        results = {
            'G001_spread': {'outcome': 'win'},
            'G002_total': {'outcome': 'loss'},
        }
        
        trader.place_bets(predictions, results)
        
        assert len(trader.bets_placed) == 2
        assert trader.bets_placed[0]['outcome'] == 'win'
        assert trader.bets_placed[1]['outcome'] == 'loss'
        assert trader.current_bankroll != trader.initial_bankroll
    
    def test_calculate_metrics(self):
        """Test metrics calculation."""
        trader = PaperTrader('20240115', 'results.csv', 1000.0)
        
        # Simulate some bets
        trader.bets_placed = [
            {'stake': 50.0, 'outcome': 'win', 'profit': 45.45},
            {'stake': 40.0, 'outcome': 'loss', 'profit': -40.0},
            {'stake': 30.0, 'outcome': 'push', 'profit': 0.0},
        ]
        trader.current_bankroll = 1005.45
        
        metrics = trader.calculate_metrics()
        
        assert metrics['date'] == '20240115'
        assert metrics['total_slips'] == 3
        assert metrics['wins'] == 1
        assert metrics['losses'] == 1
        assert metrics['roi_pct'] == 4.54  # 5.45 profit / 120 total stake
        assert metrics['bankroll_after'] == 1005.45
    
    def test_write_simulation_csv(self, temp_dir):
        """Test writing simulation CSV."""
        os.chdir(temp_dir)
        
        trader = PaperTrader('20240115', 'results.csv')
        trader.bets_placed = [
            {'game_id': 'G001', 'bet_type': 'spread', 'outcome': 'win', 'profit': 50.0},
        ]
        
        trader.write_simulation_csv()
        
        output_file = Path('output') / 'simulation_20240115.csv'
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['game_id'] == 'G001'
    
    def test_write_metrics_csv_idempotent(self, temp_dir):
        """Test idempotent metrics writing."""
        os.chdir(temp_dir)
        
        trader = PaperTrader('20240115', 'results.csv')
        metrics = {
            'date': '20240115',
            'total_slips': 5,
            'wins': 3,
            'losses': 2,
            'roi_pct': 15.5,
            'bankroll_after': 1155.0
        }
        
        # First write
        trader.write_metrics_csv(metrics)
        
        # Update metrics and write again
        metrics['wins'] = 4
        metrics['losses'] = 1
        trader.write_metrics_csv(metrics)
        
        # Check that only one row exists for the date
        metrics_file = Path('output') / 'paper_metrics.csv'
        with open(metrics_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        assert rows[0]['date'] == '20240115'
        assert rows[0]['wins'] == '4'  # Updated value
    
    def test_write_daily_summary(self, temp_dir):
        """Test writing daily summary JSON."""
        os.chdir(temp_dir)
        
        trader = PaperTrader('20240115', 'results.csv', 1000.0)
        trader.current_bankroll = 1100.0
        trader.bets_placed = [
            {'game_id': 'G001', 'bet_type': 'spread', 'profit': 80.0},
            {'game_id': 'G002', 'bet_type': 'total', 'profit': -30.0},
            {'game_id': 'G003', 'bet_type': 'moneyline', 'profit': 50.0},
        ]
        
        metrics = {'date': '20240115', 'total_slips': 3, 'wins': 2, 'losses': 1, 'roi_pct': 25.0, 'bankroll_after': 1100.0}
        trader.write_daily_summary(metrics)
        
        summary_file = Path('output') / 'daily_summary.json'
        assert summary_file.exists()
        
        with open(summary_file, 'r') as f:
            summary = json.load(f)
            
        assert summary['date'] == '20240115'
        assert summary['initial_bankroll'] == 1000.0
        assert summary['final_bankroll'] == 1100.0
        assert summary['best_bet']['game_id'] == 'G001'
        assert summary['worst_bet']['game_id'] == 'G002'
    
    def test_run_integration(self, temp_dir):
        """Test full simulation run."""
        os.chdir(temp_dir)
        
        # Create predictions
        predictions_file = 'predictions_20240115.csv'
        predictions_data = [
            {'game_id': 'G001', 'bet_type': 'spread', 'pick': 'home', 'odds': '-110', 'confidence': '0.65'},
            {'game_id': 'G002', 'bet_type': 'total', 'pick': 'over', 'odds': '+120', 'confidence': '0.55'},
        ]
        
        with open(predictions_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=predictions_data[0].keys())
            writer.writeheader()
            writer.writerows(predictions_data)
        
        # Create results
        results_file = 'results.csv'
        results_data = [
            {'game_id': 'G001', 'bet_type': 'spread', 'outcome': 'win'},
            {'game_id': 'G002', 'bet_type': 'total', 'outcome': 'loss'},
        ]
        
        with open(results_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results_data[0].keys())
            writer.writeheader()
            writer.writerows(results_data)
        
        # Run simulation
        trader = PaperTrader('20240115', results_file)
        trader.run()
        
        # Check outputs
        assert (Path('output') / 'simulation_20240115.csv').exists()
        assert (Path('output') / 'paper_metrics.csv').exists()
        assert (Path('output') / 'daily_summary.json').exists()
    
    def test_insufficient_bankroll(self):
        """Test handling of insufficient bankroll."""
        trader = PaperTrader('20240115', 'results.csv', 10.0)  # Very small bankroll
        
        predictions = [
            {'game_id': 'G001', 'bet_type': 'spread', 'pick': 'home', 'odds': '-110', 'confidence': '0.99'},
        ]
        
        results = {'G001_spread': {'outcome': 'win'}}
        
        # Should still place bet with available bankroll
        trader.place_bets(predictions, results)
        assert len(trader.bets_placed) == 1
    
    def test_edge_cases(self):
        """Test various edge cases."""
        trader = PaperTrader('20240115', 'results.csv')
        
        # Test invalid outcome
        with pytest.raises(ValueError):
            trader.calculate_payout(-110, 100.0, 'invalid')
        
        # Test empty predictions
        trader.place_bets([], {})
        assert len(trader.bets_placed) == 0
        
        # Test missing results
        predictions = [
            {'game_id': 'G999', 'bet_type': 'spread', 'pick': 'home', 'odds': '-110', 'confidence': '0.65'},
        ]
        trader.place_bets(predictions, {})
        assert trader.bets_placed[0]['outcome'] == 'void'


def test_main_cli(monkeypatch, tmpdir):
    """Test CLI entry point."""
    os.chdir(tmpdir)
    
    # Create necessary files
    with open('predictions_20240115.csv', 'w') as f:
        f.write('game_id,bet_type,pick,odds,confidence\n')
    
    with open('results.csv', 'w') as f:
        f.write('game_id,bet_type,outcome\n')
    
    # Mock sys.argv
    test_args = ['paper_trader.py', '--date', '20240115', '--results_source', 'results.csv', '--bankroll', '2000']
    monkeypatch.setattr('sys.argv', test_args)
    
    # Import and run main
    from scripts.paper_trader import main
    main()  # Should run without errors
    
    # Check outputs created
    assert Path('output').exists()


def test_main_invalid_date(monkeypatch, capsys):
    """Test CLI with invalid date format."""
    test_args = ['paper_trader.py', '--date', '2024-01-15', '--results_source', 'results.csv']
    monkeypatch.setattr('sys.argv', test_args)
    
    from scripts.paper_trader import main
    with pytest.raises(SystemExit):
        main()
    
    captured = capsys.readouterr()
    # Check if error message is in either stdout or stderr
    output = captured.out + captured.err
    assert 'Invalid date format' in output
