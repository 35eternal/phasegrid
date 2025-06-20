import requests
import json
import os

def dump_prizepicks_raw():
    print("🔎 Fetching raw PrizePicks API data...")

    url = "https://api.prizepicks.com/projections?per_page=500"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch: {response.status_code}")
        return

    try:
        data = response.json()
    except Exception as e:
        print(f"❌ JSON decode failed: {e}")
        return

    os.makedirs("debug", exist_ok=True)
    with open("debug/raw_prizepicks_response.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("✅ Raw PrizePicks data saved to: debug/raw_prizepicks_response.json")

if __name__ == "__main__":
    dump_prizepicks_raw()
