# fetch_all_gamelogs.py

import pandas as pd
import os
import time
from scripts.gamelog_scraper import fetch_gamelog_for_player

PLAYER_CSV = "data/player_directory.csv"
FAILED_CSV = "data/failed_players.csv"
PROGRESS_FILE = "data/last_scraped.txt"

# Read directory
df = pd.read_csv(PLAYER_CSV)

# Load last progress (if exists)
start_index = 0
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        last_id = f.read().strip()
        if last_id in df["ID"].values:
            start_index = df.index[df["ID"] == last_id].tolist()[0] + 1

print(f"📦 Starting batch game log scrape for {len(df)} players from index {start_index}...")

for i in range(start_index, len(df)):
    row = df.iloc[i]
    player_id = row["ID"]
    player_name = row["Name"]
    player_url = row["URL"]

    print(f"\n➡️ [{i+1}/{len(df)}] Scraping: {player_name} ({player_id})")
    try:
        success = fetch_gamelog_for_player(player_name, player_url, player_id)
        if not success:
            raise Exception("No table found or empty stats.")

        # Save progress
        with open(PROGRESS_FILE, "w") as f:
            f.write(player_id)

    except Exception as e:
        print(f"❌ Failed: {player_name} - {e}")
        # Log failure
        with open(FAILED_CSV, "a") as f:
            f.write(f"{player_name},{player_url},{player_id},{str(e)}\n")

    time.sleep(2)  # Throttle to avoid rate limits

print("\n✅ Batch scraping complete.")
