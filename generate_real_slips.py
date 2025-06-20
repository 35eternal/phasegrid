#!/usr/bin/env python3
"""Generate real betting slips from your odds data."""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

from slip_optimizer import SlipOptimizer
from bankroll_optimizer import BankrollOptimizer
from sheet_connector import SheetConnector

def load_props_data():
    """Load props from various sources."""
    # Try different file locations
    possible_files = [
        'live_odds.csv',
        'live_odds_matched.csv',
        'data/live_odds.csv',
        'daily_betting_card.csv',
        'daily_betting_card_fixed.csv'
    ]
    
    for file_path in possible_files:
        if Path(file_path).exists():
            print(f"Loading props from: {file_path}")
            df = pd.read_csv(file_path)
            print(f"Found {len(df)} props")
            print(f"Columns: {list(df.columns)}")
            return df, file_path
    
    print("No props file found!")
    return None, None

def prepare_props_for_optimizer(props_df):
    """Convert props data to format expected by slip optimizer."""
    # Map your columns to expected format
    required_cols = ['bet_id', 'player', 'stat', 'line', 'confidence', 'phase', 'result']
    
    # Create mapped dataframe
    mapped_df = pd.DataFrame()
    
    # Generate bet IDs if not present
    if 'bet_id' not in props_df.columns:
        props_df['bet_id'] = ['BET' + str(i).zfill(3) for i in range(len(props_df))]
    
    # Map columns based on what's available
    column_mappings = {
        'bet_id': ['bet_id', 'id', 'source_id'],
        'player': ['player', 'player_name', 'name'],
        'stat': ['stat', 'market', 'prop_type', 'type'],
        'line': ['line', 'value', 'number'],
        'confidence': ['confidence', 'edge', 'probability', 'win_prob'],
        'phase': ['phase', 'cycle_phase', 'menstrual_phase'],
        'result': ['result', 'outcome']
    }
    
    for target_col, possible_cols in column_mappings.items():
        for col in possible_cols:
            if col in props_df.columns:
                mapped_df[target_col] = props_df[col]
                break
        
        # Set defaults if column not found
        if target_col not in mapped_df.columns:
            if target_col == 'phase':
                mapped_df[target_col] = 'unknown'  # Default phase
            elif target_col == 'confidence':
                mapped_df[target_col] = 0.7  # Default confidence
            elif target_col == 'result':
                mapped_df[target_col] = None
            else:
                print(f"Warning: Could not find mapping for {target_col}")
    
    # Ensure confidence is numeric and reasonable
    if 'confidence' in mapped_df.columns:
        mapped_df['confidence'] = pd.to_numeric(mapped_df['confidence'], errors='coerce').fillna(0.7)
        mapped_df['confidence'] = mapped_df['confidence'].clip(0.5, 0.95)
    
    return mapped_df

def main():
    """Generate real betting slips."""
    print("=== Generating Real Betting Slips ===\n")
    
    # Load props data
    props_df, source_file = load_props_data()
    if props_df is None:
        print("Cannot proceed without props data.")
        return
    
    # Show sample of data
    print("\nSample props:")
    print(props_df.head())
    
    # Prepare data for optimizer
    print("\nPreparing data for slip optimizer...")
    optimizer_df = prepare_props_for_optimizer(props_df)
    
    # Filter for qualified bets (pending only)
    qualified_bets = optimizer_df[optimizer_df['result'].isna()].copy()
    print(f"\nQualified bets (pending): {len(qualified_bets)}")
    
    if len(qualified_bets) < 2:
        print("Not enough pending bets to create slips!")
        return
    
    # Initialize optimizers
    slip_opt = SlipOptimizer()
    bankroll_opt = BankrollOptimizer()
    
    # Generate slips
    print("\nGenerating optimal slips...")
    slips = slip_opt.generate_slips(qualified_bets, target_power=3, target_flex=3)
    
    if len(slips) == 0:
        print("No valid slips could be generated. Check confidence thresholds.")
        return
    
    print(f"Generated {len(slips)} slips:")
    print(f"  - POWER slips: {len(slips[slips['type'] == 'POWER'])}")
    print(f"  - FLEX slips: {len(slips[slips['type'] == 'FLEX'])}")
    
    # Get bankroll from settings
    try:
        sheet_id = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
        connector = SheetConnector(sheet_id)
        settings = connector.read_sheet('settings')
        
        bankroll = 1000  # Default
        if 'parameter' in settings.columns and 'value' in settings.columns:
            bankroll_row = settings[settings['parameter'] == 'bankroll']
            if len(bankroll_row) > 0:
                bankroll = float(str(bankroll_row.iloc[0]['value']).replace('$', '').replace(',', ''))
        
        print(f"\nCurrent bankroll: ${bankroll:,.2f}")
    except:
        bankroll = 1000
        print(f"\nUsing default bankroll: ${bankroll:,.2f}")
    
    # Calculate stakes
    print("\nCalculating optimal stakes...")
    slips = bankroll_opt.optimize_slip_stakes(slips, bankroll)
    
    # Show sample slips
    print("\nSample slips generated:")
    for i, (_, slip) in enumerate(slips.head(3).iterrows()):
        print(f"\n{slip['type']} Slip {i+1}:")
        print(f"  Stake: ${slip['stake']:.2f}")
        print(f"  EV: {slip['ev']:.2f}")
        print(f"  Phase: {slip['phase'] or 'mixed'}")
        
        # Show legs
        leg_ids = slip['legs'].split(',')
        print("  Legs:")
        for leg_id in leg_ids:
            bet = qualified_bets[qualified_bets['bet_id'] == leg_id].iloc[0]
            print(f"    - {bet['player']}: {bet['stat']} {bet['line']}")
    
    # Ask to push to sheets
    print(f"\nReady to push {len(slips)} slips to Google Sheets?")
    response = input("Enter 'yes' to push, anything else to cancel: ")
    
    if response.lower() == 'yes':
        try:
            connector.write_sheet('slips_log', slips, clear_first=False)
            print("✅ Slips pushed to Google Sheets!")
        except Exception as e:
            print(f"Error pushing to sheets: {e}")
    else:
        print("Cancelled - slips not pushed to sheets.")
    
    # Save locally as backup
    output_file = f"output/generated_slips_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    slips.to_csv(output_file, index=False)
    print(f"\nSlips saved to: {output_file}")

if __name__ == "__main__":
    main()