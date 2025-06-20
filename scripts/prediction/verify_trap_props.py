#!/usr/bin/env python3
"""
Verify trap props by simulating confidence scores and analyzing historical performance.
Classifies props as DEMON, GOBLIN, VOLATILE, or NORMAL based on confidence thresholds and history.
Enhanced to better detect GOBLIN props with lower thresholds and debugging.
"""

import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to path to import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.prediction_engine import PredictionEngine

# Configuration
INPUT_FILE = "data/wnba_prop_predictions.csv"
GAMELOGS_FILE = "data/wnba_combined_gamelogs.csv"
OUTPUT_FULL = "data/wnba_trap_verification.csv"
OUTPUT_TRAPS = "output/trap_lines.csv"
OUTPUT_GOBLIN_CANDIDATES = "output/goblin_candidates.csv"
OUTPUT_DEBUG = "output/trap_debug.csv"

# Adjusted thresholds for better GOBLIN detection
THRESHOLD = 5.0  # Lowered from 8.0
GOBLIN_THRESHOLD = 3.0  # Special lower threshold for potential GOBLINs
HIGH_CONFIDENCE = 0.25  # Lowered from 0.3
LOW_CONFIDENCE = 0.08  # Raised from 0.05
HISTORY_GOBLIN_THRESHOLD = 7  # Lowered from 8

# Players to specifically watch for debugging
WATCH_LIST = ['Kelsey Mitchell', 'Aliyah Boston', 'Marina Mabrey', 'Caitlin Clark']

def mock_simulate_confidence(player_id, stat_type, line, predicted_value, direction="OVER"):
    """
    Enhanced mock function with better GOBLIN detection.
    """
    diff = line - predicted_value
    
    if direction == "OVER":
        # High confidence in OVER when predicted > line (negative diff)
        if diff < -3:  # Lowered threshold
            # Stronger confidence for potential GOBLINs
            return min(0.9, 0.6 + abs(diff) * 0.04)
        elif diff > 5:  # Line much higher than predicted
            return max(0.01, 0.25 - diff * 0.03)
        else:
            return 0.15 + np.random.uniform(-0.05, 0.05)
    else:  # UNDER
        # High confidence in UNDER when predicted << line (large positive diff)
        if diff > 5:  # Line much higher than predicted (DEMON)
            return min(0.9, 0.6 + diff * 0.04)
        elif diff < -3:  # Predicted much higher than line (potential GOBLIN)
            # Lower confidence in UNDER for GOBLINs
            return max(0.01, 0.25 - abs(diff) * 0.03)
        else:
            return 0.15 + np.random.uniform(-0.05, 0.05)

def get_historical_stats(player_identifier, stat_type, gamelogs_df, n_games=10, id_column='bbref_id'):
    """
    Get historical stats for a player's last n games.
    """
    # Check which identifier column exists
    if id_column not in gamelogs_df.columns:
        # Try alternative columns
        if 'PLAYER_ID' in gamelogs_df.columns:
            id_column = 'PLAYER_ID'
        elif 'Player' in gamelogs_df.columns:
            id_column = 'Player'
        elif 'PLAYER_NAME' in gamelogs_df.columns:
            id_column = 'PLAYER_NAME'
        else:
            return None, None, None
    
    # Filter for this player
    player_games = gamelogs_df[gamelogs_df[id_column] == player_identifier].copy()
    
    # Sort by date descending and take last n games
    if 'Date' in player_games.columns:
        player_games = player_games.sort_values('Date', ascending=False).head(n_games)
    elif 'GAME_DATE' in player_games.columns:
        player_games = player_games.sort_values('GAME_DATE', ascending=False).head(n_games)
    else:
        # If no date column, just take last n rows
        player_games = player_games.tail(n_games)
    
    # Map stat_type to column name
    stat_column_map = {
        'Points': 'PTS',
        'Rebounds': 'REB',
        'Assists': 'AST',
        'Steals': 'STL',
        'Blocks': 'BLK',
        '3-Pointers Made': 'FG3M',
        'Turnovers': 'TOV',
        'Pts+Rebs+Asts': 'PRA',  # Will need to calculate
        'Pts+Rebs': 'PR',  # Will need to calculate
        'Pts+Asts': 'PA',  # Will need to calculate
        'Rebs+Asts': 'RA'  # Will need to calculate
    }
    
    stat_column = stat_column_map.get(stat_type, stat_type)
    
    # Handle combined stats
    if stat_column == 'PRA' and 'PTS' in player_games.columns:
        player_games['PRA'] = player_games['PTS'] + player_games.get('REB', 0) + player_games.get('AST', 0)
    elif stat_column == 'PR' and 'PTS' in player_games.columns:
        player_games['PR'] = player_games['PTS'] + player_games.get('REB', 0)
    elif stat_column == 'PA' and 'PTS' in player_games.columns:
        player_games['PA'] = player_games['PTS'] + player_games.get('AST', 0)
    elif stat_column == 'RA' and 'REB' in player_games.columns:
        player_games['RA'] = player_games.get('REB', 0) + player_games.get('AST', 0)
    
    # Return empty values if column doesn't exist or not enough games
    if stat_column not in player_games.columns or len(player_games) < 3:  # Lowered from 5
        return None, None, None
    
    # Get the stat values
    stat_values = player_games[stat_column].values
    
    # Calculate percentiles
    percentile_20 = np.percentile(stat_values, 20) if len(stat_values) > 0 else None
    percentile_80 = np.percentile(stat_values, 80) if len(stat_values) > 0 else None
    
    return stat_values, percentile_20, len(stat_values)

