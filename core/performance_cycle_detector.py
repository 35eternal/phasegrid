import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PerformanceCycleDetector:
    """
    Detects hot/cold streaks and cyclical patterns in player performance.
    Identifies when players are likely to bounce back or continue trends.
    """
    
    def __init__(self, min_games=20):
        self.min_games = min_games
        self.streak_thresholds = {
            'hot': 1.25,      # 25% above average
            'cold': 0.75,     # 25% below average
            'neutral': (0.75, 1.25)
        }
        
    def calculate_rolling_performance(self, player_data, stat_col, window=5):
        """Calculate rolling average and identify performance relative to season average."""
        if stat_col not in player_data.columns:
            return None
            
        # Sort by date
        player_data = player_data.sort_values('Date')
        
        # Calculate season average
        season_avg = player_data[stat_col].mean()
        
        # Calculate rolling average
        player_data[f'{stat_col}_rolling'] = player_data[stat_col].rolling(window=window, min_periods=3).mean()
        
        # Calculate performance ratio (rolling avg / season avg)
        player_data[f'{stat_col}_ratio'] = player_data[f'{stat_col}_rolling'] / season_avg
        
        return player_data, season_avg
    
    def detect_streaks(self, player_data, stat_col):
        """Identify hot/cold streaks for a specific stat."""
        streaks = []
        current_streak = {'type': None, 'length': 0, 'start_date': None}
        
        for idx, row in player_data.iterrows():
            ratio = row.get(f'{stat_col}_ratio')
            if pd.isna(ratio):
                continue
                
            # Determine streak type
            if ratio >= self.streak_thresholds['hot']:
                streak_type = 'hot'
            elif ratio <= self.streak_thresholds['cold']:
                streak_type = 'cold'
            else:
                streak_type = 'neutral'
            
            # Check if streak continues or starts new
            if streak_type == current_streak['type']:
                current_streak['length'] += 1
            else:
                # Save previous streak if significant
                if current_streak['length'] >= 3 and current_streak['type'] != 'neutral':
                    streaks.append(current_streak.copy())
                
                # Start new streak
                current_streak = {
                    'type': streak_type,
                    'length': 1,
                    'start_date': row['Date'],
                    'end_date': row['Date']
                }
        
        # Don't forget the last streak
        if current_streak['length'] >= 3 and current_streak['type'] != 'neutral':
            streaks.append(current_streak)
            
        return streaks, current_streak
    
    def analyze_bounce_back_patterns(self, player_data, stat_col):
        """Analyze how often players bounce back after cold streaks."""
        if f'{stat_col}_ratio' not in player_data.columns:
            return None
            
        bounce_backs = 0
        cold_games = 0
        
        player_data = player_data.sort_values('Date')
        
        for i in range(1, len(player_data)):
            prev_ratio = player_data.iloc[i-1][f'{stat_col}_ratio']
            curr_ratio = player_data.iloc[i][f'{stat_col}_ratio']
            
            if pd.notna(prev_ratio) and pd.notna(curr_ratio):
                # If previous game was cold
                if prev_ratio <= self.streak_thresholds['cold']:
                    cold_games += 1
                    # Check if current game is a bounce back
                    if curr_ratio >= 1.0:  # Back to or above average
                        bounce_backs += 1
        
        bounce_back_rate = bounce_backs / cold_games if cold_games > 0 else 0
        return {
            'cold_games': cold_games,
            'bounce_backs': bounce_backs,
            'bounce_back_rate': bounce_back_rate
        }
    
    def detect_cycles(self, gamelogs_df):
        """Main method to detect performance cycles for all players."""
        results = []
        
        # Key stats to analyze
        stat_columns = ['PTS', 'REB', 'AST']
        
        for player_name, player_data in gamelogs_df.groupby('Player'):
            if len(player_data) < self.min_games:
                continue
                
            player_cycles = {
                'Player': player_name,
                'Total_Games': len(player_data),
                'Date_Range': f"{player_data['Date'].min()} to {player_data['Date'].max()}"
            }
            
            # Analyze each stat
            for stat in stat_columns:
                if stat not in player_data.columns:
                    continue
                    
                # Calculate rolling performance
                analyzed_data, season_avg = self.calculate_rolling_performance(player_data.copy(), stat)
                if analyzed_data is None:
                    continue
                
                # Detect streaks
                streaks, current_streak = self.detect_streaks(analyzed_data, stat)
                
                # Analyze bounce back patterns
                bounce_back_info = self.analyze_bounce_back_patterns(analyzed_data, stat)
                
                # Store results
                player_cycles[f'{stat}_Season_Avg'] = season_avg
                player_cycles[f'{stat}_Current_Streak'] = current_streak['type']
                player_cycles[f'{stat}_Streak_Length'] = current_streak['length']
                player_cycles[f'{stat}_Hot_Streaks'] = len([s for s in streaks if s['type'] == 'hot'])
                player_cycles[f'{stat}_Cold_Streaks'] = len([s for s in streaks if s['type'] == 'cold'])
                
                if bounce_back_info:
                    player_cycles[f'{stat}_Bounce_Rate'] = bounce_back_info['bounce_back_rate']
                
                # Get recent form (last 5 games)
                recent_games = analyzed_data.tail(5)
                player_cycles[f'{stat}_Recent_Avg'] = recent_games[stat].mean()
                player_cycles[f'{stat}_Recent_Trend'] = 'up' if recent_games[stat].iloc[-1] > recent_games[stat].iloc[0] else 'down'
            
            results.append(player_cycles)
        
        return pd.DataFrame(results)
    
    def identify_betting_opportunities(self, cycles_df):
        """Identify specific betting opportunities based on cycles."""
        opportunities = []
        
        for _, player in cycles_df.iterrows():
            player_opps = {
                'Player': player['Player'],
                'Opportunities': []
            }
            
            # Check each stat
            for stat in ['PTS', 'REB', 'AST']:
                if f'{stat}_Current_Streak' not in player:
                    continue
                    
                current_streak = player[f'{stat}_Current_Streak']
                streak_length = player.get(f'{stat}_Streak_Length', 0)
                bounce_rate = player.get(f'{stat}_Bounce_Rate', 0)
                
                # Cold streak with high bounce back rate
                if current_streak == 'cold' and bounce_rate > 0.6:
                    player_opps['Opportunities'].append(
                        f"{stat} BUY LOW: Cold streak ({streak_length} games), {bounce_rate:.1%} bounce rate"
                    )
                
                # Extended hot streak (due for regression)
                elif current_streak == 'hot' and streak_length >= 5:
                    player_opps['Opportunities'].append(
                        f"{stat} FADE: Extended hot streak ({streak_length} games)"
                    )
                
                # Just ended cold streak
                elif current_streak == 'neutral' and player.get(f'{stat}_Cold_Streaks', 0) > 2:
                    recent_avg = player.get(f'{stat}_Recent_Avg', 0)
                    season_avg = player.get(f'{stat}_Season_Avg', 0)
                    if recent_avg > season_avg * 0.9:
                        player_opps['Opportunities'].append(
                            f"{stat} WARMING UP: Exiting cold streak, recent {recent_avg:.1f} vs season {season_avg:.1f}"
                        )
            
            if player_opps['Opportunities']:
                player_opps['Opportunity_Count'] = len(player_opps['Opportunities'])
                player_opps['Summary'] = ' | '.join(player_opps['Opportunities'])
                opportunities.append(player_opps)
        
        return pd.DataFrame(opportunities)

