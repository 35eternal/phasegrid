import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv('data/wnba_combined_gamelogs.csv')
df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], format='mixed')

# Basic stats
print("Dataset Overview:")
print(f"Total records: {len(df)}")
print(f"Total players: {df['PLAYER_NAME'].nunique()}")
print(f"Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")

# Games per player
games_per_player = df.groupby('PLAYER_NAME').size().sort_values(ascending=False)
print(f"\nGames per player stats:")
print(f"Max: {games_per_player.max()}")
print(f"Min: {games_per_player.min()}")
print(f"Mean: {games_per_player.mean():.1f}")
print(f"Players with 30+ games: {(games_per_player >= 30).sum()}")
print(f"Players with 20+ games: {(games_per_player >= 20).sum()}")

# Top scorers
top_scorers = df.groupby('PLAYER_NAME')['PTS'].mean().sort_values(ascending=False).head(10)
print("\nTop 10 scorers (PPG):")
for player, ppg in top_scorers.items():
    games = games_per_player[player]
    print(f"  {player}: {ppg:.1f} PPG ({games} games)")

# Check for any existing results
try:
    results = pd.read_csv('cycle_analysis_results.csv')
    print(f"\nResults found: {len(results)} rows")
    if len(results) > 0:
        print("\nFirst few results:")
        print(results.head())
except:
    print("\nNo results file found")
