# fetch_wnba_players.py

from basketball_reference_scraper.players import get_player_stats
import pandas as pd

# Define the list of WNBA players you want to fetch data for
wnba_players = [
    'Caitlin Clark',
    'A\'ja Wilson',
    'Breanna Stewart',
    'Sabrina Ionescu',
    'Kahleah Copper'
    # Add more player names as needed
]

# Initialize an empty list to store player data
player_data = []

# Fetch stats for each player
for player in wnba_players:
    try:
        print(f"Fetching data for {player}...")
        stats = get_player_stats(player, stat_type='PER_GAME', playoffs=False, career=False)
        stats['Player'] = player
        player_data.append(stats)
    except Exception as e:
        print(f"Error fetching data for {player}: {e}")

# Combine all player data into a single DataFrame
if player_data:
    all_players_df = pd.concat(player_data, ignore_index=True)
    # Save the data to a CSV file
    all_players_df.to_csv('data/wnba_player_stats.csv', index=False)
    print("✅ Player data saved to data/wnba_player_stats.csv")
else:
    print("No player data fetched.")
