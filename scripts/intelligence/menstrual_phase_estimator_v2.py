#!/usr/bin/env python3
"""
TARS Enhanced Menstrual Phase Estimator V2
Complete replacement for menstrual_phase_estimator.py
Now includes rolling performance trends instead of static 1.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the rolling trend engine
from scripts.intelligence.rolling_performance_trend import RollingPerformanceTrend

def add_menstrual_intelligence(df, player_id_col='PLAYER_ID', date_col='GAME_DATE'):
    """
    Adds menstrual cycle phase estimation to player game logs.
    Now with enhanced rolling performance trends.
    """
    print(f"[TARS V2] Adding menstrual intelligence to {len(df)} game records...")
    
    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col], format='mixed', dayfirst=False)
    
    # Initialize new columns
    df['cycle_phase'] = ''
    df['cycle_day'] = 0
    df['phase_volatility'] = 1.0
    df['cycle_confidence'] = 0.5
    df['perf_trend'] = 1.0  # Will be replaced by rolling calculations
    df['cycle_risk_tag'] = ''
    
    # Process each player
    unique_players = df[player_id_col].unique()
    print(f"[TARS V2] Processing {len(unique_players)} unique players...")
    
    for player_id in unique_players:
        player_mask = df[player_id_col] == player_id
        player_games = df[player_mask].sort_values(date_col)
        
        if len(player_games) == 0:
            continue
            
        # Get first game date as cycle start
        first_game_date = player_games[date_col].min()
        
        # Calculate cycle info for each game
        for idx in player_games.index:
            game_date = df.loc[idx, date_col]
            days_since_start = (game_date - first_game_date).days
            
            # Calculate cycle day (1-28)
            cycle_day = (days_since_start % 28) + 1
            
            # Determine phase
            if cycle_day <= 5:
                phase = 'menstrual'
                volatility = 1.15
            elif cycle_day <= 13:
                phase = 'follicular'
                volatility = 0.95
            elif cycle_day <= 16:
                phase = 'ovulation'
                volatility = 0.85
            else:
                phase = 'luteal'
                volatility = 1.10
                
            # Set values
            df.loc[idx, 'cycle_phase'] = phase
            df.loc[idx, 'cycle_day'] = cycle_day
            df.loc[idx, 'phase_volatility'] = volatility
            
            # Confidence based on games played
            games_played = len(player_games[player_games[date_col] <= game_date])
            confidence = min(0.5 + (games_played * 0.02), 0.95)
            df.loc[idx, 'cycle_confidence'] = confidence
            
            # Risk tags
            if phase == 'menstrual' and volatility > 1.1:
                risk_tag = 'FADE_MENSTRUAL'
            elif phase == 'luteal' and cycle_day >= 22:
                risk_tag = 'FADE_LUTEAL'
            elif phase == 'ovulation':
                risk_tag = 'TARGET_OVULATION'
            elif phase == 'follicular' and cycle_day >= 10:
                risk_tag = 'TARGET_FOLLICULAR'
            else:
                risk_tag = 'NEUTRAL'
                
            df.loc[idx, 'cycle_risk_tag'] = risk_tag
    
    # Now calculate rolling performance trends
    print("[TARS V2] Calculating rolling performance trends...")
    trend_engine = RollingPerformanceTrend(lookback_games=10, min_games=3)
    
    # Process all players for trends
    processed_dfs = []
    for player_id in unique_players:
        player_data = df[df[player_id_col] == player_id].copy()
        
        if len(player_data) >= 3:
            # Calculate trends for this player
            player_data = trend_engine.calculate_player_trends(player_data)
            # Use the rolling_perf_trend as perf_trend
            if 'rolling_perf_trend' in player_data.columns:
                player_data['perf_trend'] = player_data['rolling_perf_trend']
                player_data = player_data.drop('rolling_perf_trend', axis=1)
        
        processed_dfs.append(player_data)
    
    # Combine all processed data
    df_with_trends = pd.concat(processed_dfs, ignore_index=True)
    
    # Sort back to original order
    df_with_trends = df_with_trends.sort_values([date_col, player_id_col])
    
    return df_with_trends

def update_props_with_cycle_info(props_df, gamelogs_df):
    """
    Updates betting props with cycle information and risk tags.
    """
    print("[TARS V2] Updating props with cycle intelligence...")
    
    # Ensure date formats match
    props_df['GAME_DATE'] = pd.to_datetime(props_df['GAME_DATE'])
    gamelogs_df['GAME_DATE'] = pd.to_datetime(gamelogs_df['GAME_DATE'])
    
    # Select cycle columns from gamelogs
    cycle_cols = ['PLAYER_ID', 'GAME_DATE', 'cycle_phase', 'cycle_day', 
                  'phase_volatility', 'cycle_confidence', 'perf_trend', 'cycle_risk_tag']
    
    # Merge cycle info into props
    props_enhanced = pd.merge(
        props_df,
        gamelogs_df[cycle_cols],
        on=['PLAYER_ID', 'GAME_DATE'],
        how='left'
    )
    
    # Fill any missing values
    props_enhanced['cycle_phase'] = props_enhanced['cycle_phase'].fillna('unknown')
    props_enhanced['phase_volatility'] = props_enhanced['phase_volatility'].fillna(1.0)
    props_enhanced['cycle_confidence'] = props_enhanced['cycle_confidence'].fillna(0.5)
    props_enhanced['perf_trend'] = props_enhanced['perf_trend'].fillna(1.0)
    props_enhanced['cycle_risk_tag'] = props_enhanced['cycle_risk_tag'].fillna('NEUTRAL')
    
    # Adjust predictions based on performance trend
    prediction_cols = ['predicted_points', 'predicted_rebounds', 'predicted_assists', 
                       'predicted_fantasy_points']
    
    for col in prediction_cols:
        if col in props_enhanced.columns:
            # Apply trend adjustment
            props_enhanced[f'{col}_raw'] = props_enhanced[col]
            props_enhanced[col] = props_enhanced[col] * props_enhanced['perf_trend']
            
    return props_enhanced

def generate_cycle_summary(df):
    """
    Generates summary statistics for cycle analysis.
    """
    print("[TARS V2] Generating cycle phase summary...")
    
    # Phase distribution
    phase_dist = df['cycle_phase'].value_counts()
    
    # Risk tag distribution
    risk_dist = df['cycle_risk_tag'].value_counts()
    
    # Average metrics by phase
    phase_stats = df.groupby('cycle_phase').agg({
        'WNBA_FANTASY_PTS': ['mean', 'std', 'count'],
        'phase_volatility': 'mean',
        'perf_trend': ['mean', 'std'],
        'MIN': 'mean'
    }).round(3)
    
    # Risk tag performance
    risk_stats = df.groupby('cycle_risk_tag').agg({
        'WNBA_FANTASY_PTS': ['mean', 'std', 'count'],
        'perf_trend': ['mean', 'std']
    }).round(3)
    
    # Save summaries
    summary_df = pd.DataFrame({
        'metric': ['total_games', 'unique_players', 'avg_trend', 'avg_volatility'],
        'value': [
            len(df),
            df['PLAYER_ID'].nunique(),
            df['perf_trend'].mean(),
            df['phase_volatility'].mean()
        ]
    })
    
    # Save all summaries
    phase_stats.to_csv('output/cycle_phase_summary_v2.csv')
    risk_stats.to_csv('output/cycle_risk_summary_v2.csv')
    summary_df.to_csv('output/cycle_overall_summary_v2.csv', index=False)
    
    print(f"\n[TARS V2] Phase Distribution:")
    print(phase_dist)
    print(f"\n[TARS V2] Risk Tag Distribution:")
    print(risk_dist)
    print(f"\n[TARS V2] Average Performance Trend: {df['perf_trend'].mean():.3f}")
    
    return phase_stats, risk_stats

def main():
    """
    Main execution function for enhanced menstrual phase estimation.
    """
    print("[TARS V2] Starting enhanced menstrual intelligence processing...")
    print(f"[TARS V2] Current time: {datetime.now()}")
    
    try:
        # Load game logs
        gamelogs_path = 'data/wnba_combined_gamelogs.csv'
        print(f"[TARS V2] Loading game logs from {gamelogs_path}")
        gamelogs_df = pd.read_csv(gamelogs_path)
        print(f"[TARS V2] Loaded {len(gamelogs_df)} game records")
        
        # Add menstrual intelligence with rolling trends
        gamelogs_enhanced = add_menstrual_intelligence(gamelogs_df)
        
        # Save enhanced game logs
        output_path = 'data/wnba_gamelogs_with_cycle_phases.csv'
        gamelogs_enhanced.to_csv(output_path, index=False)
        print(f"[TARS V2] Saved enhanced game logs to {output_path}")
        
        # Load and update props
        props_path = 'data/wnba_prop_predictions.csv'
        if os.path.exists(props_path):
            print(f"[TARS V2] Loading props from {props_path}")
            props_df = pd.read_csv(props_path)
            
            # Update props with cycle info
            props_enhanced = update_props_with_cycle_info(props_df, gamelogs_enhanced)
            
            # Save enhanced props
            props_output = 'data/wnba_clean_props_for_betting.csv'
            props_enhanced.to_csv(props_output, index=False)
            print(f"[TARS V2] Saved enhanced props to {props_output}")
        else:
            print(f"[TARS V2] Props file not found at {props_path}")
            
        # Generate summaries
        phase_stats, risk_stats = generate_cycle_summary(gamelogs_enhanced)
        
        print("\n[TARS V2] ✅ Enhanced menstrual intelligence processing complete!")
        print(f"[TARS V2] Performance trends now calculated using 10-game rolling windows")
        print(f"[TARS V2] Ready for backtesting with cycle_risk_backtest.py")
        
    except Exception as e:
        print(f"\n[TARS V2] ❌ Error in processing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
