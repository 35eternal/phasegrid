import os
import requests
import pandas as pd
import time

# Output folder
output_dir = "data/player_gamelogs_2025"
os.makedirs(output_dir, exist_ok=True)

# Active player name → WNBA Stats site player ID (as of 2025 season)
players = {
    "Caitlin Clark": "1641835",
    "A'ja Wilson": "1628932",
    "Breanna Stewart": "1627766",
    "Alyssa Thomas": "1629711",
    "Arike Ogunbowale": "1628837",
    "Sabrina Ionescu": "1630132",
    "Jewell Loyd": "1626167",
    "Napheesa Collier": "1628935",
    "Brittney Griner": "203139",
    "Aliyah Boston": "1641782"
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.wnba.com/",
    "Origin": "https://www.wnba.com"
}

def fetch_logs(player_name, player_id, season="2025"):
    url = f"https://stats.wnba.com/stats/playergamelogs?PlayerID={player_id}&Season={season}&SeasonType=Regular%20Season"
    print(f"🌐 Fetching {player_name} ({season})...")
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        headers_row = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]
        df = pd.DataFrame(rows, columns=headers_row)

        if len(df) < 3:
            print(f"⚠️  Skipping {player_name} — only {len(df)} games")
            return

        df["PlayerName"] = player_name
        filename = f"{player_name.replace(' ', '_')}_2025.csv"
        df.to_csv(os.path.join(output_dir, filename), index=False)
        print(f"✅ Saved {player_name} ({len(df)} games)")

    except Exception as e:
        print(f"❌ Failed to fetch {player_name}: {e}")

# Run all players
for name, pid in players.items():
    fetch_logs(name, pid)
    time.sleep(1.5)  # respectful rate limiting
