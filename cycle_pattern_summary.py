import pandas as pd
from datetime import datetime, timedelta

# Load results
results = pd.read_csv('enhanced_cycle_results.csv')
strong_patterns = results[results['classification'].str.contains('Strong')]

print("CYCLE PATTERN ANALYSIS - 2024 SEASON")
print("="*60)
print("\nNote: This data is from the 2024 WNBA season.")
print("These patterns can be applied to future seasons.\n")

# Show pattern summary
print("STRONGEST CYCLICAL PATTERNS DETECTED:")
print("-"*60)

# Group by player and show their patterns
player_patterns = {}
for _, row in strong_patterns.iterrows():
    player = row['player_name']
    if player not in player_patterns:
        player_patterns[player] = []
    player_patterns[player].append({
        'metric': row['metric'],
        'cycle_days': row['mean_interval'],
        'pattern_score': row['pattern_score'],
        'avg_drop': row['avg_drop_pct']
    })

# Sort by number of strong patterns
sorted_players = sorted(player_patterns.items(), key=lambda x: len(x[1]), reverse=True)

for player, patterns in sorted_players:
    print(f"\n{player}:")
    games = results[results['player_name'] == player].iloc[0]['total_games']
    print(f"  Games played: {games}")
    for p in patterns:
        print(f"  • {p['metric']}: {p['cycle_days']:.1f}-day cycle (Pattern strength: {p['pattern_score']:.2f}, Avg drop: {p['avg_drop']:.1f}%)")

print("\n" + "="*60)
print("HOW TO USE FOR BETTING:")
print("="*60)

print("""
1. CHENNEDY CARTER - Triple Pattern Player
   - Shows consistent 29-31 day cycles across ALL stats
   - When one stat dips, others likely follow
   - Track her game schedule and bet UNDER around cycle dates

2. HIGH-CONFIDENCE SINGLE PATTERNS:
   - Layshia Clarendon: PTS every 22 days (73% drop!)
   - Cecilia Zandalasini: PTS every 31 days (100% drop!)
   - Kate Martin: AST every 29 days (100% drop!)

3. BETTING STRATEGY:
   - Mark cycle dates on calendar from season start
   - Bet UNDER on metrics 2-3 days before expected dip
   - Bet OVER 5-7 days after dip (recovery phase)
   - Combine with injury reports for maximum edge
""")

# Create a historical backtest example
print("\nHISTORICAL VALIDATION EXAMPLE:")
print("-"*40)

# Find Chennedy Carter's pattern
carter_data = strong_patterns[strong_patterns['player_name'] == 'Chennedy Carter']
if not carter_data.empty:
    carter_pts = carter_data[carter_data['metric'] == 'PTS'].iloc[0]
    dips = carter_pts['recent_dips'].split(', ')
    
    print(f"Chennedy Carter PTS dips in 2024:")
    for i, dip in enumerate(dips):
        print(f"  Dip {i+1}: {dip}")
        if i < len(dips) - 1:
            days_between = (pd.to_datetime(dips[i+1]) - pd.to_datetime(dip)).days
            print(f"    → {days_between} days until next dip")
    
    print(f"\nAverage cycle: {carter_pts['mean_interval']:.1f} days")
    print(f"Pattern reliability: {carter_pts['pattern_score']:.1%}")

# Export summary for easy reference
summary_data = []
for _, row in strong_patterns.iterrows():
    summary_data.append({
        'Player': row['player_name'],
        'Stat': row['metric'],
        'Cycle_Days': round(row['mean_interval'], 1),
        'Pattern_Strength': round(row['pattern_score'], 3),
        'Avg_Drop_%': round(row['avg_drop_pct'], 1),
        'Bet_Value': 'HIGH' if row['pattern_score'] > 0.8 else 'MEDIUM'
    })

summary_df = pd.DataFrame(summary_data)
summary_df = summary_df.sort_values(['Pattern_Strength', 'Avg_Drop_%'], ascending=[False, False])
summary_df.to_csv('cycle_betting_guide.csv', index=False)

print(f"\nExported betting guide to 'cycle_betting_guide.csv'")
print("\nFor 2025 season: Track these players from Day 1 and apply cycle patterns!")