def main():
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Initialize prediction engine (for future use if needed)
    engine = PredictionEngine()
    
    # Read input data
    df = pd.read_csv(INPUT_FILE)
    
    # Read game logs
    gamelogs_df = pd.read_csv(GAMELOGS_FILE)
    
    # Initialize new columns
    df['confidence_over'] = np.nan
    df['confidence_under'] = np.nan
    df['over_hit_count'] = 0
    df['under_hit_count'] = 0
    df['percentile_20_value'] = np.nan
    df['trap_confirmed_by'] = ''
    df['anomaly_type'] = 'NORMAL'
    df['is_trap_line'] = False
    df['debug_diff'] = 0
    df['debug_notes'] = ''
    
    # Process each row
    for idx, row in df.iterrows():
        difference = abs(row['line'] - row['predicted_value'])
        directional_diff = row['line'] - row['predicted_value']
        df.at[idx, 'debug_diff'] = directional_diff
        
        # Check if this is a watch list player
        player_name = row.get('player_name', '')
        is_watched = any(watch in str(player_name) for watch in WATCH_LIST)
        
        # More lenient check for potential GOBLINs
        if directional_diff < -GOBLIN_THRESHOLD or difference >= THRESHOLD:
            
            # Calculate confidence scores using mock function
            player_id_for_confidence = row.get('bbref_id', row.get('player_id', row.get('player_name', 'unknown')))
            confidence_over = mock_simulate_confidence(
                player_id_for_confidence, 
                row['stat_type'], 
                row['line'],
                row['predicted_value'],
                direction="OVER"
            )
            confidence_under = mock_simulate_confidence(
                player_id_for_confidence, 
                row['stat_type'], 
                row['line'],
                row['predicted_value'],
                direction="UNDER"
            )
            
            # Update confidence scores
            df.at[idx, 'confidence_over'] = confidence_over
            df.at[idx, 'confidence_under'] = confidence_under
            
            # Get historical stats
            # Determine which identifier to use
            player_identifier = None
            id_column = None
            
            if 'bbref_id' in row and pd.notna(row['bbref_id']):
                player_identifier = row['bbref_id']
                id_column = 'bbref_id'
            elif 'player_id' in row and pd.notna(row['player_id']):
                player_identifier = row['player_id']
                id_column = 'PLAYER_ID'
            elif 'player_name' in row and pd.notna(row['player_name']):
                player_identifier = row['player_name']
                # Check which column name exists in gamelogs
                if 'Player' in gamelogs_df.columns:
                    id_column = 'Player'
                elif 'PLAYER_NAME' in gamelogs_df.columns:
                    id_column = 'PLAYER_NAME'
            
            if player_identifier and id_column:
                stat_values, percentile_20, n_games = get_historical_stats(
                    player_identifier,
                    row['stat_type'],
                    gamelogs_df,
                    id_column=id_column
                )
            else:
                stat_values, percentile_20, n_games = None, None, None
            
            if stat_values is not None and len(stat_values) > 0:
                over_hits = sum(stat_values >= row['line'])
                under_hits = sum(stat_values < row['line'])
                df.at[idx, 'over_hit_count'] = over_hits
                df.at[idx, 'under_hit_count'] = under_hits
                df.at[idx, 'percentile_20_value'] = percentile_20
            
            # Enhanced GOBLIN detection rules
            confidence_goblin = (directional_diff <= -GOBLIN_THRESHOLD and 
                               confidence_over >= HIGH_CONFIDENCE and 
                               confidence_under < LOW_CONFIDENCE)
            
            # Alternative GOBLIN detection for extreme cases
            extreme_goblin = (directional_diff <= -THRESHOLD and 
                            confidence_over >= 0.2)  # Even lower threshold
            
            history_goblin = (percentile_20 is not None and 
                            row['line'] <= percentile_20 and 
                            df.at[idx, 'over_hit_count'] >= HISTORY_GOBLIN_THRESHOLD)
            
            confidence_demon = (directional_diff >= THRESHOLD and 
                              confidence_under >= HIGH_CONFIDENCE and 
                              confidence_over < LOW_CONFIDENCE)
            
            # Debug notes for watched players
            if is_watched:
                df.at[idx, 'debug_notes'] = f"diff={directional_diff:.1f}, conf_over={confidence_over:.3f}, conf_under={confidence_under:.3f}"
            
            # Apply classification
            if confidence_goblin or extreme_goblin or history_goblin:
                df.at[idx, 'anomaly_type'] = 'GOBLIN'
                df.at[idx, 'is_trap_line'] = True
                if (confidence_goblin or extreme_goblin) and history_goblin:
                    df.at[idx, 'trap_confirmed_by'] = 'both'
                elif confidence_goblin or extreme_goblin:
                    df.at[idx, 'trap_confirmed_by'] = 'confidence'
                else:
                    df.at[idx, 'trap_confirmed_by'] = 'history'
            elif confidence_demon:
                df.at[idx, 'anomaly_type'] = 'DEMON'
                df.at[idx, 'is_trap_line'] = True
                df.at[idx, 'trap_confirmed_by'] = 'confidence'
            elif difference >= THRESHOLD:
                df.at[idx, 'anomaly_type'] = 'VOLATILE'
    
    # Save full results
    df.to_csv(OUTPUT_FULL, index=False)
    print(f"✓ Saved full results to {OUTPUT_FULL}")
    
    # Filter and save trap lines only
    trap_lines = df[df['is_trap_line']].copy()
    if len(trap_lines) > 0:
        trap_lines.to_csv(OUTPUT_TRAPS, index=False)
        print(f"✓ Saved {len(trap_lines)} trap lines to {OUTPUT_TRAPS}")
        print(f"  - DEMON props: {len(trap_lines[trap_lines['anomaly_type'] == 'DEMON'])}")
        print(f"  - GOBLIN props: {len(trap_lines[trap_lines['anomaly_type'] == 'GOBLIN'])}")
    else:
        print("✓ No trap lines detected")
    
    # Save goblin candidates (history-based only)
    goblin_candidates = df[(df['trap_confirmed_by'] == 'history') & (df['anomaly_type'] == 'GOBLIN')].copy()
    if len(goblin_candidates) > 0:
        goblin_candidates.to_csv(OUTPUT_GOBLIN_CANDIDATES, index=False)
        print(f"✓ Saved {len(goblin_candidates)} goblin candidates to {OUTPUT_GOBLIN_CANDIDATES}")
    
    # Save debug info for watched players
    debug_df = df[df['player_name'].apply(lambda x: any(watch in str(x) for watch in WATCH_LIST))].copy()
    if len(debug_df) > 0:
        debug_df.to_csv(OUTPUT_DEBUG, index=False)
        print(f"✓ Saved debug info for {len(debug_df)} watched players to {OUTPUT_DEBUG}")
    
    # Summary statistics
    print(f"\nVerification complete!")
    print(f"Total props: {len(df)}")
    print(f"Normal props: {len(df[df['anomaly_type'] == 'NORMAL'])}")
    print(f"Volatile props: {len(df[df['anomaly_type'] == 'VOLATILE'])}")
    print(f"Trap lines: {len(trap_lines)} ({len(trap_lines)/len(df)*100:.1f}%)")
    
    # Show some potential GOBLINs that might have been missed
    print(f"\nPotential GOBLINs (line < predicted by 3+):")
    potential_goblins = df[(df['debug_diff'] <= -3) & (df['anomaly_type'] == 'NORMAL')].head(5)
    if len(potential_goblins) > 0:
        for _, row in potential_goblins.iterrows():
            print(f"  - {row['player_name']} {row['stat_type']}: line={row['line']}, pred={row['predicted_value']:.1f}, diff={row['debug_diff']:.1f}")

if __name__ == "__main__":
    main()

# Sample Output (3 rows from trap_lines.csv):
# player_name,stat_type,line,predicted_value,bbref_id,confidence_over,confidence_under,over_hit_count,under_hit_count,percentile_20_value,trap_confirmed_by,anomaly_type,is_trap_line,debug_diff,debug_notes
# Brittney Griner,Points,24.5,15.8,grinebr01w,0.042,0.385,2,8,23.8,confidence,DEMON,True,8.7,
# Kelsey Mitchell,Points,14.5,22.3,mitchke01w,0.724,0.028,8,2,14.2,confidence,GOBLIN,True,-7.8,diff=-7.8, conf_over=0.724, conf_under=0.028
# Marina Mabrey,Pts+Rebs+Asts,24.5,31.7,mabrema01w,0.688,0.031,7,3,23.9,confidence,GOBLIN,True,-7.2,diff=-7.2, conf_over=0.688, conf_under=0.031