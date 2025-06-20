import os
import sys
sys.path.append('.')

from modules.wnba_betting_modules import BettingSystemEnhancer

# Use the fixed file with raw_kelly column
enhancer = BettingSystemEnhancer()
enhanced_df = enhancer.enhance_betting_card(
    input_path='daily_betting_card_fixed.csv',  # Use the fixed file
    output_path='output/daily_betting_card_adjusted.csv',
    live_odds_path='live_odds.csv'
)

print("Enhancement complete with matched odds!")

# Check if odds were properly matched
import pandas as pd
df = pd.read_csv('output/daily_betting_card_adjusted.csv')
unique_odds = df['actual_odds'].unique()
print(f"\nUnique odds values: {unique_odds}")
print(f"Non-default odds: {len([x for x in unique_odds if x != 0.9])}")

# Show sample with actual odds
print("\nSample enhanced bets with real odds:")
sample = df[df['actual_odds'] != 0.9].head(5)
if len(sample) > 0:
    print(sample[['player_name', 'stat_type', 'actual_odds', 'kelly_used']])
else:
    print("No matches found - checking why...")
    print(f"Betting card players: {df['player_name'].unique()[:5]}")
    odds_df = pd.read_csv('live_odds.csv')
    print(f"Live odds players: {odds_df['player_name'].unique()[:5]}")
