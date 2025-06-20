import requests
import time
import json

BASE_URL = "https://api.prizepicks.com/projections"
OUTPUT_FILE = "../data/wnba_prizepicks_props.json"

HEADERS = {
    "Accept": "application/json",
    "Origin": "https://app.prizepicks.com",
    "Referer": "https://app.prizepicks.com/",
    "User-Agent": "Mozilla/5.0"
}

COOKIES = {
    "_prizepicks_session": "YOUR_SESSION_COOKIE_HERE",  # Replace this
    # You can copy others too if needed
}

PARAMS = {
    "league_id": 3,
    "page": 1,
    "per_page": 250,
    "single_stat": "true",
    "in_game": "true",
    "state_code": "NM",
    "game_mode": "pickem"
}


def scrape_wnba_props():
    print("📊 Scraping PrizePicks WNBA props...\n")
    page = 1
    all_props = []

    while True:
        PARAMS["page"] = page
        response = requests.get(BASE_URL, headers=HEADERS, cookies=COOKIES, params=PARAMS)

        if response.status_code == 429:
            print(f"❌ Page {page}: Rate limited. Stopping scrape.")
            break

        if response.status_code != 200:
            print(f"❌ Page {page}: Failed to fetch - {response.status_code}")
            break

        data = response.json()
        projections = data.get("data", [])
        if not projections:
            print(f"⚠️ Page {page}: No projections found.")
            break

        print(f"✅ Page {page}: Found {len(projections)} projections")
        all_props.extend(projections)

        page += 1
        time.sleep(1.2)  # Prevent 429s

    print(f"\n✅ Total props scraped: {len(all_props)}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_props, f, indent=2)

    print(f"💾 Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    scrape_wnba_props()
