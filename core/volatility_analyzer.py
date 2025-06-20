import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class VolatilityAnalyzer:
    """
    Analyzes player performance volatility to identify high-risk betting targets.
    Uses rolling windows to calculate consistency scores across key stats.
    """
    
    def __init__(self, lookback_games=10):
        self.lookback_games = lookback_games
        self.volatility_thresholds = {
            'extreme': 0.40,  # CV > 40% 
            'high': 0.30,     # CV > 30%
            'moderate': 0.20, # CV > 20%
            'low': 0.10       # CV > 10%
        }
        
    def calculate_coefficient_of_variation(self, series):
        """Calculate CV (std dev / mean) for a series, handling edge cases."""
        if len(series) < 3 or series.mean() <= 0:
            return np.nan
        return series.std() / series.mean()
    
    def analyze_player_volatility(self, gamelogs_df):
        """
        Calculate volatility metrics for all players across key betting stats.
        Returns DataFrame with volatility scores and risk classifications.
        """
        # Key stats for prop betting - using actual column names from the data
        stat_columns = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M', 'FGM', 'FTM']
        existing_stats = [col for col in stat_columns if col in gamelogs_df.columns]
        
        if not existing_stats:
            print("⚠️  Warning: No standard stat columns found. Available columns:")
            print(gamelogs_df.columns.tolist())
            return pd.DataFrame()
        
        print(f"📊 Analyzing stats: {existing_stats}")
        
        results = []
        
        # Group by player
        for player_name, player_data in gamelogs_df.groupby('Player'):
            # Sort by date if available
            if 'Date' in player_data.columns:
                player_data = player_data.sort_values('Date', ascending=False)
            
            # Skip if insufficient games
            if len(player_data) < self.lookback_games:
                continue
                
            # Get recent games
            recent_games = player_data.head(self.lookback_games)
            
            player_volatility = {
                'Player': player_name,
                'Games_Analyzed': len(recent_games),
            }
            
            if 'Date' in recent_games.columns:
                player_volatility['Date_Range'] = f"{recent_games['Date'].min()} to {recent_games['Date'].max()}"
            else:
                player_volatility['Date_Range'] = f"Last {self.lookback_games} games"
            
            # Calculate CV for each stat
            volatility_scores = []
            for stat in existing_stats:
                cv = self.calculate_coefficient_of_variation(recent_games[stat])
                player_volatility[f'{stat}_CV'] = cv
                player_volatility[f'{stat}_Mean'] = recent_games[stat].mean()
                player_volatility[f'{stat}_Std'] = recent_games[stat].std()
                
                if not np.isnan(cv):
                    volatility_scores.append(cv)
            
            # Overall volatility score (average CV across all stats)
            if volatility_scores:
                player_volatility['Overall_Volatility'] = np.mean(volatility_scores)
                player_volatility['Max_Stat_Volatility'] = np.max(volatility_scores)
                
                # Classify risk level
                overall_vol = player_volatility['Overall_Volatility']
                if overall_vol > self.volatility_thresholds['extreme']:
                    risk_level = 'EXTREME'
                elif overall_vol > self.volatility_thresholds['high']:
                    risk_level = 'HIGH'
                elif overall_vol > self.volatility_thresholds['moderate']:
                    risk_level = 'MODERATE'
                else:
                    risk_level = 'LOW'
                    
                player_volatility['Risk_Level'] = risk_level
            else:
                player_volatility['Overall_Volatility'] = np.nan
                player_volatility['Risk_Level'] = 'UNKNOWN'
                
            results.append(player_volatility)
        
        return pd.DataFrame(results)
    
    def identify_volatility_patterns(self, volatility_df):
        """
        Identify specific volatility patterns that are important for betting.
        """
        patterns = []
        
        for _, player in volatility_df.iterrows():
            player_patterns = {
                'Player': player['Player'],
                'Risk_Level': player['Risk_Level'],
                'Key_Insights': []
            }
            
            # Check for extreme single-stat volatility
            stat_columns = [col for col in player.index if col.endswith('_CV') and col != 'Overall_Volatility']
            for stat_col in stat_columns:
                if pd.notna(player[stat_col]) and player[stat_col] > self.volatility_thresholds['extreme']:
                    stat_name = stat_col.replace('_CV', '')
                    player_patterns['Key_Insights'].append(
                        f"EXTREME volatility in {stat_name} (CV: {player[stat_col]:.3f})"
                    )
            
            # Flag players with high overall volatility but specific stable stats
            if player['Overall_Volatility'] > self.volatility_thresholds['high']:
                stable_stats = []
                for stat_col in stat_columns:
                    if pd.notna(player[stat_col]) and player[stat_col] < self.volatility_thresholds['moderate']:
                        stat_name = stat_col.replace('_CV', '')
                        stable_stats.append(stat_name)
                
                if stable_stats:
                    player_patterns['Key_Insights'].append(
                        f"High overall volatility but stable in: {', '.join(stable_stats)}"
                    )
            
            if player_patterns['Key_Insights']:
                player_patterns['Insights_Summary'] = ' | '.join(player_patterns['Key_Insights'])
                patterns.append(player_patterns)
        
        return pd.DataFrame(patterns)

