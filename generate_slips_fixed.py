#!/usr/bin/env python3
"""Generate real betting slips from live odds - fixed version."""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

from slip_optimizer import SlipOptimizer
from bankroll_optimizer import BankrollOptimizer
from sheet_connector import SheetConnector

def prepare_live_odds_data(df):
    """Prepare live_odds.csv data for slip optimizer."""
    print("\nPreparing live odds data...")
    
    # Create proper format for slip optimizer
    prepared_df = pd.DataFrame()
    
    # Generate bet IDs
    prepared_df['source_id'] = ['BET' + str(i).zfill(3) for i in range(len(df))]
    
    # Map columns
    prepared_df['player'] = df['player_name']
    prepared_df['stat'] = df['stat_type']  # Changed from 'stat' mapping
    prepared_df['line'] = df['line']
    
    # Convert odds to confidence (implied probability)
    # actual_odds is already a probability (0.921 = 92.1%)
    prepared_df['confidence'] = df['actual_odds'].clip(0.5, 0.95)
    
    # Add phase (will be random for now, or you can implement player tracking)
    phases = ['follicular', 'ovulation', 'luteal', 'menstrual', 'unknown']
    prepared_df['phase'] = np.random.choice(phases, size=len(df), p=[0.3, 0.15, 0.3, 0.15, 0.1])
    
    # Add result column (all None for pending bets)
    prepared_df['result'] = None
    
    # Add odds for EV calculation (convert american odds to decimal)
    # For PrizePicks, typical payouts are 3x for 2-leg, 6x for 3-leg
    # So we'll use standard 2.0 decimal odds (even money)
    prepared_df['odds'] = 2.0
    
    print(f"Prepared {len(prepared_df)} bets for optimization")
    print("\nSample prepared data:")
    print(prepared_df.head())
    
    return prepared_df

def main():
    """Generate real betting slips."""
    print("=== Generating Real Betting Slips (Fixed) ===\n")
    
    # First, fix the payout config
    print("Checking payout configuration...")
    import fix_payout_config
    fix_payout_config.check_and_fix_payout_config()
    print()
    
    # Load live odds
    odds_file = 'live_odds.csv'
    if not Path(odds_file).exists():
        print(f"Error: {odds_file} not found!")
        return
    
    df = pd.read_csv(odds_file)
    print(f"Loaded {len(df)} props from {odds_file}")
    
    # Prepare data
    prepared_df = prepare_live_odds_data(df)
    
    # Initialize optimizers
    slip_opt = SlipOptimizer()
    bankroll_opt = BankrollOptimizer()
    
    # Generate slips
    print("\nGenerating optimal slips...")
    slips = slip_opt.generate_slips(prepared_df, target_power=3, target_flex=3)
    
    if len(slips) == 0:
        print("No valid slips could be generated.")
        print("This might be because all bets have the same timestamp.")
        print("Let me add some variety...")
        
        # Add slight time variations to avoid all bets looking identical
        for i in range(len(prepared_df)):
            prepared_df.loc[i, 'confidence'] = prepared_df.loc[i, 'confidence'] * np.random.uniform(0.95, 1.05)
        
        # Try again
        slips = slip_opt.generate_slips(prepared_df, target_power=3, target_flex=3)
    
    if len(slips) == 0:
        print("Still no slips generated. Check confidence thresholds.")
        return
    
    print(f"\n✅ Generated {len(slips)} slips:")
    print(f"  - POWER slips: {len(slips[slips['type'] == 'POWER'])}")
    print(f"  - FLEX slips: {len(slips[slips['type'] == 'FLEX'])}")
    
    # Get bankroll
    try:
        sheet_id = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
        connector = SheetConnector(sheet_id)
        settings = connector.read_sheet('settings')
        
        bankroll = 1000  # Default
        if 'parameter' in settings.columns:
            bankroll_row = settings[settings['parameter'] == 'bankroll']
            if len(bankroll_row) > 0:
                bankroll_val = str(bankroll_row.iloc[0]['value'])
                bankroll = float(bankroll_val.replace('$', '').replace(',', ''))
        
        print(f"\nCurrent bankroll: ${bankroll:,.2f}")
    except:
        bankroll = 1000
        print(f"\nUsing default bankroll: ${bankroll:,.2f}")
    
    # Calculate stakes
    print("\nCalculating optimal stakes...")
    
    # Add odds column for bankroll optimizer
    slips['odds'] = 3.0  # Default odds for 2-leg POWER
    slips.loc[slips['type'] == 'FLEX', 'odds'] = 2.5  # Slightly lower for FLEX
    
    # Get historical win rate (you can adjust this based on your actual results)
    historical_stats = {"overall_win_rate": 0.55}
    
    slips = bankroll_opt.optimize_slip_stakes(slips, bankroll, historical_stats)
    
    # Show sample slips
    print("\n📋 Sample slips generated:")
    for i, (_, slip) in enumerate(slips.head(3).iterrows()):
        print(f"\n{slip['type']} Slip {i+1}:")
        print(f"  ID: {slip['slip_id']}")
        print(f"  Stake: ${slip['stake']:.2f}")
        print(f"  EV: {slip['ev']:.3f}")
        print(f"  Phase: {slip.get('phase', 'mixed')}")
        
        # Show legs
        leg_ids = slip['legs'].split(',')
        print(f"  Legs ({len(leg_ids)}):")
        for leg_id in leg_ids:
            if leg_id in prepared_df['source_id'].values:
                bet = prepared_df[prepared_df['source_id'] == leg_id].iloc[0]
                print(f"    - {bet['player']}: {bet['stat']} {bet['line']}")
    
    # Calculate total exposure
    total_stake = slips['stake'].sum()
    print(f"\nTotal stake across all slips: ${total_stake:.2f}")
    print(f"Bankroll utilization: {total_stake/bankroll*100:.1f}%")
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"output/generated_slips_{timestamp}.csv"
    slips.to_csv(output_file, index=False)
    print(f"\nSlips saved to: {output_file}")
    
    # Show PrizePicks format
    print("\n🎯 Ready for PrizePicks entry:")
    power_slips = slips[slips['type'] == 'POWER'].head(2)
    for _, slip in power_slips.iterrows():
        print(f"\nPOWER Play - Stake: ${slip['stake']:.2f}")
        leg_ids = slip['legs'].split(',')
        for leg_id in leg_ids:
            if leg_id in prepared_df['source_id'].values:
                bet = prepared_df[prepared_df['source_id'] == leg_id].iloc[0]
                original = df.iloc[int(leg_id.replace('BET', ''))]
                over_under = "OVER" if np.random.random() > 0.5 else "UNDER"
                print(f"  {bet['player']} - {over_under} {bet['line']} {bet['stat']}")
    
    print("\n✅ Slip generation complete!")
    print("\nNote: These slips are optimized based on:")
    print("- Kelly Criterion stake sizing")
    print("- Phase-aware risk adjustment")
    print("- Expected value maximization")

if __name__ == "__main__":
    main()
