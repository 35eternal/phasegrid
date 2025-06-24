#!/usr/bin/env python3
"""
Paper Trading Trial - Simulates betting performance using historical data.

This module provides functionality to backtest betting strategies by processing
historical bets and game results to calculate payouts and performance metrics.
"""

import argparse
import csv
import json
import logging
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Bet:
    """Represents a single bet with its properties."""
    game_id: str
    bet_type: str  # 'moneyline', 'spread', 'total'
    selection: str  # team name or 'over'/'under'
    odds: float
    stake: float
    
    @property
    def potential_payout(self) -> float:
        """Calculate potential payout including stake."""
        if self.odds > 0:
            return self.stake * (1 + self.odds / 100)
        else:
            return self.stake * (1 + 100 / abs(self.odds))


@dataclass
class GameResult:
    """Represents the result of a game."""
    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: str  # 'completed', 'void', etc.
    
    @property
    def winner(self) -> Optional[str]:
        """Determine the winner of the game."""
        if self.status != 'completed':
            return None
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return 'push'  # Tie game
    
    @property
    def total_score(self) -> int:
        """Calculate total score for over/under bets."""
        return self.home_score + self.away_score


@dataclass
class BetResult:
    """Result of evaluating a bet against game results."""
    bet: Bet
    result: str  # 'win', 'loss', 'push', 'void'
    payout: float
    profit: float


@dataclass
class PerformanceMetrics:
    """Summary performance metrics for the simulation."""
    total_bets: int
    wins: int
    losses: int
    pushes: int
    voids: int
    total_wagered: float
    total_payout: float
    net_profit: float
    roi: float  # Return on Investment percentage
    win_rate: float  # Win percentage (excluding pushes/voids)
    starting_bankroll: float
    ending_bankroll: float


