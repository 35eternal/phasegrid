import json
import csv
import os

INPUT_JSON = "data/wnba_prizepicks_props.json"
OUTPUT_CSV = "data/prizepicks_player_map.csv"

def extract_player_map():
    if not os.path.exists(INPUT_JSON):
        print(f"❌ File not found: {INPUT_JSON}")
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            return

    if not isinstance(data, list):
        print("❌ Expected top-level JSON list.")
        return

    print(f"🔍 Extracting player_id → name from {len(data)} entries...")

    seen = set()
    player_map = []

    for entry in data:
        try:
            player_id = int(entry["relationships"]["new_player"]["data"]["id"])
            player_name = entry["attributes"]["name"]
        except (KeyError, TypeError, ValueError):
            continue

        if player_id not in seen:
            player_map.append({"player_id": player_id, "player_name": player_name})
            seen.add(player_id)

    # Save to CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["player_id", "player_name"])
        writer.writeheader()
        writer.writerows(player_map)

    print(f"✅ Extracted {len(player_map)} unique players.")
    print(f"📁 Saved mapping to: {OUTPUT_CSV}")

if __name__ == "__main__":
    extract_player_map()
