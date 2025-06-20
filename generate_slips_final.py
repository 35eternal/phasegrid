#!/usr/bin/env python3
"""Generate real betting slips - final working version."""

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
    prepared_df['stat'] = df['stat_type']
    prepared_df['line'] = df['line']
    
    # Convert odds to confidence (implied probability)
    prepared_df['confidence'] = df['actual_odds'].clip(0.5, 0.95)
    
    # Add phase (random for now)
    phases = ['follicular', 'ovulation', 'luteal', 'menstrual', 'unknown']
    prepared_df['phase'] = np.random.choice(phases, size=len(df), p=[0.3, 0.15, 0.3, 0.15, 0.1])
    
    # Add result column (all None for pending bets)
    prepared_df['result'] = None
    
    # Add odds for EV calculation
    prepared_df['odds'] = 2.0
    
    print(f"Prepared {len(prepared_df)} bets for optimization")
    
    return prepared_df

def add_slip_metadata(slips, bets_df):
    """Add confidence and odds metadata to slips for bankroll optimization."""
    print("\nAdding slip metadata...")
    
    # Calculate aggregate confidence for each slip
    confidences = []
    odds_list = []
    
    for _, slip in slips.iterrows():
        leg_ids = slip['legs'].split(',')
        
        # Get confidence for each leg
        leg_confidences = []
        for leg_id in leg_ids:
            if leg_id in bets_df['source_id'].values:
                bet = bets_df[bets_df['source_id'] == leg_id].iloc[0]
                leg_confidences.append(bet['confidence'])
        
        # Calculate combined confidence (product for POWER, average for FLEX)
        if slip['type'] == 'POWER':
            combined_confidence = np.prod(leg_confidences) if leg_confidences else 0.7
        else:  # FLEX
            combined_confidence = np.mean(leg_confidences) if leg_confidences else 0.7
        
        confidences.append(combined_confidence)
        
        # Set odds based on slip type and legs
        num_legs = len(leg_ids)
        if slip['type'] == 'POWER':
            odds = 3.0 if num_legs == 2 else 6.0
        else:  # FLEX
            odds = 2.5  # Average FLEX payout
        
        odds_list.append(odds)
    
    slips['confidence'] = confidences
    slips['odds'] = odds_list
    
    return slips

def main():
    """Generate real betting slips."""
    print("=== Generating Real Betting Slips (Final Version) ===\n")
    
    # Load live odds
    odds_file = 'live_odds.csv'
    if not Path(odds_file).exists():
        print(f"Error: {odds_file} not found!")
        return
    
    df = pd.read_csv(odds_file)
    print(f"Loaded {len(df)} props from {odds_file}")
    
    # Show unique players
    players = df['player_name'].unique()
    print(f"\nPlayers available: {', '.join(players[:5])}{'...' if len(players) > 5 else ''}")
    
    # Prepare data
    prepared_df = prepare_live_odds_data(df)
    
    # Initialize optimizers
    slip_opt = SlipOptimizer()
    bankroll_opt = BankrollOptimizer()
    
    # Generate slips
    print("\nGenerating optimal slips...")
    slips = slip_opt.generate_slips(prepared_df, target_power=3, target_flex=3)
    
    if len(slips) == 0:
        print("No slips generated. Adjusting confidence threshold...")
        slip_opt.min_confidence = 0.6  # Lower threshold
        slips = slip_opt.generate_slips(prepared_df, target_power=3, target_flex=3)
    
    if len(slips) == 0:
        print("Still no slips. Check your data.")
        return
    
    print(f"\n✅ Generated {len(slips)} slips:")
    print(f"  - POWER slips: {len(slips[slips['type'] == 'POWER'])}")
    print(f"  - FLEX slips: {len(slips[slips['type'] == 'FLEX'])}")
    
    # Add metadata for bankroll optimizer
    slips = add_slip_metadata(slips, prepared_df)
    
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
    except Exception as e:
        bankroll = 1000
        print(f"\nUsing default bankroll: ${bankroll:,.2f}")
    
    # Calculate stakes
    print("\nCalculating optimal stakes...")
    
    # Get historical win rate
    historical_stats = {"overall_win_rate": 0.55}
    
    slips = bankroll_opt.optimize_slip_stakes(slips, bankroll, historical_stats)
    
    # Format stakes to 2 decimal places
    slips['stake'] = slips['stake'].round(2)
    
    # Show sample slips
    print("\n📋 Generated Betting Slips:")
    print("=" * 70)
    
    for i, (_, slip) in enumerate(slips.iterrows()):
        print(f"\n{slip['type']} Slip #{i+1}")
        print(f"Slip ID: {slip['slip_id']}")
        print(f"Stake: ${slip['stake']:.2f}")
        print(f"Expected Value: {slip['ev']:.3f}")
        print(f"Phase: {slip.get('phase', 'mixed')}")
        print(f"Confidence: {slip['confidence']:.1%}")
        
        # Show legs
        leg_ids = slip['legs'].split(',')
        print(f"\nLegs ({len(leg_ids)}):")
        for j, leg_id in enumerate(leg_ids):
            if leg_id in prepared_df['source_id'].values:
                bet = prepared_df[prepared_df['source_id'] == leg_id].iloc[0]
                # Determine over/under based on confidence
                over_under = "OVER" if bet['confidence'] > 0.5 else "UNDER"
                print(f"  {j+1}. {bet['player']} - {over_under} {bet['line']} {bet['stat']}")
        
        if i >= 2:  # Show first 3 slips
            break
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY:")
    total_stake = slips['stake'].sum()
    print(f"Total slips: {len(slips)}")
    print(f"Total stake: ${total_stake:.2f}")
    print(f"Bankroll utilization: {total_stake/bankroll*100:.1f}%")
    print(f"Average EV: {slips['ev'].mean():.3f}")
    
    # Phase distribution
    print("\nPhase distribution in slips:")
    phase_counts = slips['phase'].value_counts()
    for phase, count in phase_counts.items():
        if phase:  # Skip empty phases
            avg_stake = slips[slips['phase'] == phase]['stake'].mean()
            print(f"  {phase}: {count} slips, avg stake ${avg_stake:.2f}")
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"output/betting_slips_{timestamp}.csv"
    slips.to_csv(output_file, index=False)
    print(f"\nSlips saved to: {output_file}")
    
    # Create PrizePicks entry format
    print("\n🎯 PRIZEPICKS ENTRY FORMAT:")
    print("=" * 70)
    
    # Show top 2 POWER plays
    power_slips = slips[slips['type'] == 'POWER'].head(2)
    for i, (_, slip) in enumerate(power_slips.iterrows()):
        print(f"\nPOWER Play #{i+1} - ${slip['stake']:.2f}")
        leg_ids = slip['legs'].split(',')
        for leg_id in leg_ids:
            if leg_id in prepared_df['source_id'].values:
                bet = prepared_df[prepared_df['source_id'] == leg_id].iloc[0]
                over_under = "MORE" if bet['confidence'] > 0.5 else "LESS"
                print(f"  {bet['player']} - {bet['line']} {bet['stat']} - {over_under}")
    
    print("\n✅ Slip generation complete!")
    print("\n💡 Tips:")
    print("- Enter slips with highest EV first")
    print("- Monitor results to update win rates")
    print("- Adjust phase tracking for better optimization")

if __name__ == "__main__":
    main()
