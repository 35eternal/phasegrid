#!/usr/bin/env python3
"""
cycle_dip_detector.py - Advanced WNBA Performance Dip Detection System
Detects time-based player performance patterns for betting intelligence.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class CycleDipDetector:
    """
    Advanced system for detecting cyclical performance dips in WNBA players.
    Analyzes rolling averages, trend patterns, and potential periodic cycles.
    """
    
    def __init__(self, min_games=10, cycle_length=28, drop_threshold=0.20):
        """
        Initialize the detector with configurable parameters.
        
        Args:
            min_games (int): Minimum games required for analysis
            cycle_length (int): Days to check for periodic patterns (default 28)
            drop_threshold (float): Percentage drop to consider significant (default 20%)
        """
        self.min_games = min_games
        self.cycle_length = cycle_length
        self.drop_threshold = drop_threshold
        self.results = None
        
    def load_data(self, filepath):
        """
        Load and validate WNBA game log data.
        
        Args:
            filepath (str): Path to wnba_2024_gamelogs.csv
            
        Returns:
            pd.DataFrame: Cleaned and validated game log data
        """
        print(f"Loading data from {filepath}...")
        
        try:
            df = pd.read_csv(filepath)
            print(f"Loaded {len(df)} game logs")
            
            # Map column names to expected format
            column_mapping = {
                'PLAYER_NAME': 'player',
                'GAME_DATE': 'date', 
                'TEAM_ABBREVIATION': 'team',
                'MATCHUP': 'opponent',
                'MIN': 'minutes',
                'PTS': 'points',
                'AST': 'assists', 
                'REB': 'rebounds'
            }
            
            # Rename columns to standard format
            df = df.rename(columns=column_mapping)
            print("✅ Mapped column names to standard format")
            
            # Validate required columns now exist
            required_cols = ['player', 'date', 'team', 'opponent', 'minutes', 
                           'points', 'assists', 'rebounds']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"Warning: Still missing columns {missing_cols}")
                print(f"Available columns: {list(df.columns)}")
                return pd.DataFrame()  # Return empty if critical columns missing
            
            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Convert minutes from MM:SS format to decimal if needed
            if df['minutes'].dtype == 'object':
                df['minutes'] = df['minutes'].apply(self._convert_minutes_to_decimal)
            
            # Create fantasy_points using WNBA_FANTASY_PTS if available, otherwise calculate
            if 'WNBA_FANTASY_PTS' in df.columns:
                df['fantasy_points'] = df['WNBA_FANTASY_PTS']
                print("✅ Used WNBA_FANTASY_PTS column")
            else:
                df['fantasy_points'] = (df['points'] + 
                                      df['assists'] * 1.5 + 
                                      df['rebounds'] * 1.2)
                print("✅ Created fantasy_points column")
            
            # Clean opponent field (remove @ symbol and team abbrev)
            df['opponent'] = df['opponent'].str.replace('@', '').str.replace('vs.', '').str.strip()
            df['opponent'] = df['opponent'].str.split().str[-1]  # Get last part (opponent team)
            
            # Filter players with minimum games
            player_counts = df['player'].value_counts()
            valid_players = player_counts[player_counts >= self.min_games].index
            df = df[df['player'].isin(valid_players)]
            
            print(f"✅ After filtering: {len(df)} games for {len(valid_players)} players")
            
            return df.sort_values(['player', 'date']).reset_index(drop=True)
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def _convert_minutes_to_decimal(self, minutes_str):
        """Convert MM:SS format to decimal minutes."""
        try:
            if pd.isna(minutes_str) or minutes_str == '':
                return 0.0
            if ':' in str(minutes_str):
                parts = str(minutes_str).split(':')
                return float(parts[0]) + float(parts[1]) / 60.0
            else:
                return float(minutes_str)
        except:
            return 0.0
    
    def calculate_rolling_stats(self, df):
        """
        Calculate rolling averages for key performance metrics.
        
        Args:
            df (pd.DataFrame): Game log data
            
        Returns:
            pd.DataFrame: Data with rolling averages added
        """
        print("Calculating rolling averages...")
        
        # Define key stats to analyze
        key_stats = ['points', 'assists', 'rebounds', 'fantasy_points', 'minutes']
        rolling_windows = [3, 5, 10]
        
        df = df.copy()
        
        for player in df['player'].unique():
            player_mask = df['player'] == player
            player_data = df[player_mask].copy()
            
            # Calculate player's season averages
            for stat in key_stats:
                df.loc[player_mask, f'{stat}_season_avg'] = player_data[stat].mean()
            
            # Calculate rolling averages
            for window in rolling_windows:
                for stat in key_stats:
                    rolling_avg = player_data[stat].rolling(
                        window=window, min_periods=1
                    ).mean()
                    df.loc[player_mask, f'{stat}_roll_{window}'] = rolling_avg
        
        return df
    
    def detect_performance_trends(self, df):
        """
        Detect performance trends and significant drops.
        
        Args:
            df (pd.DataFrame): Data with rolling averages
            
        Returns:
            pd.DataFrame: Data with trend analysis added
        """
        print("Detecting performance trends...")
        
        df = df.copy()
        key_stats = ['points', 'assists', 'rebounds', 'fantasy_points']
        
        for player in df['player'].unique():
            player_mask = df['player'] == player
            player_data = df[player_mask].copy()
            
            if len(player_data) < 3:
                continue
                
            # Analyze each stat for trends
            for stat in key_stats:
                season_avg = player_data[f'{stat}_season_avg'].iloc[0]
                recent_avg = player_data[f'{stat}_roll_3']
                
                # Calculate percentage drop from season average
                pct_drop = (season_avg - recent_avg) / season_avg
                df.loc[player_mask, f'{stat}_pct_drop'] = pct_drop
                
                # Detect consecutive declining games
                stat_values = player_data[stat].values
                declining_streaks = self._find_declining_streaks(stat_values)
                df.loc[player_mask, f'{stat}_decline_streak'] = declining_streaks
        
        return df
    
    def _find_declining_streaks(self, values):
        """
        Find consecutive declining values in a series.
        
        Args:
            values (np.array): Array of statistical values
            
        Returns:
            np.array: Array indicating streak length at each position
        """
        streaks = np.zeros_like(values)
        current_streak = 0
        
        for i in range(1, len(values)):
            if values[i] < values[i-1]:
                current_streak += 1
            else:
                current_streak = 0
            streaks[i] = current_streak
            
        return streaks
    
    def detect_periodic_cycles(self, df):
        """
        Detect potential periodic performance cycles (e.g., 28-day patterns).
        
        Args:
            df (pd.DataFrame): Game log data
            
        Returns:
            pd.DataFrame: Data with cycle analysis added
        """
        print(f"Detecting {self.cycle_length}-day periodic cycles...")
        
        df = df.copy()
        df['cycle_phase'] = 'unknown'
        df['days_in_cycle'] = 0
        df['cycle_performance_score'] = 0.0
        
        for player in df['player'].unique():
            player_mask = df['player'] == player
            player_data = df[player_mask].copy()
            
            if len(player_data) < self.cycle_length:
                continue
            
            # Calculate days since first game for this player
            first_date = player_data['date'].min()
            player_data['days_since_start'] = (player_data['date'] - first_date).dt.days
            
            # Map to cycle position (0-27 for 28-day cycle)
            cycle_position = player_data['days_since_start'] % self.cycle_length
            
            # Analyze performance by cycle position
            performance_by_cycle = self._analyze_cycle_performance(
                player_data, cycle_position
            )
            
            df.loc[player_mask, 'days_in_cycle'] = cycle_position
            df.loc[player_mask, 'cycle_performance_score'] = performance_by_cycle
            
        return df
    
    def _analyze_cycle_performance(self, player_data, cycle_position):
        """
        Analyze performance patterns within cycle positions.
        
        Args:
            player_data (pd.DataFrame): Single player's data
            cycle_position (pd.Series): Position within cycle (0-27)
            
        Returns:
            np.array: Performance scores for each game
        """
        # Use fantasy_points as primary performance metric
        performance_scores = np.zeros(len(player_data))
        
        # Calculate average performance for each cycle position
        for pos in range(self.cycle_length):
            pos_mask = cycle_position == pos
            if pos_mask.any():
                pos_avg = player_data.loc[pos_mask, 'fantasy_points'].mean()
                season_avg = player_data['fantasy_points'].mean()
                
                # Score relative to season average
                relative_score = (pos_avg - season_avg) / season_avg
                performance_scores[pos_mask] = relative_score
        
        return performance_scores
    
    def label_trend_phases(self, df):
        """
        Label each game with its trend phase.
        
        Args:
            df (pd.DataFrame): Data with trend analysis
            
        Returns:
            pd.DataFrame: Data with trend phases labeled
        """
        print("Labeling trend phases...")
        
        df = df.copy()
        df['trend_phase'] = 'Stable'
        df['games_in_trend'] = 1
        df['dip_type'] = 'none'
        
        for player in df['player'].unique():
            player_mask = df['player'] == player
            player_data = df[player_mask].copy().reset_index(drop=True)
            
            if len(player_data) < 5:
                continue
            
            # Analyze fantasy points trend
            fp_values = player_data['fantasy_points'].values
            fp_roll_3 = player_data['fantasy_points_roll_3'].values
            fp_season_avg = player_data['fantasy_points_season_avg'].iloc[0]
            
            phases = self._classify_trend_phases(
                fp_values, fp_roll_3, fp_season_avg
            )
            
            # Classify dip types
            dip_types = self._classify_dip_types(
                player_data, phases
            )
            
            df.loc[player_mask, 'trend_phase'] = phases
            df.loc[player_mask, 'dip_type'] = dip_types
            
            # Calculate games in current trend
            trend_lengths = self._calculate_trend_lengths(phases)
            df.loc[player_mask, 'games_in_trend'] = trend_lengths
            
        return df
    
    def _classify_trend_phases(self, values, rolling_avg, season_avg):
        """
        Classify each game into trend phases.
        
        Args:
            values (np.array): Raw statistical values
            rolling_avg (np.array): Rolling average values
            season_avg (float): Season average
            
        Returns:
            list: Trend phase labels for each game
        """
        phases = ['Stable'] * len(values)
        
        for i in range(2, len(values)):
            current_val = rolling_avg[i]
            prev_val = rolling_avg[i-1]
            prev2_val = rolling_avg[i-2] if i >= 2 else rolling_avg[i-1]
            
            # Calculate trend direction
            recent_trend = current_val - prev_val
            medium_trend = current_val - prev2_val
            
            # Relative to season average
            vs_season = (current_val - season_avg) / season_avg
            
            # Classify phases
            if vs_season > 0.15 and recent_trend > 0:
                phases[i] = 'Peak'
            elif vs_season > 0.05 and recent_trend > 0:
                phases[i] = 'Ascending'
            elif vs_season < -0.15 and recent_trend < 0:
                phases[i] = 'Trough'
            elif vs_season < -0.05 and recent_trend < 0:
                phases[i] = 'Descending'
            elif vs_season < -0.1 and recent_trend > 0:
                phases[i] = 'Recovery'
            else:
                phases[i] = 'Stable'
                
        return phases
    
    def _classify_dip_types(self, player_data, phases):
        """
        Classify the type of performance dip.
        
        Args:
            player_data (pd.DataFrame): Single player's data
            phases (list): Trend phase labels
            
        Returns:
            list: Dip type classifications
        """
        dip_types = ['none'] * len(player_data)
        
        for i, phase in enumerate(phases):
            if phase in ['Descending', 'Trough']:
                # Check for cycle-related patterns
                if abs(player_data.iloc[i]['cycle_performance_score']) > 0.1:
                    dip_types[i] = 'cycle'
                # Check for fatigue patterns (high minutes recently)
                elif i >= 3:
                    recent_minutes = player_data.iloc[i-3:i+1]['minutes'].mean()
                    season_minutes = player_data['minutes'].mean()
                    if recent_minutes > season_minutes * 1.2:
                        dip_types[i] = 'fatigue'
                    else:
                        dip_types[i] = 'unknown'
                else:
                    dip_types[i] = 'unknown'
        
        return dip_types
    
    def _calculate_trend_lengths(self, phases):
        """
        Calculate how many consecutive games in current trend.
        
        Args:
            phases (list): Trend phase labels
            
        Returns:
            list: Number of games in current trend
        """
        trend_lengths = [1] * len(phases)
        
        for i in range(1, len(phases)):
            if phases[i] == phases[i-1]:
                trend_lengths[i] = trend_lengths[i-1] + 1
            else:
                trend_lengths[i] = 1
                
        return trend_lengths
    
    def generate_summary_stats(self, df):
        """
        Generate summary statistics for the analysis.
        
        Args:
            df (pd.DataFrame): Processed data
            
        Returns:
            dict: Summary statistics
        """
        total_games = len(df)
        total_players = df['player'].nunique()
        
        # Phase distribution
        phase_counts = df['trend_phase'].value_counts()
        
        # Dip type distribution
        dip_counts = df['dip_type'].value_counts()
        
        # Players currently in concerning phases
        concerning_phases = ['Descending', 'Trough']
        concerning_players = df[
            df['trend_phase'].isin(concerning_phases)
        ]['player'].nunique()
        
        return {
            'total_games': total_games,
            'total_players': total_players,
            'phase_distribution': phase_counts.to_dict(),
            'dip_type_distribution': dip_counts.to_dict(),
            'concerning_players': concerning_players,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def export_results(self, df, output_file='detected_performance_dips.csv'):
        """
        Export results to CSV file.
        
        Args:
            df (pd.DataFrame): Processed data
            output_file (str): Output filename
        """
        print(f"Exporting results to {output_file}...")
        
        # Select relevant columns for export
        export_columns = [
            'player', 'date', 'team', 'opponent',
            'points', 'assists', 'rebounds', 'fantasy_points', 'minutes',
            'trend_phase', 'games_in_trend', 'dip_type',
            'fantasy_points_roll_3', 'fantasy_points_pct_drop',
            'cycle_performance_score', 'days_in_cycle'
        ]
        
        # Filter to include only available columns
        available_columns = [col for col in export_columns if col in df.columns]
        export_df = df[available_columns].copy()
        
        # Add percentage drop calculation
        if 'fantasy_points_pct_drop' in df.columns:
            export_df['percent_drop_from_avg'] = (
                export_df['fantasy_points_pct_drop'] * 100
            ).round(1)
        
        # Sort by date (most recent first)
        export_df = export_df.sort_values('date', ascending=False)
        
        export_df.to_csv(output_file, index=False)
        print(f"Exported {len(export_df)} records")
    
    def print_top_concerns(self, df, top_n=10):
        """
        Print top concerning players to terminal.
        
        Args:
            df (pd.DataFrame): Processed data
            top_n (int): Number of top concerns to show
        """
        print(f"\n{'='*60}")
        print(f"TOP {top_n} CONCERNING PERFORMANCE TRENDS")
        print(f"{'='*60}")
        
        # Filter to concerning phases
        concerning = df[
            df['trend_phase'].isin(['Descending', 'Trough'])
        ].copy()
        
        if len(concerning) == 0:
            print("No concerning trends detected.")
            return
        
        # Get most recent game for each player in concerning phase
        latest_concerns = concerning.groupby('player').apply(
            lambda x: x.loc[x['date'].idxmax()]
        ).reset_index(drop=True)
        
        # Sort by severity (combination of trend length and drop percentage)
        if 'fantasy_points_pct_drop' in latest_concerns.columns:
            latest_concerns['severity_score'] = (
                latest_concerns['games_in_trend'] * 
                latest_concerns['fantasy_points_pct_drop'] * 100
            )
            latest_concerns = latest_concerns.sort_values(
                'severity_score', ascending=False
            )
        else:
            latest_concerns = latest_concerns.sort_values(
                'games_in_trend', ascending=False
            )
        
        # Display top concerns
        for i, (_, row) in enumerate(latest_concerns.head(top_n).iterrows()):
            print(f"\n{i+1}. {row['player']} ({row['team']})")
            print(f"   Status: {row['trend_phase']} for {row['games_in_trend']} games")
            print(f"   Dip Type: {row['dip_type']}")
            print(f"   Last Game: {row['date'].strftime('%Y-%m-%d')}")
            
            if 'fantasy_points_pct_drop' in row.index:
                drop_pct = row['fantasy_points_pct_drop'] * 100
                print(f"   Performance Drop: {drop_pct:.1f}% below season avg")
            
            print(f"   Recent Fantasy Points: {row['fantasy_points']:.1f}")
            
            if 'fantasy_points_roll_3' in row.index:
                print(f"   3-Game Average: {row['fantasy_points_roll_3']:.1f}")
    
    def run_analysis(self, filepath, output_file='detected_performance_dips.csv'):
        """
        Run the complete analysis pipeline.
        
        Args:
            filepath (str): Path to input data file
            output_file (str): Path for output CSV file
            
        Returns:
            pd.DataFrame: Processed analysis results
        """
        print(f"Starting WNBA Performance Dip Analysis")
        print(f"Parameters: min_games={self.min_games}, cycle_length={self.cycle_length}")
        print(f"Drop threshold: {self.drop_threshold*100:.0f}%")
        print("-" * 50)
        
        # Load and process data
        df = self.load_data(filepath)
        df = self.calculate_rolling_stats(df)
        df = self.detect_performance_trends(df)
        df = self.detect_periodic_cycles(df)
        df = self.label_trend_phases(df)
        
        # Generate summary and export
        summary = self.generate_summary_stats(df)
        print(f"\nAnalysis Summary:")
        print(f"  Total Games: {summary['total_games']:,}")
        print(f"  Total Players: {summary['total_players']}")
        print(f"  Players with Concerns: {summary['concerning_players']}")
        
        # Export results
        self.export_results(df, output_file)
        
        # Print top concerns
        self.print_top_concerns(df)
        
        # Store results
        self.results = df
        
        return df

def main():
    """
    Main execution function for command-line usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='WNBA Performance Dip Detection System'
    )
    parser.add_argument(
        '--input', '-i', 
        default='data/wnba_2024_gamelogs.csv',
        help='Input CSV file path'
    )
    parser.add_argument(
        '--output', '-o',
        default='detected_performance_dips.csv', 
        help='Output CSV file path'
    )
    parser.add_argument(
        '--min-games', '-m',
        type=int, default=10,
        help='Minimum games required for analysis'
    )
    parser.add_argument(
        '--cycle-length', '-c',
        type=int, default=28,
        help='Cycle length for periodic analysis'
    )
    parser.add_argument(
        '--drop-threshold', '-d',
        type=float, default=0.20,
        help='Performance drop threshold (0.20 = 20%)'
    )
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = CycleDipDetector(
        min_games=args.min_games,
        cycle_length=args.cycle_length,
        drop_threshold=args.drop_threshold
    )
    
    # Run analysis
    try:
        results = detector.run_analysis(args.input, args.output)
        print(f"\nAnalysis complete! Results saved to {args.output}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()