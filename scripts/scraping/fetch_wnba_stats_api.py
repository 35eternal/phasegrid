import requests
import pandas as pd
import os
import time

# Player name → WNBA stats site ID mapping
players = {
    "Alyssa Thomas": "1629711",
    "A'ja Wilson": "1628932",
    "Nneka Ogwumike": "203100",
    "Arike Ogunbowale": "1628837",
    "Jewell Loyd": "1626167",
    "Sabrina Ionescu": "1630132",
    "DeWanna Bonner": "201312",
    "Brittney Griner": "203139",
    "Napheesa Collier": "1628935",
    "Breanna Stewart": "1627766"
}

output_dir = "data/player_gamelogs"
os.makedirs(output_dir, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.wnba.com/",
    "Origin": "https://www.wnba.com"
}

def fetch_gamelogs(player_name, player_id, season="2023"):
    url = f"https://stats.wnba.com/stats/playergamelogs?PlayerID={player_id}&Season={season}&SeasonType=Regular%20Season"
    print(f"🌐 Fetching logs for {player_name} ({season})...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        headers_row = data["resultSets"][0]["headers"]
        rows = data["resultSets"][0]["rowSet"]

        df = pd.DataFrame(rows, columns=headers_row)
        df["PlayerName"] = player_name

        output_path = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_{season}.csv")
        df.to_csv(output_path, index=False)
        print(f"✅ Saved to {output_path}")
    except Exception as e:
        print(f"❌ Failed to fetch {player_name}: {e}")

# Run for all players
for name, pid in players.items():
    fetch_gamelogs(name, pid, season="2023")
    time.sleep(1.5)  # Respectful rate limiting
