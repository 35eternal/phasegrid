#!/usr/bin/env python3
"""
WNBA Prop Predictions Runner
Analyzes mapped props using PredictionEngine
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from core.prediction_engine import PredictionEngine

# Stat type mapping - updated for actual column names
STAT_MAP = {
    'Points': 'PTS',
    'Rebounds': 'REB',
    'Assists': 'AST',
    'Steals': 'STL',
    'Blocks': 'BLK',
    'Turnovers': 'TOV',
    '3-Pointers Made': 'FG3M',
    '3-PT Made': 'FG3M',
    'FG Made': 'FGM',
    'FT Made': 'FTM',
    'Fantasy Score': 'WNBA_FANTASY_PTS'
}

def main():
    # Load data
    props_df = pd.read_csv('data/wnba_props_mapped.csv')
    gamelogs_df = pd.read_csv('data/wnba_combined_gamelogs.csv')
    
    # Check available columns
    print(f"Gamelog columns: {gamelogs_df.columns.tolist()[:10]}...")
    
    # Find date column (could be 'Date', 'date', 'game_date', etc.)
    date_cols = [col for col in gamelogs_df.columns if 'date' in col.lower()]
    
    if date_cols:
        date_col = date_cols[0]
        gamelogs_df[date_col] = pd.to_datetime(gamelogs_df[date_col], format='%Y-%m-%d', errors='coerce')
    else:
        print("Warning: No date column found, using row order for recency")
        date_col = None
    
    # Initialize engine
    engine = PredictionEngine()
    
    # Results storage
    predictions = []
    skipped = []
    
    for _, prop in props_df.iterrows():
        bbref_id = prop['bbref_id']
        stat_type = prop['stat_type']
        line = prop['line']
        
        # Check if player exists in gamelogs
        # Always match by player name since gamelogs don't have bbref_id
        player_name = prop['player_name']
        player_logs = gamelogs_df[gamelogs_df['PLAYER_NAME'] == player_name]
        
        if player_logs.empty:
            skipped.append({
                'player_name': prop['player_name'],
                'bbref_id': bbref_id,
                'stat_type': stat_type,
                'reason': 'No game logs found'
            })
            continue
        
        # Map stat type
        mapped_stat = STAT_MAP.get(stat_type, stat_type)
        
        # Get recent games (last 10)
        if date_col:
            recent_logs = player_logs.nlargest(10, date_col)
        else:
            # If no date column, use last 10 rows
            recent_logs = player_logs.tail(10)
        
        # Calculate average for predicted value
        # Handle combined stats
        if '+' in stat_type:
            # Handle combined stats like "Pts+Rebs"
            stat_parts = stat_type.replace(' ', '').split('+')
            total = 0
            for part in stat_parts:
                if part == 'Pts':
                    if 'PTS' in recent_logs.columns:
                        total += recent_logs['PTS'].mean()
                elif part == 'Rebs':
                    if 'REB' in recent_logs.columns:
                        total += recent_logs['REB'].mean()
                elif part == 'Asts':
                    if 'AST' in recent_logs.columns:
                        total += recent_logs['AST'].mean()
            predicted_value = total
        elif mapped_stat in recent_logs.columns:
            predicted_value = recent_logs[mapped_stat].mean()
        else:
            skipped.append({
                'player_name': prop['player_name'],
                'bbref_id': bbref_id,
                'stat_type': stat_type,
                'reason': f'Stat {mapped_stat} not found'
            })
            continue
        
        # Run prediction engine
        try:
            result = engine.predict(bbref_id, stat_type)
            
            predictions.append({
                'player_name': prop['player_name'],
                'stat_type': stat_type,
                'line': line,
                'predicted_value': round(predicted_value, 2),
                'confidence_score': result.confidence_score,  # Access as attribute
                'volatility_score': result.volatility_score,  # Access as attribute
                'recommendation': result.recommendation,      # Access as attribute
                'bbref_id': bbref_id,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            skipped.append({
                'player_name': prop['player_name'],
                'bbref_id': bbref_id,
                'stat_type': stat_type,
                'reason': str(e)
            })
    
    # Save results
    predictions_df = pd.DataFrame(predictions)
    predictions_df.to_csv('data/wnba_prop_predictions.csv', index=False)
    
    # Save skipped props
    if skipped:
        skipped_df = pd.DataFrame(skipped)
        os.makedirs('output', exist_ok=True)
        skipped_df.to_csv('output/skipped_props.csv', index=False)
    
    print(f"✅ Processed {len(predictions)} props")
    print(f"⚠️  Skipped {len(skipped)} props")

if __name__ == "__main__":
    main()

# Sample Output:
# player_name,stat_type,line,predicted_value,confidence_score,volatility_score,recommendation,bbref_id,timestamp
# A'ja Wilson,Points,27.5,28.4,0.85,0.12,PASS,wilsoa'j01,2025-01-15T10:30:45.123456
# Breanna Stewart,Rebounds,8.5,9.1,0.78,0.18,PASS,stewabr01,2025-01-15T10:30:45.234567
# Sabrina Ionescu,Assists,5.5,6.2,0.72,0.22,PASS,ionessa01,2025-01-15T10:30:45.345678