def main():
    """Run volatility analysis on gamelogs."""
    print("🎲 WNBA Player Volatility Analyzer")
    print("=" * 50)
    
    # Use the correct file with actual game statistics
    gamelogs_path = 'data/wnba_combined_gamelogs.csv'
    
    try:
        gamelogs_df = pd.read_csv(gamelogs_path)
        print(f"✅ Loaded gamelogs from {gamelogs_path}: {len(gamelogs_df)} records")
    except FileNotFoundError:
        print(f"❌ Could not find {gamelogs_path}")
        print("\nTrying alternative files...")
        
        # Fallback options
        alternative_paths = [
            'data/wnba_2024_gamelogs.csv',
            'data/archive/2024/engineered_gamelogs_2024.csv',
            'data/wnba_full_gamelogs.csv'
        ]
        
        gamelogs_df = None
        for path in alternative_paths:
            try:
                gamelogs_df = pd.read_csv(path)
                print(f"✅ Loaded gamelogs from {path}: {len(gamelogs_df)} records")
                break
            except FileNotFoundError:
                continue
        
        if gamelogs_df is None:
            print("❌ Could not find any gamelog files.")
            return
    
    # Rename columns to standard names
    column_mapping = {
        'PLAYER_NAME': 'Player',
        'GAME_DATE': 'Date',
        'PLAYER_ID': 'PlayerID'
    }
    
    gamelogs_df = gamelogs_df.rename(columns=column_mapping)
    
    # Verify we have the required columns
    print(f"\n📋 Columns found: {list(gamelogs_df.columns)[:15]}")  # Show first 15
    
    # Initialize analyzer
    analyzer = VolatilityAnalyzer(lookback_games=10)
    
    # Run analysis
    print("\n📊 Analyzing player volatility...")
    volatility_results = analyzer.analyze_player_volatility(gamelogs_df)
    
    if volatility_results.empty:
        print("❌ No volatility results generated. Check your data format.")
        return
    
    # Sort by overall volatility
    volatility_results = volatility_results.sort_values('Overall_Volatility', ascending=False)
    
    # Save full results
    volatility_results.to_csv('output/player_volatility_analysis.csv', index=False)
    print(f"\n✅ Saved full analysis to output/player_volatility_analysis.csv")
    
    # Identify patterns
    patterns_df = analyzer.identify_volatility_patterns(volatility_results)
    if not patterns_df.empty:
        patterns_df.to_csv('output/volatility_patterns.csv', index=False)
        print(f"✅ Saved {len(patterns_df)} volatility patterns to output/volatility_patterns.csv")
    
    # Display summary
    print("\n🎯 VOLATILITY SUMMARY")
    print("=" * 50)
    
    risk_counts = volatility_results['Risk_Level'].value_counts()
    for risk_level in ['EXTREME', 'HIGH', 'MODERATE', 'LOW']:
        if risk_level in risk_counts.index:
            print(f"{risk_level} Risk: {risk_counts[risk_level]} players")
    
    # Show top 10 most volatile players
    print("\n⚠️  TOP 10 MOST VOLATILE PLAYERS:")
    print("-" * 50)
    
    for idx, player in volatility_results.head(10).iterrows():
        print(f"{player['Player']}: {player['Overall_Volatility']:.3f} CV ({player['Risk_Level']})")
        
        # Show which stats are most volatile
        stat_cvs = {col.replace('_CV', ''): player[col] 
                   for col in player.index if col.endswith('_CV') and col != 'Overall_Volatility'}
        stat_cvs = {k: v for k, v in stat_cvs.items() if pd.notna(v)}
        if stat_cvs:
            most_volatile_stat = max(stat_cvs.items(), key=lambda x: x[1])
            print(f"  → Most volatile: {most_volatile_stat[0]} (CV: {most_volatile_stat[1]:.3f})")
    
    print("\n✅ Volatility analysis complete!")
    
if __name__ == "__main__":
    main()