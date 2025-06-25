#!/usr/bin/env python
"""Simple paper trader for testing workflow."""
import os
import sys
import csv
import json
import argparse
from datetime import datetime
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', required=True, help='Date in YYYYMMDD format')
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Get environment variables
    bankroll = float(os.environ.get('BANKROLL', '1000'))
    results_source = os.environ.get('RESULTS_SOURCE', 'data/bets.csv')
    
    print(f"Running paper trading for date: {args.date}")
    print(f"Starting bankroll: ${bankroll}")
    print(f"Results source: {results_source}")
    
    # Read bets data
    if not Path(results_source).exists():
        print(f"Error: {results_source} not found!")
        return 1
        
    total_bets = 0
    wins = 0
    losses = 0
    total_payout = 0
    
    with open(results_source, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_bets += 1
            if row['outcome'] == 'WIN':
                wins += 1
            elif row['outcome'] == 'LOSS':
                losses += 1
            total_payout += float(row.get('payout', 0))
    
    # Calculate metrics
    win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
    roi = (total_payout / bankroll * 100) if bankroll > 0 else 0
    
    # Write simulation CSV
    sim_file = output_dir / f'simulation_{args.date}.csv'
    with open(sim_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'total_bets', 'wins', 'losses', 'win_rate', 'roi'])
        writer.writerow([args.date, total_bets, wins, losses, f'{win_rate:.2f}', f'{roi:.2f}'])
    
    # Write daily summary
    summary = {
        'date': args.date,
        'starting_bankroll': bankroll,
        'total_bets': total_bets,
        'wins': wins,
        'losses': losses,
        'win_rate_percent': round(win_rate, 2),
        'roi_percent': round(roi, 2),
        'total_payout': total_payout,
        'ending_bankroll': bankroll + total_payout
    }
    
    summary_file = output_dir / 'daily_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Update paper_metrics.csv
    metrics_file = output_dir / 'paper_metrics.csv'
    file_exists = metrics_file.exists()
    
    with open(metrics_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['simulation_id', 'timestamp', 'starting_bankroll', 'total_bets', 
                           'wins', 'losses', 'roi_percent', 'ending_bankroll'])
        
        sim_id = f'SIM_{args.date}_{datetime.now().strftime("%H%M%S")}'
        writer.writerow([
            sim_id,
            datetime.now().isoformat(),
            bankroll,
            total_bets,
            wins,
            losses,
            round(roi, 2),
            bankroll + total_payout
        ])
    
    print(f"\nResults written to:")
    print(f"  - {sim_file}")
    print(f"  - {summary_file}")
    print(f"  - {metrics_file}")
    
    print(f"\nSummary:")
    print(f"  Total bets: {total_bets}")
    print(f"  Win rate: {win_rate:.2f}%")
    print(f"  ROI: {roi:.2f}%")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
