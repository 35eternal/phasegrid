import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class PropValueAnalyzer:
    """
    Analyzes prop betting value by combining volatility, cycles, and actual lines.
    Identifies mathematical edges based on historical performance patterns.
    """
    
    def __init__(self):
        self.value_thresholds = {
            'strong_over': 0.15,   # 15%+ expected value
            'over': 0.08,          # 8%+ expected value
            'under': -0.08,        # 8%+ expected value on under
            'strong_under': -0.15  # 15%+ expected value on under
        }
        
    def load_analysis_data(self):
        """Load previously generated analysis files."""
        try:
            # Load volatility analysis
            volatility_df = pd.read_csv('output/player_volatility_analysis.csv')
            print(f"✅ Loaded volatility data for {len(volatility_df)} players")
        except:
            print("⚠️  Could not load volatility analysis")
            volatility_df = pd.DataFrame()
            
        try:
            # Load cycle analysis
            cycles_df = pd.read_csv('output/player_performance_cycles.csv')
            print(f"✅ Loaded cycle data for {len(cycles_df)} players")
        except:
            print("⚠️  Could not load cycle analysis")
            cycles_df = pd.DataFrame()
            
        return volatility_df, cycles_df
    
    def calculate_adjusted_projection(self, player_stats, stat_type, volatility_info, cycle_info):
        """Calculate projection adjusted for volatility and current cycle."""
        # Handle FG3M specially since it might be stored as FG3M in stats
        if stat_type == 'FG3M':
            base_projection = player_stats.get(f'{stat_type}_Season_Avg', 0)
            if base_projection == 0:
                # Try alternate naming
                base_projection = player_stats.get('3PM_Season_Avg', 0)
        else:
            base_projection = player_stats.get(f'{stat_type}_Season_Avg', 0)
        
        if base_projection == 0:
            return None
            
        # Get stat-specific volatility
        stat_volatility = volatility_info.get(f'{stat_type}_CV', volatility_info.get('Overall_Volatility', 0.5))
        
        # Volatility adjustment - LESS HARSH
        volatility_factor = 1.0
        
        # Adjusted penalties - more reasonable for real players
        if stat_volatility > 0.8:  # Very high volatility
            volatility_factor = 0.92  # Was 0.85
        elif stat_volatility > 0.5:  # High volatility  
            volatility_factor = 0.96  # Was 0.92
        elif stat_volatility > 0.3:  # Moderate volatility
            volatility_factor = 0.98
            
        # Cycle adjustment
        current_streak = cycle_info.get(f'{stat_type}_Current_Streak', 'neutral')
        streak_length = cycle_info.get(f'{stat_type}_Streak_Length', 0)
        recent_avg = cycle_info.get(f'{stat_type}_Recent_Avg', base_projection)
        
        cycle_factor = 1.0
        if current_streak == 'hot':
            # Weight recent performance more heavily
            cycle_factor = 0.7 + (0.3 * (recent_avg / base_projection))
            # But cap upside for extended streaks
            if streak_length >= 5:
                cycle_factor = min(cycle_factor, 1.1)
        elif current_streak == 'cold':
            # Consider bounce-back potential
            bounce_rate = cycle_info.get(f'{stat_type}_Bounce_Rate', 0.5)
            if bounce_rate > 0.6:
                cycle_factor = 0.85  # Expect some recovery
            else:
                cycle_factor = 0.75  # Stay conservative
                
        # Combined projection
        adjusted_projection = base_projection * volatility_factor * cycle_factor
        
        # Get stat-specific volatility for confidence calculation
        stat_volatility = volatility_info.get(f'{stat_type}_CV', volatility_info.get('Overall_Volatility', 0.5))
        
        return {
            'base': base_projection,
            'adjusted': adjusted_projection,
            'volatility_factor': volatility_factor,
            'cycle_factor': cycle_factor,
            'confidence': self._calculate_confidence(stat_volatility, current_streak, streak_length)
        }
    
    def _calculate_confidence(self, volatility, streak_type, streak_length):
        """Calculate confidence level (0-1) in projection."""
        # Start with base confidence
        confidence = 0.75  # Was 0.7
        
        # Reduce for high volatility (LESS HARSH)
        if volatility > 0.8:
            confidence -= 0.15  # Was 0.3 for >0.4
        elif volatility > 0.5:
            confidence -= 0.08  # Was 0.15 for >0.3
        elif volatility > 0.3:
            confidence -= 0.03  # Was 0.05 for >0.2
            
        # Adjust for streaks
        if streak_type == 'neutral':
            confidence += 0.1
        elif streak_length >= 5:
            confidence -= 0.1  # Extended streaks less predictable
            
        return max(0.3, min(1.0, confidence))
    
    def calculate_prop_value(self, line, projection_data):
        """Calculate expected value of a prop bet."""
        if not projection_data:
            return None
            
        adjusted = projection_data['adjusted']
        confidence = projection_data['confidence']
        
        # Calculate hit probability using a normal distribution approach
        # Assume standard deviation is ~25% of the mean for basketball stats
        std_dev = adjusted * 0.25
        
        # Calculate z-score
        z_score = (line - adjusted) / std_dev if std_dev > 0 else 0
        
        # Convert to probability (simplified normal CDF)
        # This gives us the probability of going OVER the line
        if z_score > 3:
            hit_probability = 0.05  # Very unlikely to go over
        elif z_score < -3:
            hit_probability = 0.95  # Very likely to go over
        else:
            # Approximate normal CDF
            hit_probability = 1 / (1 + np.exp(1.7 * z_score))
        
        # Adjust for confidence
        hit_probability = (hit_probability * confidence) + (0.5 * (1 - confidence))
        hit_probability = max(0.1, min(0.9, hit_probability))
        
        # Calculate expected value (assuming -110 odds)
        ev_over = (hit_probability * 0.909) - ((1 - hit_probability) * 1)
        ev_under = ((1 - hit_probability) * 0.909) - (hit_probability * 1)
        
        return {
            'hit_probability': hit_probability,
            'ev_over': ev_over,
            'ev_under': ev_under,
            'recommendation': self._get_recommendation(ev_over, ev_under),
            'confidence': confidence
        }
    
    def _get_recommendation(self, ev_over, ev_under):
        """Get betting recommendation based on EV."""
        if ev_over >= self.value_thresholds['strong_over']:
            return 'STRONG OVER'
        elif ev_over >= self.value_thresholds['over']:
            return 'OVER'
        elif ev_under >= abs(self.value_thresholds['under']):
            return 'UNDER'
        elif ev_under >= abs(self.value_thresholds['strong_under']):
            return 'STRONG UNDER'
        else:
            return 'PASS'
    
    def analyze_props(self, props_df, gamelogs_df, volatility_df, cycles_df, stat_mapping):
        """Main analysis method."""
        results = []
        
        # Merge analysis data
        analysis_df = volatility_df.merge(cycles_df, on='Player', how='outer')
        
        # Get recent gamelogs for each player
        player_stats = {}
        for player, data in gamelogs_df.groupby('Player'):
            stats = {}
            for stat in ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG3M']:
                if stat in data.columns:
                    stats[f'{stat}_Season_Avg'] = data[stat].mean()
                    stats[f'{stat}_Last10_Avg'] = data.head(10)[stat].mean()
            player_stats[player] = stats
        
        # Analyze each prop
        for _, prop in props_df.iterrows():
            # Get player name - check multiple possible columns
            player_name = prop.get('player_name', prop.get('name', prop.get('Player', '')))
            
            # Get stat type and map it
            stat_type_display = prop.get('stat_type', prop.get('stat', ''))
            stat_type = stat_mapping.get(stat_type_display, stat_type_display)
            
            # Handle combo stats
            if stat_type == 'PRA':  # Points + Rebounds + Assists
                continue  # Skip for now, would need special handling
            elif stat_type == 'PR':  # Points + Rebounds
                continue  # Skip for now
            elif stat_type == 'PA':  # Points + Assists
                continue  # Skip for now
            
            line = prop.get('line_score', prop.get('line', 0))
            
            if not player_name or not stat_type or line == 0:
                continue
                
            # Get player analysis data
            player_analysis = analysis_df[analysis_df['Player'] == player_name]
            if player_analysis.empty:
                continue
                
            player_vol = player_analysis.iloc[0].to_dict()
            player_cycle = player_analysis.iloc[0].to_dict()
            player_stat = player_stats.get(player_name, {})
            
            # Calculate adjusted projection
            projection_data = self.calculate_adjusted_projection(
                player_stat, stat_type, player_vol, player_cycle
            )
            
            if not projection_data:
                # Skip if no projection could be made
                continue
                
            # Skip if projection is 0 (player doesn't take that stat)
            if projection_data['adjusted'] < 0.1:
                continue
                
            # Calculate prop value
            value_data = self.calculate_prop_value(line, projection_data)
            
            if not value_data:
                continue
                
            # Only include props with edge
            if value_data['recommendation'] != 'PASS':
                result = {
                    'Player': player_name,
                    'Stat': stat_type_display,  # Use original stat name for display
                    'Line': line,
                    'Projection': round(projection_data['adjusted'], 1),
                    'Base_Avg': round(projection_data['base'], 1),
                    'Hit_Probability': round(value_data['hit_probability'] * 100, 1),
                    'EV': round(max(value_data['ev_over'], value_data['ev_under']) * 100, 1),
                    'Recommendation': value_data['recommendation'],
                    'Confidence': round(value_data['confidence'] * 100),
                    'Volatility': round(player_vol.get(f'{stat_type}_CV', player_vol.get('Overall_Volatility', 0)), 3),
                    'Current_Streak': player_cycle.get(f'{stat_type}_Current_Streak', 'unknown'),
                    'Risk_Level': player_vol.get('Risk_Level', 'unknown')
                }
                results.append(result)
        
        return pd.DataFrame(results)

