#!/usr/bin/env python3
"""
TARS Module: Rolling Performance Trend Engine
Purpose: Calculate true rolling performance trends based on cycle phases
Integration: Drop-in replacement for placeholder trend calculation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

class RollingPerformanceTrend:
    """
    Calculates rolling performance trends relative to cycle phases.
    Replaces static 1.0 placeholder with actual performance deltas.
    """
    
    def __init__(self, lookback_games: int = 10, min_games: int = 3):
        self.lookback_games = lookback_games
        self.min_games = min_games
        self.phase_baselines = {}
        
    def calculate_player_trends(self, player_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate rolling performance trends for a single player.
        
        Args:
            player_df: DataFrame with columns [game_date, cycle_phase, actual_fantasy_points, minutes]
            
        Returns:
            DataFrame with added 'rolling_perf_trend' column
        """
        # Sort by date
        player_df = player_df.sort_values('game_date').copy()
        
        # Initialize trend column
        player_df['rolling_perf_trend'] = 1.0
        
        # Calculate phase-specific baselines
        phase_stats = self._calculate_phase_baselines(player_df)
        
        # Calculate rolling trends
        for idx in range(len(player_df)):
            if idx < self.min_games:
                continue
                
            # Get lookback window
            start_idx = max(0, idx - self.lookback_games)
            window = player_df.iloc[start_idx:idx]
            
            # Current phase
            current_phase = player_df.iloc[idx]['cycle_phase']
            
            # Calculate trend
            trend = self._calculate_trend(
                window, 
                current_phase, 
                phase_stats
            )
            
            player_df.loc[player_df.index[idx], 'rolling_perf_trend'] = trend
            
        return player_df
    
    def _calculate_phase_baselines(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate baseline performance for each phase."""
        phase_stats = {}
        
        for phase in df['cycle_phase'].unique():
            phase_data = df[df['cycle_phase'] == phase]
            
            if len(phase_data) >= 2:
                # Filter for games with significant minutes (>10)
                significant_games = phase_data[phase_data['minutes'] > 10]
                
                if len(significant_games) > 0:
                    phase_stats[phase] = {
                        'mean_fantasy': significant_games['actual_fantasy_points'].mean(),
                        'std_fantasy': significant_games['actual_fantasy_points'].std(),
                        'mean_minutes': significant_games['minutes'].mean(),
                        'game_count': len(significant_games)
                    }
                    
        return phase_stats
    
    def _calculate_trend(self, window: pd.DataFrame, current_phase: str, 
                        phase_stats: Dict) -> float:
        """
        Calculate performance trend for current game.
        
        Returns:
            Float representing performance multiplier (1.0 = baseline)
        """
        if current_phase not in phase_stats:
            return 1.0
            
        # Get recent performance in same phase
        same_phase_games = window[window['cycle_phase'] == current_phase]
        
        if len(same_phase_games) < 2:
            return 1.0
            
        # Calculate recent average (weighted by recency)
        weights = np.linspace(0.5, 1.0, len(same_phase_games))
        weighted_avg = np.average(
            same_phase_games['actual_fantasy_points'], 
            weights=weights
        )
        
        # Compare to phase baseline
        baseline = phase_stats[current_phase]['mean_fantasy']
        
        if baseline > 0:
            trend = weighted_avg / baseline
        else:
            trend = 1.0
            
        # Bound between 0.7 and 1.3 for stability
        return np.clip(trend, 0.7, 1.3)
    
    def process_all_players(self, gamelogs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process all players in the gamelogs DataFrame.
        
        Args:
            gamelogs_df: Full gamelogs with cycle phases
            
        Returns:
            DataFrame with added rolling_perf_trend column
        """
        print(f"[TARS] Processing rolling trends for {gamelogs_df['player_id'].nunique()} players...")
        
        # Group by player
        processed_dfs = []
        
        for player_id, player_data in gamelogs_df.groupby('player_id'):
            # Skip players with too few games
            if len(player_data) < self.min_games:
                player_data['rolling_perf_trend'] = 1.0
            else:
                player_data = self.calculate_player_trends(player_data)
                
            processed_dfs.append(player_data)
            
        # Combine all players
        result_df = pd.concat(processed_dfs, ignore_index=True)
        
        # Log summary statistics
        trend_stats = result_df.groupby('cycle_phase')['rolling_perf_trend'].agg(['mean', 'std', 'count'])
        print(f"\n[TARS] Trend Statistics by Phase:")
        print(trend_stats)
        
        return result_df

def integrate_rolling_trends(gamelogs_path: str, output_path: str) -> pd.DataFrame:
    """
    Main integration function to add rolling trends to existing gamelogs.
    
    Args:
        gamelogs_path: Path to gamelogs with cycle phases
        output_path: Path to save enhanced gamelogs
        
    Returns:
        Enhanced DataFrame
    """
    print(f"[TARS] Loading gamelogs from {gamelogs_path}")
    df = pd.read_csv(gamelogs_path)
    
    # Convert date column
    df['game_date'] = pd.to_datetime(df['game_date'])
    
    # Initialize trend calculator
    trend_engine = RollingPerformanceTrend(lookback_games=10, min_games=3)
    
    # Process all players
    enhanced_df = trend_engine.process_all_players(df)
    
    # Replace the static perf_trend with our calculated rolling_perf_trend
    if 'perf_trend' in enhanced_df.columns:
        enhanced_df['perf_trend'] = enhanced_df['rolling_perf_trend']
    else:
        enhanced_df['perf_trend'] = enhanced_df['rolling_perf_trend']
        
    # Drop temporary column
    enhanced_df = enhanced_df.drop('rolling_perf_trend', axis=1, errors='ignore')
    
    # Save enhanced gamelogs
    enhanced_df.to_csv(output_path, index=False)
    print(f"[TARS] Enhanced gamelogs saved to {output_path}")
    
    # Generate trend summary
    generate_trend_summary(enhanced_df)
    
    return enhanced_df

def generate_trend_summary(df: pd.DataFrame):
    """Generate summary statistics for trend analysis."""
    summary_path = 'output/rolling_trend_summary.csv'
    
    # Calculate phase-specific trend impacts
    phase_summary = df.groupby(['cycle_phase', 'cycle_risk_tag']).agg({
        'perf_trend': ['mean', 'std', 'min', 'max', 'count'],
        'actual_fantasy_points': 'mean'
    }).round(3)
    
    phase_summary.to_csv(summary_path)
    print(f"[TARS] Trend summary saved to {summary_path}")
    
    # Log high-impact findings
    high_volatility = df[df['perf_trend'] > 1.15]
    low_volatility = df[df['perf_trend'] < 0.85]
    
    print(f"\n[TARS] High Volatility Games (trend > 1.15): {len(high_volatility)}")
    print(f"[TARS] Low Volatility Games (trend < 0.85): {len(low_volatility)}")

if __name__ == "__main__":
    # Example integration
    integrate_rolling_trends(
        gamelogs_path='data/wnba_gamelogs_with_cycle_phases.csv',
        output_path='data/wnba_gamelogs_with_rolling_trends.csv'
    )