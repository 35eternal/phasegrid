import requests
import pandas as pd
from tqdm import tqdm
import os
import time

# Output file
OUTPUT_FILE = "data/wnba_2024_gamelogs.csv"
SEASON_YEAR = 2024

# Endpoint URL
BASE_URL = "https://stats.wnba.com/stats/playergamelogs"

# Custom headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.wnba.com/stats/",
    "Origin": "https://www.wnba.com"
}

# Fetch game logs for all players
def fetch_game_logs():
    print(f"📊 Fetching {SEASON_YEAR} WNBA game logs...")

    params = {
        "LeagueID": "10",             # WNBA
        "Season": f"{SEASON_YEAR}",   # 2024 season
        "SeasonType": "Regular Season"
    }

    response = requests.get(BASE_URL, headers=HEADERS, params=params)

    if response.status_code != 200:
        print(f"❌ Failed to fetch data. Status code: {response.status_code}")
        return

    data = response.json()
    headers = data['resultSets'][0]['headers']
    rows = data['resultSets'][0]['rowSet']

    df = pd.DataFrame(rows, columns=headers)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Saved {len(df)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    fetch_game_logs()
