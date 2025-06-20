import os
import pandas as pd
from bs4 import BeautifulSoup

def build_all_gamelogs(directory_path="data/html_cache", year=2024):
    os.makedirs("data/player_gamelogs", exist_ok=True)
    os.makedirs("data/failed_players", exist_ok=True)
    failed_players = []

    for filename in os.listdir(directory_path):
        if not filename.endswith(f"_{year}.html"):
            continue

        player_id = filename.replace(f"_{year}.html", "")
        player_name = "Caitlin Clark" if player_id == "clarkca02w" else player_id

        try:
            with open(os.path.join(directory_path, filename), "r", encoding="utf-8") as f:
                html = f.read()

            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", id="pgl_basic")
            if table is None:
                raise Exception("Missing game log table.")

            df = pd.read_html(str(table))[0]
            df = df[df["Rk"] != "Rk"]
            df.to_csv(f"data/player_gamelogs/{player_name.replace(' ', '_')}_{year}.csv", index=False)
            print(f"✅ Saved: {player_name}")

        except Exception as e:
            print(f"❌ Failed: {player_name} — {e}")
            failed_players.append(player_name)

    # Save failed list
    if failed_players:
        pd.Series(failed_players).to_csv("data/failed_players/failed_players.csv", index=False)
        print(f"\n⚠️ {len(failed_players)} players failed. Logged to failed_players.csv.")
    else:
        print("\n✅ All player gamelogs built successfully.")

if __name__ == "__main__":
    build_all_gamelogs()
