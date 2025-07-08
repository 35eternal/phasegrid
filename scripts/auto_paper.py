#!/usr/bin/env python
"""Auto paper trading script for PhaseGrid."""
import sys
import argparse
from datetime import datetime

# Import from project modules
from odds_provider.prizepicks import fetch_current_board
from slip_optimizer import build_slips
from sheets_integration import push_slips_to_sheets
from utils.csv_writer import write_csv

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default='today')
    parser.add_argument('--dry_run', action='store_true')
    parser.add_argument('--bypass-guard-rail', action='store_true')
    args = parser.parse_args()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Starting auto_paper.py for {today}")
    
    # Fetch current board
    board = fetch_current_board()
    print(f"Fetched {len(board)} props from PrizePicks")
    
    # Build optimal slips
    slips = build_slips(board)
    print(f"Built {len(slips)} slips")
    
    # Check guard rail
    if len(slips) < 5 and not args.bypass_guard_rail:
        raise ValueError(f"InsufficientSlipsError: Only {len(slips)} slips generated, minimum 5 required")
    
    if not args.dry_run:
        # Push to Google Sheets
        push_slips_to_sheets(slips)
        print("Pushed slips to Google Sheets")
    
    # Write to CSV
    write_csv(slips, f"output/simulation_{today}.csv")
    print(f"Wrote slips to output/simulation_{today}.csv")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
