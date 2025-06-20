import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from time import sleep
from tqdm import tqdm

# --- Config ---
INPUT_CSV = "data/player_directory.csv"
OUTPUT_DIR = "data/player_gamelogs_2024"
SEASON = "2024"
DELAY_BETWEEN_REQUESTS = 3  # seconds

# --- Ensure output directory exists ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load and prepare player directory ---
players = pd.read_csv(INPUT_CSV)
players = players.rename(columns={"Name": "name", "ID": "BBRefID"})
players = players.dropna(subset=["BBRefID"])

# --- Function to scrape individual player logs ---
def fetch_player_log(name, bbref_id):
    first_letter = bbref_id[0]
    url = f"https://www.basketball-reference.com/wnba/players/{first_letter}/{bbref_id}/gamelog/{SEASON}/"
    print(f"🌐 Fetching {name} ({bbref_id})...")

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code != 200:
            return f"❌ {name}: HTTP {res.status_code}"

        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", id="pgl_basic")

        if not table:
            return f"⚠️  {name}: No game log table"

        df = pd.read_html(str(table))[0]
        df = df[df["Rk"] != "Rk"]  # Remove repeated headers

        df["Player"] = name
        df["BBRefID"] = bbref_id

        output_path = os.path.join(OUTPUT_DIR, f"{name.replace(' ', '_')}_{SEASON}.csv")
        df.to_csv(output_path, index=False)
        return f"✅ Saved {name}'s game log ({len(df)} games)"

    except Exception as e:
        return f"❌ {name}: {str(e)}"

# --- Main loop ---
print(f"\n📊 Fetching {SEASON} game logs for all players...\n")
for _, row in tqdm(players.iterrows(), total=len(players)):
    name = row["name"]
    bbref_id = row["BBRefID"]
    result = fetch_player_log(name, bbref_id)
    print(result)
    sleep(DELAY_BETWEEN_REQUESTS)

print("\n🎯 Done fetching player logs.\n")
