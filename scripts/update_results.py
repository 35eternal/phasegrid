"""
Result ingestion script for updating slip statuses and tracking phase performance.
Accepts CSV input or API scraping (stub) and updates Google Sheets accordingly.
"""

import sys
import csv
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for module imports
sys.path.append(str(Path(__file__).parent.parent))

from modules.sheet_connector import SheetConnector


class ResultIngester:
    """Handles ingestion of settled props and updates slip statuses."""
    
    def __init__(self, sheet_connector: SheetConnector):
        """
        Initialize with sheet connector instance.
        
        Args:
            sheet_connector: Initialized SheetConnector for Google Sheets access
        """
        self.sheet_connector = sheet_connector
        self.results_tracker_path = Path("data/phase_results_tracker.csv")
        
        # Ensure data directory exists
        self.results_tracker_path.parent.mkdir(exist_ok=True)
    
    def ingest_from_csv(self, csv_path: str) -> Dict[str, bool]:
        """
        Ingest settled prop results from CSV file.
        
        Args:
            csv_path: Path to CSV with columns: prop_id, result (hit/miss)
        
        Returns:
            Dictionary mapping prop_id to hit/miss boolean
        """
        results = {}
        
        try:
            with open(csv_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    prop_id = row['prop_id']
                    result = row['result'].lower() == 'hit'
                    results[prop_id] = result
            
            print(f"Loaded {len(results)} prop results from {csv_path}")
            return results
            
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return {}
    
    def scrape_results_api(self, date: Optional[str] = None) -> Dict[str, bool]:
        """
        Stub for API scraping functionality.
        
        Args:
            date: Date to scrape results for (YYYY-MM-DD format)
        
        Returns:
            Dictionary mapping prop_id to hit/miss boolean
        """
        # TODO: Implement actual API scraping
        print(f"API scraping stub called for date: {date or 'today'}")
        print("This functionality requires API credentials and endpoints.")
        
        # Return empty dict for now
        return {}
    
    def update_slip_statuses(self, prop_results: Dict[str, bool]) -> int:
        """
        Update slip statuses in slips_log based on prop results.
        
        Args:
            prop_results: Dictionary mapping prop_id to hit/miss boolean
        
        Returns:
            Number of slips updated
        """
        # Fetch current slips_log
        slips_df = self.sheet_connector.fetch_slips_log()
        
        if slips_df.empty:
            print("No slips found in slips_log")
            return 0
        
        updates = []
        slips_updated = 0
        
        for idx, row in slips_df.iterrows():
            # Skip already settled slips
            if row['status'] in ['won', 'lost']:
                continue
            
            # Parse props from JSON
            try:
                slip_props = json.loads(row['props'])
            except:
                continue
            
            # Check if all props in slip have results
            prop_ids = [p['prop_id'] for p in slip_props]
            if not all(pid in prop_results for pid in prop_ids):
                continue  # Not all props settled yet
            
            # Determine slip outcome
            if row['ticket_type'] == 'POWER':
                # POWER play: all must hit
                won = all(prop_results[pid] for pid in prop_ids)
                payout = float(row['stake']) * float(row['odds']) if won else 0.0
            else:  # FLEX
                # FLEX play: calculate based on hits
                n_hits = sum(prop_results[pid] for pid in prop_ids)
                payout = self._calculate_flex_payout(row, n_hits)
                won = payout > 0
            
            # Update slip
            slips_df.at[idx, 'status'] = 'won' if won else 'lost'
            slips_df.at[idx, 'payout'] = round(payout, 2)
            slips_df.at[idx, 'settled_at'] = datetime.now().isoformat()
            
            slips_updated += 1
            
            # Track for phase results
            updates.append({
                'slip_id': row['slip_id'],
                'phase': slip_props[0].get('phase', 'unknown'),  # Use first prop's phase
                'ticket_type': row['ticket_type'],
                'stake': float(row['stake']),
                'payout': payout,
                'won': won,
                'settled_at': datetime.now().isoformat()
            })
        
        # Push updates back to sheet
        if slips_updated > 0:
            # Convert back to format expected by sheet
            slips_df['props'] = slips_df['props'].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)
            self.sheet_connector.worksheet.update([slips_df.columns.tolist()] + slips_df.values.tolist())
            print(f"Updated {slips_updated} slips in Google Sheets")
        
        # Append to phase results tracker
        if updates:
            self._update_phase_tracker(updates)
        
        return slips_updated
    
    def _calculate_flex_payout(self, slip_row: pd.Series, n_hits: int) -> float:
        """Calculate FLEX payout based on number of hits."""
        n_props = len(json.loads(slip_row['props']))
        
        # Load payout tables
        try:
            with open('config/payout_tables.json', 'r') as f:
                payouts = json.load(f)['flex']
        except:
            # Fallback payouts
            payouts = {
                "3_of_3": 5.0, "3_of_4": 2.5, "4_of_4": 10.0,
                "4_of_5": 4.0, "5_of_5": 20.0, "5_of_6": 10.0, "6_of_6": 40.0
            }
        
        tier_key = f"{n_hits}_of_{n_props}"
        multiplier = payouts.get(tier_key, 0.0)
        
        return float(slip_row['stake']) * multiplier
    
    def _update_phase_tracker(self, updates: List[Dict]):
        """Append results to phase_results_tracker.csv."""
        # Read existing tracker or create new
        if self.results_tracker_path.exists():
            tracker_df = pd.read_csv(self.results_tracker_path)
        else:
            tracker_df = pd.DataFrame(columns=[
                'slip_id', 'phase', 'ticket_type', 'stake', 
                'payout', 'won', 'settled_at'
            ])
        
        # Append new results
        new_df = pd.DataFrame(updates)
        
        # Avoid FutureWarning by ensuring both DataFrames have same columns
        for col in tracker_df.columns:
            if col not in new_df.columns:
                new_df[col] = None
        
        tracker_df = pd.concat([tracker_df, new_df], ignore_index=True)
        
        # Save
        tracker_df.to_csv(self.results_tracker_path, index=False)
        print(f"Updated phase_results_tracker.csv with {len(updates)} results")
        
        # Trigger confidence tracker update (stub)
        print("TODO: Trigger phase_confidence_tracker.py to refresh win-rates")


def main():
    """Main entry point for result ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update betting slip results")
    parser.add_argument('--csv', type=str, help='Path to CSV with prop results')
    parser.add_argument('--api', action='store_true', help='Scrape results from API')
    parser.add_argument('--date', type=str, help='Date for API scraping (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Initialize sheet connector
    connector = SheetConnector()
    connector.connect()
    
    # Initialize ingester
    ingester = ResultIngester(connector)
    
    # Get prop results
    prop_results = {}
    
    if args.csv:
        prop_results = ingester.ingest_from_csv(args.csv)
    elif args.api:
        prop_results = ingester.scrape_results_api(args.date)
    else:
        print("Error: Must specify either --csv or --api")
        sys.exit(1)
    
    if not prop_results:
        print("No prop results loaded")
        sys.exit(1)
    
    # Update slip statuses
    n_updated = ingester.update_slip_statuses(prop_results)
    print(f"\nSummary: Updated {n_updated} slips")


if __name__ == "__main__":
    main()