def main():
    """Run performance cycle detection."""
    print("🔄 WNBA Performance Cycle Detector")
    print("=" * 50)
    
    # Load gamelogs
    try:
        gamelogs_df = pd.read_csv('data/wnba_combined_gamelogs.csv')
        print(f"✅ Loaded gamelogs: {len(gamelogs_df)} records")
    except FileNotFoundError:
        print("❌ Could not find data/wnba_combined_gamelogs.csv")
        return
    
    # Rename columns for consistency
    column_mapping = {
        'PLAYER_NAME': 'Player',
        'GAME_DATE': 'Date'
    }
    gamelogs_df = gamelogs_df.rename(columns=column_mapping)
    
    # Check date format
    print(f"📅 Sample dates: {gamelogs_df['Date'].iloc[0:3].tolist()}")
    
    # Convert date to datetime - handle various formats
    try:
        gamelogs_df['Date'] = pd.to_datetime(gamelogs_df['Date'], format='%Y-%m-%d')
    except:
        try:
            gamelogs_df['Date'] = pd.to_datetime(gamelogs_df['Date'], format='mixed')
        except:
            gamelogs_df['Date'] = pd.to_datetime(gamelogs_df['Date'], errors='coerce')
    
    # Remove rows with invalid dates
    valid_dates = gamelogs_df['Date'].notna()
    if not valid_dates.all():
        print(f"⚠️  Removing {(~valid_dates).sum()} rows with invalid dates")
        gamelogs_df = gamelogs_df[valid_dates]
    
    # Initialize detector
    detector = PerformanceCycleDetector(min_games=20)
    
    # Run cycle detection
    print("\n🔍 Detecting performance cycles...")
    cycles_results = detector.detect_cycles(gamelogs_df)
    
    # Save results
    cycles_results.to_csv('output/player_performance_cycles.csv', index=False)
    print(f"✅ Saved cycle analysis to output/player_performance_cycles.csv")
    
    # Identify opportunities
    opportunities = detector.identify_betting_opportunities(cycles_results)
    if not opportunities.empty:
        opportunities = opportunities.sort_values('Opportunity_Count', ascending=False)
        opportunities.to_csv('output/cycle_betting_opportunities.csv', index=False)
        print(f"✅ Saved {len(opportunities)} betting opportunities to output/cycle_betting_opportunities.csv")
    
    # Display summary
    print("\n📊 CYCLE DETECTION SUMMARY")
    print("=" * 50)
    print(f"Total players analyzed: {len(cycles_results)}")
    
    # Count current streaks
    for stat in ['PTS', 'REB', 'AST']:
        col = f'{stat}_Current_Streak'
        if col in cycles_results.columns:
            streak_counts = cycles_results[col].value_counts()
            print(f"\n{stat} Current Streaks:")
            for streak_type in ['hot', 'cold', 'neutral']:
                if streak_type in streak_counts.index:
                    print(f"  {streak_type.upper()}: {streak_counts[streak_type]} players")
    
    # Show top opportunities
    if not opportunities.empty:
        print("\n🎯 TOP BETTING OPPORTUNITIES:")
        print("-" * 50)
        
        for idx, opp in opportunities.head(10).iterrows():
            print(f"\n{opp['Player']} ({opp['Opportunity_Count']} opportunities):")
            for opportunity in opp['Opportunities']:
                print(f"  → {opportunity}")
    
    print("\n✅ Cycle detection complete!")

if __name__ == "__main__":
    main()