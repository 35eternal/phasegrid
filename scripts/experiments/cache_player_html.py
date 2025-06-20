import requests
import os
import random
import time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
]

def cache_html(player_id, year):
    url = f"https://www.basketball-reference.com/wnba/players/{player_id[0]}/{player_id}/gamelog/{year}/"
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    print(f"🔍 Fetching HTML for {player_id}...")

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return

    os.makedirs("data/html_cache", exist_ok=True)
    path = f"data/html_cache/{player_id}_{year}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"✅ Saved to {path}")

# Run this
if __name__ == "__main__":
    cache_html("clarkca02w", 2024)
