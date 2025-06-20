# scripts/scrape_wnba_props_fixed.py

import requests
import csv
import os

OUTPUT_PATH = os.path.join("data", "prizepicks_wnba_props_fixed.csv")
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}
BASE_URL = "https://api.prizepicks.com/projections"
LEAGUE_ID = 18  # WNBA

def fetch_all_pages():
    props = []
    page = 1

    while True:
        url = f"{BASE_URL}?league_id={LEAGUE_ID}&per_page=250&page={page}"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"❌ Error fetching page {page}: {response.status_code}")
            break

        data = response.json()
        page_props = data.get("data", [])
        
        if not page_props:
            break

        props.extend(page_props)
        page += 1

    return props

def extract_props(raw_props):
    extracted = []

    for prop in raw_props:
        attr = prop.get("attributes", {})
        player_name = attr.get("name")
        stat_type = attr.get("stat_type")
        line_score = attr.get("line_score")
        game_str = attr.get("description")

        if player_name and stat_type:
            extracted.append({
                "Player": player_name,
                "Stat": stat_type,
                "Line": line_score,
                "Game": game_str
            })

    return extracted

def save_to_csv(props):
    if not props:
        print("❌ No props to save.")
        return

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Player", "Stat", "Line", "Game"])
        writer.writeheader()
        writer.writerows(props)

    print(f"✅ Saved {len(props)} WNBA props to {OUTPUT_PATH}")

def main():
    print("📊 Scraping PrizePicks WNBA props (fixed method)...")
    raw_props = fetch_all_pages()

    print(f"✅ Found {len(raw_props)} raw projections")
    extracted = extract_props(raw_props)

    if not extracted:
        print("❌ No WNBA props matched criteria.")
    else:
        print(f"✅ Extracted {len(extracted)} props")
        save_to_csv(extracted)

if __name__ == "__main__":
    main()
