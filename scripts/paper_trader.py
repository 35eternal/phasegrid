#!/usr/bin/env python3
"""
Paper Trading Trial - Simulates betting strategies using model predictions.
"""

import argparse
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PaperTrader:
    """Simulates paper trading using model predictions and bet results."""
    
    def __init__(self, date: str, results_source: str, bankroll: float = 1000.0):
        """
        Initialize PaperTrader with configuration.
        
        Args:
            date: Date in YYYYMMDD format
            results_source: Path to bet results CSV
            bankroll: Starting bankroll amount
        """
        self.date = date
        self.results_source = results_source
        self.initial_bankroll = bankroll
        self.current_bankroll = bankroll
        self.bets_placed = []
        self.results = []
        
    def load_predictions(self) -> List[Dict[str, str]]:
        """Load predictions from predictions_YYYYMMDD.csv."""
        predictions_file = f"predictions_{self.date}.csv"
        predictions = []
        
        if not os.path.exists(predictions_file):
            print(f"Warning: Predictions file {predictions_file} not found")
            return predictions
            
        with open(predictions_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                predictions.append(row)
                
        return predictions
    
    def load_results(self) -> Dict[str, Dict[str, str]]:
        """Load bet results from CSV file."""
        results = {}
        
        if not os.path.exists(self.results_source):
            print(f"Warning: Results file {self.results_source} not found")
            return results
            
        with open(self.results_source, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Strip whitespace from keys and values
                clean_row = {k.strip(): v.strip() if v else v for k, v in row.items()}
                
                # Check if required fields exist
                if 'game_id' in clean_row and 'bet_type' in clean_row:
                    # Key by game_id and bet_type for lookup
                    key = f"{clean_row['game_id']}_{clean_row['bet_type']}"
                    results[key] = clean_row
                else:
                    print(f"Warning: Missing required fields in row: {row}")
                
        return results
    
    def calculate_payout(self, odds: int, stake: float, outcome: str) -> float:
        """
        Calculate payout based on American odds and outcome.
        
        Args:
            odds: American odds (e.g., -110, +150)
            stake: Amount wagered
            outcome: 'win', 'loss', 'push', or 'void'
            
        Returns:
            Payout amount (including stake for wins, 0 for losses, stake for push/void)
        """
        if outcome in ['push', 'void']:
            return stake
        elif outcome == 'loss':
            return 0.0
        elif outcome == 'win':
            if odds > 0:
                # Positive odds: profit = stake * (odds/100)
                profit = stake * (odds / 100)
            else:
                # Negative odds: profit = stake / (abs(odds)/100)
                profit = stake / (abs(odds) / 100)
            return stake + profit
        else:
            raise ValueError(f"Unknown outcome: {outcome}")
    
    def place_bets(self, predictions: List[Dict[str, str]], results: Dict[str, Dict[str, str]]) -> None:
        """Place bets based on predictions and calculate results."""
        for pred in predictions:
            # Extract bet details
            game_id = pred.get('game_id', '').strip()
            bet_type = pred.get('bet_type', '').strip()
            pick = pred.get('pick', '').strip()
            
            # Handle odds that might have + or - prefix
            odds_str = pred.get('odds', '0').strip()
            if odds_str.startswith('+'):
                odds = int(odds_str[1:])
            else:
                odds = int(odds_str)
                
            confidence = float(pred.get('confidence', '0.5'))
            
            # Calculate stake based on confidence (Kelly criterion simplified)
            stake = min(self.current_bankroll * confidence * 0.1, self.current_bankroll * 0.05)
            stake = round(stake, 2)
            
            # Skip if insufficient bankroll
            if stake > self.current_bankroll or stake <= 0:
                continue
                
            # Look up result
            result_key = f"{game_id}_{bet_type}"
            result = results.get(result_key, {})
            outcome = result.get('outcome', 'void')
            
            # Calculate payout
            payout = self.calculate_payout(odds, stake, outcome)
            profit = payout - stake
            self.current_bankroll += profit
            
            # Record bet
            bet_record = {
                'game_id': game_id,
                'bet_type': bet_type,
                'pick': pick,
                'odds': odds,
                'stake': stake,
                'outcome': outcome,
                'payout': payout,
                'profit': profit,
                'bankroll_after': self.current_bankroll
            }
            self.bets_placed.append(bet_record)
    
    def calculate_metrics(self) -> Dict[str, any]:
        """Calculate performance metrics."""
        total_slips = len(self.bets_placed)
        wins = sum(1 for bet in self.bets_placed if bet['outcome'] == 'win')
        losses = sum(1 for bet in self.bets_placed if bet['outcome'] == 'loss')
        
        total_stake = sum(bet['stake'] for bet in self.bets_placed)
        total_profit = self.current_bankroll - self.initial_bankroll
        
        roi_pct = 0.0
        if total_stake > 0:
            roi_pct = (total_profit / total_stake) * 100
            
        return {
            'date': self.date,
            'total_slips': total_slips,
            'wins': wins,
            'losses': losses,
            'roi_pct': round(roi_pct, 2),
            'bankroll_after': round(self.current_bankroll, 2)
        }
    
    def write_simulation_csv(self) -> None:
        """Write detailed simulation results to CSV."""
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f'simulation_{self.date}.csv'
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if self.bets_placed:
                fieldnames = self.bets_placed[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.bets_placed)
    
    def write_metrics_csv(self, metrics: Dict[str, any]) -> None:
        """Write or update metrics in paper_metrics.csv (idempotent)."""
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        metrics_file = output_dir / 'paper_metrics.csv'
        
        # Read existing metrics
        existing_metrics = []
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    # Only keep rows that match our schema
                    for row in reader:
                        if 'date' in row and row['date'] != self.date:
                            # Only keep rows with our expected fields
                            clean_row = {
                                'date': row.get('date', ''),
                                'total_slips': row.get('total_slips', '0'),
                                'wins': row.get('wins', '0'),
                                'losses': row.get('losses', '0'),
                                'roi_pct': row.get('roi_pct', '0.0'),
                                'bankroll_after': row.get('bankroll_after', '0.0')
                            }
                            existing_metrics.append(clean_row)
            except Exception as e:
                print(f"Warning: Could not read existing metrics file: {e}")
                # Start fresh if we can't read the file
                existing_metrics = []
        
        # Add current metrics
        existing_metrics.append(metrics)
        
        # Sort by date
        existing_metrics.sort(key=lambda x: x['date'])
        
        # Write all metrics
        with open(metrics_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['date', 'total_slips', 'wins', 'losses', 'roi_pct', 'bankroll_after']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_metrics)
    
    def write_daily_summary(self, metrics: Dict[str, any]) -> None:
        """Write daily summary JSON."""
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        summary = {
            'date': self.date,
            'initial_bankroll': self.initial_bankroll,
            'final_bankroll': self.current_bankroll,
            'total_bets': len(self.bets_placed),
            'metrics': metrics,
            'best_bet': None,
            'worst_bet': None
        }
        
        if self.bets_placed:
            # Find best and worst bets
            best_bet = max(self.bets_placed, key=lambda x: x['profit'])
            worst_bet = min(self.bets_placed, key=lambda x: x['profit'])
            
            summary['best_bet'] = {
                'game_id': best_bet['game_id'],
                'bet_type': best_bet['bet_type'],
                'profit': best_bet['profit']
            }
            summary['worst_bet'] = {
                'game_id': worst_bet['game_id'],
                'bet_type': worst_bet['bet_type'],
                'profit': worst_bet['profit']
            }
        
        output_file = output_dir / 'daily_summary.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
    
    def run(self) -> None:
        """Execute paper trading simulation."""
        print(f"Starting paper trading for {self.date}")
        print(f"Initial bankroll: ${self.initial_bankroll}")
        
        # Load data
        predictions = self.load_predictions()
        results = self.load_results()
        
        print(f"Loaded {len(predictions)} predictions")
        print(f"Loaded {len(results)} results")
        
        # Place bets
        self.place_bets(predictions, results)
        
        # Calculate metrics
        metrics = self.calculate_metrics()
        
        # Write outputs
        self.write_simulation_csv()
        self.write_metrics_csv(metrics)
        self.write_daily_summary(metrics)
        
        print(f"\nSimulation complete!")
        print(f"Total bets placed: {metrics['total_slips']}")
        print(f"Wins: {metrics['wins']}, Losses: {metrics['losses']}")
        print(f"ROI: {metrics['roi_pct']}%")
        print(f"Final bankroll: ${metrics['bankroll_after']}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Paper Trading Trial - Simulate betting strategies')
    parser.add_argument('--date', required=True, help='Date in YYYYMMDD format')
    parser.add_argument('--results_source', required=True, help='Path to bet results CSV')
    parser.add_argument('--bankroll', type=float, default=1000.0, help='Starting bankroll (default: 1000)')
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.date, '%Y%m%d')
    except ValueError:
        parser.error(f"Invalid date format: {args.date}. Use YYYYMMDD.")
    
    # Run simulation
    trader = PaperTrader(args.date, args.results_source, args.bankroll)
    trader.run()


if __name__ == '__main__':
    main()
