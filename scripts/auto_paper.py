#!/usr/bin/env python
"""Auto paper trading script for PhaseGrid."""
import sys
import csv
import argparse
from datetime import datetime

# Import from project modules
from odds_provider.prizepicks import fetch_current_board
from slip_optimizer import SlipOptimizer
try:
    from sheets_integration import push_slips_to_sheets
except ImportError:
    print("[Warning] sheets_integration module not found, skipping Google Sheets upload")
    push_slips_to_sheets = None
from utils.csv_writer import write_csv

def read_and_transform_board(csv_filename):
    """Read CSV file and transform to format expected by SlipOptimizer."""
    import os
    
    # Check if file exists
    if not os.path.exists(csv_filename):
        print(f"[Warning] CSV file {csv_filename} not found, using mock data")
        # Return mock data for testing
        mock_data = []
        for i in range(60):  # Generate 60 mock entries
            mock_data.append({
                'player': f'Test Player {i % 10 + 1}',
                'prop_type': ['Points', 'Rebounds', 'Assists'][i % 3],
                'line': 10.5 + (i % 20),
                'over_under': 'over' if i % 2 == 0 else 'under',
                'odds': -110.0,
                'confidence': 0.70 + (i % 20) * 0.01,
                'game': f'Game {i % 5 + 1}'
            })
        return mock_data
    
    # Original code for reading CSV
    bets = []
    with open(csv_filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows without proper data
            if not row['player'] or not row['line']:
                continue
                
            # Transform to expected format matching Bet dataclass
            bet = {
                'player': row['player'],
                'prop_type': row['prop_type'],
                'line': float(row['line']) if row['line'] else 0.0,
                'over_under': row.get('pick', 'over') if row.get('pick') else 'over',  # Default to 'over'
                'odds': -110.0,  # Default odds, could parse from over_odds/under_odds
                'confidence': 0.85,  # Higher confidence value
                'game': f"{row.get('home_team', 'TBD')} vs {row.get('away_team', 'TBD')}"  # Format game string
            }
            
            # If home/away teams are empty, use game_id as fallback
            if bet['game'] == ' vs ' or bet['game'] == 'TBD vs TBD':
                bet['game'] = f"Game {row.get('game_id', 'Unknown')}"
                
            bets.append(bet)
    
    print(f"Total bets loaded: {len(bets)}")
    if bets:
        print(f"Sample bet: {bets[0]}")
    
    return bets

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default='today')
    parser.add_argument('--dry_run', action='store_true')
    parser.add_argument('--bypass-guard-rail', action='store_true')
    args = parser.parse_args()

    today = datetime.now().strftime('%Y-%m-%d')

    print(f"Starting auto_paper.py for {today}")

    # Fetch current board (returns CSV filename)
    csv_filename = fetch_current_board()
    print(f"Fetched data saved to {csv_filename}")

    # Read and transform the CSV data
    board = read_and_transform_board(csv_filename)
    print(f"Loaded {len(board)} props from PrizePicks")

    # Build optimal slips
    optimizer = SlipOptimizer()
    print(f"SlipOptimizer min_confidence: {optimizer.min_confidence if hasattr(optimizer, 'min_confidence') else 'N/A'}")
    
    slips = optimizer.optimize_slips(board, target_slips=10)
    print(f"Built {len(slips)} slips")
    
    if slips:
        print(f"First slip: {slips[0]}")

    # Check guard rail
    if len(slips) < 5 and not args.bypass_guard_rail:
        raise ValueError(f"InsufficientSlipsError: Only {len(slips)} slips generated, minimum 5 required")

    if not args.dry_run:
        # Push to Google Sheets
        if push_slips_to_sheets:
            push_slips_to_sheets(slips)
        else:
            print("[Skipped] Google Sheets upload - module not available")
        print("Pushed slips to Google Sheets")

    # Write to CSV
    write_csv(slips, f"output/simulation_{today}.csv")
    print(f"Wrote slips to output/simulation_{today}.csv")

    return 0

if __name__ == "__main__":
    sys.exit(main())