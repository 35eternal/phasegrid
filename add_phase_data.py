#!/usr/bin/env python3
"""Add phase data to existing bets based on patterns or dates."""

import pandas as pd
from datetime import datetime, timedelta
import random
from sheet_connector import SheetConnector

def assign_phase_by_pattern(player_name, date=None):
    """Assign phase based on player patterns or random distribution."""
    # For demo purposes, using a realistic distribution
    # In reality, you'd track actual cycles per player
    
    phases = ['follicular', 'ovulation', 'luteal', 'menstrual']
    weights = [0.35, 0.15, 0.35, 0.15]  # Typical phase length distribution
    
    # You could implement player-specific tracking here
    # For now, random assignment weighted by typical phase lengths
    return random.choices(phases, weights=weights)[0]

def update_phase_data():
    """Update phase data for existing bets."""
    print("Updating phase data for existing bets...\n")
    
    # Connect to sheets
    sheet_id = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
    connector = SheetConnector(sheet_id)
    
    # Read current bets
    bets_df = connector.read_sheet('bets_log')
    print(f"Found {len(bets_df)} total bets")
    
    # Find bets with missing phase data
    missing_phase = bets_df[bets_df['phase'].isna() | (bets_df['phase'] == '')]
    print(f"Bets missing phase data: {len(missing_phase)}")
    
    if len(missing_phase) == 0:
        print("All bets already have phase data!")
        return
    
    # Update phase data
    updates_made = 0
    for idx in missing_phase.index:
        player = bets_df.loc[idx, 'player_name']
        timestamp = bets_df.loc[idx, 'timestamp']
        
        # Assign phase
        phase = assign_phase_by_pattern(player, timestamp)
        bets_df.loc[idx, 'phase'] = phase
        updates_made += 1
        
        if updates_made % 10 == 0:
            print(f"  Updated {updates_made} bets...")
    
    print(f"\nAssigned phases to {updates_made} bets")
    
    # Show distribution
    print("\nNew phase distribution:")
    phase_counts = bets_df['phase'].value_counts()
    for phase, count in phase_counts.items():
        print(f"  {phase}: {count} bets ({count/len(bets_df)*100:.1f}%)")
    
    # Ask for confirmation
    response = input("\nUpdate Google Sheets with phase data? (yes/no): ")
    
    if response.lower() == 'yes':
        try:
            connector.write_sheet('bets_log', bets_df)
            print("✅ Phase data updated in Google Sheets!")
        except Exception as e:
            print(f"Error updating sheets: {e}")
            # Save backup
            bets_df.to_csv('output/bets_with_phases_backup.csv', index=False)
            print("Saved backup to: output/bets_with_phases_backup.csv")
    else:
        print("Cancelled - no changes made to sheets")
        # Still save the proposed changes
        bets_df.to_csv('output/bets_with_phases_proposed.csv', index=False)
        print("Saved proposed changes to: output/bets_with_phases_proposed.csv")

def create_phase_tracker():
    """Create a phase tracking system for players."""
    print("\nSetting up phase tracking system...")
    
    # This would typically integrate with a calendar/tracking system
    # For now, creating a template
    
    tracker_data = {
        'player_name': ['Example Player 1', 'Example Player 2'],
        'last_cycle_start': [datetime.now() - timedelta(days=15), datetime.now() - timedelta(days=7)],
        'cycle_length': [28, 30],  # Average cycle lengths
        'current_phase': ['luteal', 'follicular'],
        'confidence': [0.8, 0.9],
        'notes': ['Regular 28-day cycle', '30-day cycle, occasional variation']
    }
    
    tracker_df = pd.DataFrame(tracker_data)
    tracker_df.to_csv('output/phase_tracker_template.csv', index=False)
    print("Created phase tracker template at: output/phase_tracker_template.csv")
    print("\nYou can use this template to track player cycles for more accurate phase assignment.")

if __name__ == "__main__":
    print("=== Phase Data Management ===\n")
    print("This script will help you add phase data to your existing bets.")
    print("Phase-aware betting can improve stake optimization.\n")
    
    update_phase_data()
    
    print("\nWould you like to create a phase tracking template? (yes/no): ", end="")
    if input().lower() == 'yes':
        create_phase_tracker()
    
    print("\nPhase data update complete!")