def main():
    """Run prop value analysis."""
    print("💰 WNBA Prop Value Analyzer")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = PropValueAnalyzer()
    
    # Load analysis data
    volatility_df, cycles_df = analyzer.load_analysis_data()
    
    if volatility_df.empty or cycles_df.empty:
        print("❌ Missing required analysis files. Run volatility and cycle detectors first.")
        return
    
    # Load gamelogs
    try:
        gamelogs_df = pd.read_csv('data/wnba_combined_gamelogs.csv')
        column_mapping = {'PLAYER_NAME': 'Player', 'GAME_DATE': 'Date'}
        gamelogs_df = gamelogs_df.rename(columns=column_mapping)
        print(f"✅ Loaded gamelogs: {len(gamelogs_df)} records")
    except:
        print("❌ Could not load gamelogs")
        return
    
    # Load props data - use WNBA specific file
    props_df = None
    try:
        props_df = pd.read_csv('data/wnba_prizepicks_props.csv')
        print(f"✅ Loaded WNBA props: {len(props_df)} records")
    except:
        print("❌ Could not load WNBA props from data/wnba_prizepicks_props.csv")
        return
    
    # Map stat types from props format to gamelogs format
    stat_mapping = {
        'Points': 'PTS',
        'Rebounds': 'REB', 
        'Assists': 'AST',
        'Steals': 'STL',
        'Blocks': 'BLK',
        '3-PT Made': 'FG3M',
        'Pts+Rebs+Asts': 'PRA',
        'Pts+Rebs': 'PR',
        'Pts+Asts': 'PA'
    }
    
    # Run analysis
    print("\n💎 Analyzing prop value...")
    
    # Debug: Show what we're working with
    print(f"\n📊 Data overview:")
    print(f"   Props columns: {list(props_df.columns)}")
    if 'stat_type' in props_df.columns:
        print(f"   Stat types: {props_df['stat_type'].unique()}")
    elif 'stat' in props_df.columns:
        print(f"   Stat types: {props_df['stat'].unique()}")
    
    if 'player_name' in props_df.columns:
        print(f"   Sample players in props: {props_df['player_name'].dropna().unique()[:5]}")
    
    value_results = analyzer.analyze_props(props_df, gamelogs_df, volatility_df, cycles_df, stat_mapping)
    
    if value_results.empty:
        print("❌ No valuable props found")
        return
    
    # Sort by EV
    value_results = value_results.sort_values('EV', ascending=False)
    
    # Save results
    value_results.to_csv('output/prop_value_analysis.csv', index=False)
    print(f"✅ Saved {len(value_results)} valuable props to output/prop_value_analysis.csv")
    
    # Display summary
    print("\n📊 VALUE SUMMARY")
    print("=" * 50)
    
    rec_counts = value_results['Recommendation'].value_counts()
    for rec in ['STRONG OVER', 'OVER', 'UNDER', 'STRONG UNDER']:
        if rec in rec_counts.index:
            print(f"{rec}: {rec_counts[rec]} props")
    
    # Show top 10 value plays
    print("\n🎯 TOP 10 VALUE PLAYS:")
    print("-" * 80)
    print(f"{'Player':<20} {'Stat':<5} {'Line':<6} {'Proj':<6} {'Hit%':<6} {'EV%':<6} {'Rec':<12} {'Risk'}")
    print("-" * 80)
    
    for _, prop in value_results.head(10).iterrows():
        print(f"{prop['Player']:<20} {prop['Stat']:<5} {prop['Line']:<6} "
              f"{prop['Projection']:<6} {prop['Hit_Probability']:<6} "
              f"{prop['EV']:<6} {prop['Recommendation']:<12} {prop['Risk_Level']}")
    
    # Risk distribution
    print("\n⚠️  RISK DISTRIBUTION OF VALUE PLAYS:")
    risk_counts = value_results['Risk_Level'].value_counts()
    for risk in ['LOW', 'MODERATE', 'HIGH', 'EXTREME']:
        if risk in risk_counts.index:
            print(f"  {risk}: {risk_counts[risk]} props")
    
    print("\n✅ Prop value analysis complete!")

if __name__ == "__main__":
    main()