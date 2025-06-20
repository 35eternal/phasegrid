# run_batch_fetch.py

import pandas as pd
from scripts.gamelog_scraper import fetch_gamelog_for_player

print("📁 Starting batch scrape...")

player_df = pd.read_csv("player_directory.csv")

for _, row in player_df.iterrows():
    name = row["Name"]
    url = row["URL"]
    print(f"\n➡️ Scraping {name}...")
    fetch_gamelog_for_player(url)

print("\n✅ Batch scrape complete.")
