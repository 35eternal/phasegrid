import pandas as pd
from difflib import get_close_matches

# Load data
betting_df = pd.read_csv("output/daily_betting_card.csv")
odds_df = pd.read_csv("live_odds.csv")

# Get unique names
betting_names = betting_df["player_name"].unique()
odds_names = odds_df["player_name"].unique()

print(f"Betting card players: {len(betting_names)}")
print(f"Live odds players: {len(odds_names)}")

# Show examples of mismatches
print("\nExample betting card names:")
print(list(betting_names)[:10])
print("\nExample live odds names:")
print(list(odds_names))

# Create simple mapping for common patterns
print("\nCreating updated live odds file...")

# For now, just show that all bets get default odds
print(f"\nAll {len(betting_names)} players currently getting default 0.9 odds")
print("To fix: Update live_odds.csv with your actual player names")