class PaperTrader:
    """Simulates paper trading for sports betting."""
    
    def __init__(self, date: str, results_source: str, bankroll: float = 1000.0):
        """
        Initialize the PaperTrader.
        
        Args:
            date: Date for the simulation (YYYYMMDD format)
            results_source: Source of game results ('api' or 'csv')
            bankroll: Starting bankroll amount
        """
        self.date = date
        self.results_source = results_source
        self.bankroll = bankroll
        self.starting_bankroll = bankroll
        self.bets: List[Bet] = []
        self.game_results: Dict[str, GameResult] = {}
        self.bet_results: List[BetResult] = []
        
    def load_bets(self, filepath: Path) -> None:
        """
        Load bets from CSV file.
        
        Expected CSV format:
        game_id,bet_type,selection,odds,stake
        """
        logger.info(f"Loading bets from {filepath}")
        
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    bet = Bet(
                        game_id=row['game_id'].strip(),
                        bet_type=row['bet_type'].strip().lower(),
                        selection=row['selection'].strip(),
                        odds=float(row['odds']),
                        stake=float(row['stake'])
                    )
                    self.bets.append(bet)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid bet row: {row}, error: {e}")
                    
        logger.info(f"Loaded {len(self.bets)} bets")
        
    def load_results(self, filepath: Optional[Path] = None) -> None:
        """
        Load game results from CSV file or API.
        
        Expected CSV format:
        game_id,home_team,away_team,home_score,away_score,status
        """
        if self.results_source == 'csv' and filepath:
            self._load_results_from_csv(filepath)
        elif self.results_source == 'api':
            self._load_results_from_api()
        else:
            raise ValueError(f"Invalid results source: {self.results_source}")
            
    def _load_results_from_csv(self, filepath: Path) -> None:
        """Load results from CSV file."""
        logger.info(f"Loading results from {filepath}")
        
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    result = GameResult(
                        game_id=row['game_id'].strip(),
                        home_team=row['home_team'].strip(),
                        away_team=row['away_team'].strip(),
                        home_score=int(row['home_score']),
                        away_score=int(row['away_score']),
                        status=row['status'].strip().lower()
                    )
                    self.game_results[result.game_id] = result
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid result row: {row}, error: {e}")
                    
        logger.info(f"Loaded {len(self.game_results)} game results")
        
    def _load_results_from_api(self) -> None:
        """Load results from API (placeholder for actual implementation)."""
        logger.info("Loading results from API...")
        # This would connect to a real sports data API
        # For now, we'll create some sample data
        self.game_results = {
            'game_001': GameResult('game_001', 'TeamA', 'TeamB', 110, 105, 'completed'),
            'game_002': GameResult('game_002', 'TeamC', 'TeamD', 98, 102, 'completed'),
            'game_003': GameResult('game_003', 'TeamE', 'TeamF', 0, 0, 'void'),
        }
        
    def evaluate_bet(self, bet: Bet, game_result: GameResult) -> BetResult:
        """
        Evaluate a single bet against game results.
        
        Returns:
            BetResult with outcome and payout information
        """
        if game_result.status != 'completed':
            return BetResult(bet, 'void', bet.stake, 0.0)
            
        result = 'loss'  # Default to loss
        payout = 0.0
        
        if bet.bet_type == 'moneyline':
            winner = game_result.winner
            if winner == 'push':
                result = 'push'
                payout = bet.stake
            elif winner == bet.selection:
                result = 'win'
                payout = bet.potential_payout
                
        elif bet.bet_type == 'spread':
            # Simplified spread betting logic
            # Would need actual spread values in real implementation
            home_spread = -5.5  # Example spread
            adjusted_home_score = game_result.home_score + home_spread
            
            if bet.selection == game_result.home_team:
                if adjusted_home_score > game_result.away_score:
                    result = 'win'
                    payout = bet.potential_payout
                elif adjusted_home_score == game_result.away_score:
                    result = 'push'
                    payout = bet.stake
            else:  # Away team bet
                if game_result.away_score > adjusted_home_score:
                    result = 'win'
                    payout = bet.potential_payout
                elif game_result.away_score == adjusted_home_score:
                    result = 'push'
                    payout = bet.stake
                    
        elif bet.bet_type == 'total':
            total_line = 215.5  # Example total line
            actual_total = game_result.total_score
            
            if bet.selection == 'over':
                if actual_total > total_line:
                    result = 'win'
                    payout = bet.potential_payout
                elif actual_total == total_line:
                    result = 'push'
                    payout = bet.stake
            else:  # Under bet
                if actual_total < total_line:
                    result = 'win'
                    payout = bet.potential_payout
                elif actual_total == total_line:
                    result = 'push'
                    payout = bet.stake
                    
        profit = payout - bet.stake
        return BetResult(bet, result, payout, profit)
        
    def simulate(self) -> None:
        """Run the paper trading simulation."""
        logger.info("Starting paper trading simulation...")
        
        for bet in self.bets:
            if bet.game_id not in self.game_results:
                logger.warning(f"No result found for game {bet.game_id}")
                # Treat as void
                self.bet_results.append(BetResult(bet, 'void', bet.stake, 0.0))
                continue
                
            game_result = self.game_results[bet.game_id]
            bet_result = self.evaluate_bet(bet, game_result)
            self.bet_results.append(bet_result)
            
            # Update bankroll
            self.bankroll = self.bankroll - bet.stake + bet_result.payout
            
        logger.info(f"Simulation complete. Evaluated {len(self.bet_results)} bets")
        
    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics from simulation results."""
        wins = sum(1 for r in self.bet_results if r.result == 'win')
        losses = sum(1 for r in self.bet_results if r.result == 'loss')
        pushes = sum(1 for r in self.bet_results if r.result == 'push')
        voids = sum(1 for r in self.bet_results if r.result == 'void')
        
        total_wagered = sum(r.bet.stake for r in self.bet_results)
        total_payout = sum(r.payout for r in self.bet_results)
        net_profit = total_payout - total_wagered
        
        # Calculate ROI and win rate
        roi = (net_profit / total_wagered * 100) if total_wagered > 0 else 0.0
        total_decided = wins + losses
        win_rate = (wins / total_decided * 100) if total_decided > 0 else 0.0
        
        return PerformanceMetrics(
            total_bets=len(self.bet_results),
            wins=wins,
            losses=losses,
            pushes=pushes,
            voids=voids,
            total_wagered=total_wagered,
            total_payout=total_payout,
            net_profit=net_profit,
            roi=roi,
            win_rate=win_rate,
            starting_bankroll=self.starting_bankroll,
            ending_bankroll=self.bankroll
        )
        
    def save_simulation_results(self, output_dir: Path) -> Tuple[Path, Path]:
        """
        Save simulation results to CSV and summary to JSON.
        
        Returns:
            Tuple of (simulation_csv_path, summary_json_path)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save detailed results to CSV
        csv_filename = f"simulation_{self.date}.csv"
        csv_path = output_dir / csv_filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'game_id', 'bet_type', 'selection', 'odds', 'stake',
                'result', 'payout', 'profit', 'running_bankroll'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            running_bankroll = self.starting_bankroll
            for bet_result in self.bet_results:
                running_bankroll = running_bankroll - bet_result.bet.stake + bet_result.payout
                writer.writerow({
                    'game_id': bet_result.bet.game_id,
                    'bet_type': bet_result.bet.bet_type,
                    'selection': bet_result.bet.selection,
                    'odds': bet_result.bet.odds,
                    'stake': bet_result.bet.stake,
                    'result': bet_result.result,
                    'payout': round(bet_result.payout, 2),
                    'profit': round(bet_result.profit, 2),
                    'running_bankroll': round(running_bankroll, 2)
                })
                
        logger.info(f"Saved simulation results to {csv_path}")
        
        # Save summary metrics to JSON
        json_filename = "daily_summary.json"
        json_path = output_dir / json_filename
        
        metrics = self.calculate_metrics()
        summary_data = {
            'date': self.date,
            'results_source': self.results_source,
            'metrics': {
                'total_bets': metrics.total_bets,
                'wins': metrics.wins,
                'losses': metrics.losses,
                'pushes': metrics.pushes,
                'voids': metrics.voids,
                'total_wagered': round(metrics.total_wagered, 2),
                'total_payout': round(metrics.total_payout, 2),
                'net_profit': round(metrics.net_profit, 2),
                'roi_percentage': round(metrics.roi, 2),
                'win_rate_percentage': round(metrics.win_rate, 2),
                'starting_bankroll': round(metrics.starting_bankroll, 2),
                'ending_bankroll': round(metrics.ending_bankroll, 2)
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
            
        logger.info(f"Saved summary metrics to {json_path}")
        
        return csv_path, json_path


def main():
    """Main entry point for the paper trader CLI."""
    parser = argparse.ArgumentParser(
        description='Paper Trading Trial - Simulate betting performance'
    )
    parser.add_argument(
        '--date',
        required=True,
        help='Date for simulation (YYYYMMDD format)'
    )
    parser.add_argument(
        '--results_source',
        choices=['api', 'csv'],
        default='csv',
        help='Source of game results'
    )
    parser.add_argument(
        '--bankroll',
        type=float,
        default=1000.0,
        help='Starting bankroll amount'
    )
    parser.add_argument(
        '--bets_file',
        type=Path,
        default=Path('data/bets.csv'),
        help='Path to bets CSV file'
    )
    parser.add_argument(
        '--results_file',
        type=Path,
        default=Path('data/results.csv'),
        help='Path to results CSV file (for csv source)'
    )
    parser.add_argument(
        '--output_dir',
        type=Path,
        default=Path('output'),
        help='Directory for output files'
    )
    parser.add_argument(
        '--log_level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Validate date format
    try:
        datetime.strptime(args.date, '%Y%m%d')
    except ValueError:
        parser.error('Date must be in YYYYMMDD format')
        
    # Initialize paper trader
    trader = PaperTrader(
        date=args.date,
        results_source=args.results_source,
        bankroll=args.bankroll
    )
    
    try:
        # Load bets
        if not args.bets_file.exists():
            logger.error(f"Bets file not found: {args.bets_file}")
            sys.exit(1)
        trader.load_bets(args.bets_file)
        
        # Load results
        if args.results_source == 'csv':
            if not args.results_file.exists():
                logger.error(f"Results file not found: {args.results_file}")
                sys.exit(1)
            trader.load_results(args.results_file)
        else:
            trader.load_results()
            
        # Run simulation
        trader.simulate()
        
        # Save results
        csv_path, json_path = trader.save_simulation_results(args.output_dir)
        
        # Print summary
        metrics = trader.calculate_metrics()
        print("\n" + "="*50)
        print("PAPER TRADING SIMULATION RESULTS")
        print("="*50)
        print(f"Date: {args.date}")
        print(f"Starting Bankroll: ${metrics.starting_bankroll:,.2f}")
        print(f"Ending Bankroll: ${metrics.ending_bankroll:,.2f}")
        print(f"\nBet Results:")
        print(f"  Total Bets: {metrics.total_bets}")
        print(f"  Wins: {metrics.wins}")
        print(f"  Losses: {metrics.losses}")
        print(f"  Pushes: {metrics.pushes}")
        print(f"  Voids: {metrics.voids}")
        print(f"\nFinancial Summary:")
        print(f"  Total Wagered: ${metrics.total_wagered:,.2f}")
        print(f"  Total Payout: ${metrics.total_payout:,.2f}")
        print(f"  Net Profit: ${metrics.net_profit:,.2f}")
        print(f"  ROI: {metrics.roi:.2f}%")
        print(f"  Win Rate: {metrics.win_rate:.2f}%")
        print(f"\nOutput Files:")
        print(f"  Simulation: {csv_path}")
        print(f"  Summary: {json_path}")
        print("="*50 + "\n")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
