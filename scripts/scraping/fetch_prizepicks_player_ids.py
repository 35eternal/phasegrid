import requests
import csv

API_URL = "https://api.prizepicks.com/projections?league_id=3&per_page=250&single_stat=true&in_game=true&state_code=NM&game_mode=pickem"
OUTPUT_CSV = "data/prizepicks_player_ids.csv"

HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "origin": "https://app.prizepicks.com",
    "referer": "https://app.prizepicks.com/",
    "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "x-device-id": "048c632e-0ed3-4f5e-9cf0-8c938dab0148",
    "x-device-info": "anonymousId=e8c3fcaf-21f9-4815-bedf-1e60e66dc20d,name=,os=windows,osVersion=Windows NT 10.0; Win64; x64,platform=web,appVersion=,gameMode=pickem,stateCode=NM,fbp=fb.1.1748995254414.948797635306132314",
    "cookie": "_vwo_uuid_v2=D17C6965C85DA4524D93A2D00014B5CBE|5a441471879b17e94f5f7151c492c9e7; (your full cookie here)"
}

def fetch_player_ids():
    print("🌐 Requesting WNBA props...")
    res = requests.get(API_URL, headers=HEADERS)

    if res.status_code != 200:
        print(f"❌ Failed to fetch data: {res.status_code}")
        return

    j = res.json()
    data = j.get("data", [])
    if not data:
        print("❌ No data found in response.")
        return

    player_ids = set()
    for entry in data:
        try:
            player_id = int(entry["relationships"]["new_player"]["data"]["id"])
            player_ids.add(player_id)
        except:
            continue

    print(f"✅ Found {len(player_ids)} unique player IDs.")
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["player_id"])
        for pid in sorted(player_ids):
            writer.writerow([pid])

    print(f"📁 Saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    fetch_player_ids()
