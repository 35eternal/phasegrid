# build_player_directory.py
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.basketball-reference.com/wnba/players/"

def build_directory():
    print("🌐 Fetching WNBA player index page...")

    response = requests.get(BASE_URL)
    if response.status_code != 200:
        print(f"❌ Failed to fetch index page. Status Code: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    all_links = soup.select("div#content a")

    player_data = []

    for link in all_links:
        href = link.get("href", "")
        if href.startswith("/wnba/players/") and href.count("/") == 4:
            name = link.text.strip()
            url = "https://www.basketball-reference.com" + href
            player_id = href.split("/")[-1].replace(".html", "")
            player_data.append({"Name": name, "URL": url, "ID": player_id})

    if not player_data:
        print("❌ No player data found.")
    else:
        print(f"✅ Found {len(player_data)} WNBA players. Saving to CSV...")

    df = pd.DataFrame(player_data)
    df.to_csv("data/player_directory.csv", index=False)
    print("📁 Saved player directory to data/player_directory.csv")

if __name__ == "__main__":
    build_directory()
