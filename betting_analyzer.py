import pandas as pd
from datetime import datetime, timedelta

# Load results
results = pd.read_csv('enhanced_cycle_results.csv')
strong_patterns = results[results['classification'].str.contains('Strong')]

print("IMMEDIATE BETTING OPPORTUNITIES")
print("="*50)
print("\nPlayers with Strong Cyclical Patterns:")
print(f"Found {len(strong_patterns)} strong patterns\n")

today = datetime.now()

for _, row in strong_patterns.iterrows():
    player = row['player_name']
    metric = row['metric']
    interval = row['mean_interval']
    
    # Parse recent dips
    if pd.notna(row['recent_dips']) and row['recent_dips']:
        dips = row['recent_dips'].split(', ')
        if dips:
            last_dip = pd.to_datetime(dips[-1])
            next_dip = last_dip + timedelta(days=interval)
            days_until = (next_dip - today).days
            
            print(f"{player} - {metric}")
            print(f"  Cycle: Every {interval:.1f} days")
            print(f"  Last dip: {last_dip.strftime('%Y-%m-%d')}")
            print(f"  Next expected: {next_dip.strftime('%Y-%m-%d')} ({days_until} days)")
            
            if -3 <= days_until <= 3:
                print("  ⚠️ DIP WINDOW ACTIVE - Consider UNDER bets")
            elif days_until < 0:
                print("  ✓ Past dip window - Performance likely recovering")
            print()

# Export actionable bets
betting_opportunities = []
for _, row in strong_patterns.iterrows():
    if pd.notna(row['recent_dips']) and row['recent_dips']:
        dips = row['recent_dips'].split(', ')
        if dips:
            last_dip = pd.to_datetime(dips[-1])
            next_dip = last_dip + timedelta(days=row['mean_interval'])
            days_until = (next_dip - today).days
            
            betting_opportunities.append({
                'player': row['player_name'],
                'metric': row['metric'],
                'pattern_strength': row['pattern_score'],
                'avg_drop_pct': row['avg_drop_pct'],
                'next_dip_date': next_dip.strftime('%Y-%m-%d'),
                'days_until_dip': days_until,
                'bet_recommendation': 'UNDER' if -3 <= days_until <= 3 else 'WAIT'
            })

betting_df = pd.DataFrame(betting_opportunities)
betting_df = betting_df.sort_values('days_until_dip')
betting_df.to_csv('betting_opportunities.csv', index=False)
print(f"\nExported {len(betting_df)} betting opportunities to betting_opportunities.csv")
