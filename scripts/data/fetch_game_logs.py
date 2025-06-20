import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

INPUT_MAPPING = "data/player_final_mapping.csv"
OUTPUT_DIR = "data"

def fetch_game_log(player_id, bbref_id):
    url = f"https://www.basketball-reference.com/wnba/players/{bbref_id[0]}/{bbref_id}/gamelog/2024/"
    print(f"📥 Fetching: {player_id} → {bbref_id} ...")

    res = requests.get(url)
    if res.status_code != 200:
        print(f"❌ Failed to fetch {bbref_id} — Status {res.status_code}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table", id="pgl_basic")
    if table is None:
        print(f"❌ No game log table found for {bbref_id}")
        return

    df = pd.read_html(str(table))[0]
    df = df[df["Rk"] != "Rk"]  # Remove repeating headers
    df.dropna(subset=["Rk"], inplace=True)
    df.to_csv(f"{OUTPUT_DIR}/{player_id}_2024_gamelog.csv", index=False)
    print(f"✅ Saved: {player_id}_2024_gamelog.csv")

def main():
    mapping_df = pd.read_csv(INPUT_MAPPING)

    for _, row in mapping_df.iterrows():
        fetch_game_log(row["player_id"], row["BBRefID"])

if __name__ == "__main__":
    main()
