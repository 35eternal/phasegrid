import json
import pandas as pd

# Load player mappings
mapping_path = "data/player_final_mapping.csv"
mapping_df = pd.read_csv(mapping_path)
mapped_names = set(mapping_df["name"].str.strip())

# Load PrizePicks props JSON
with open("data/wnba_prizepicks_props.json", "r") as f:
    data = json.load(f)

players_seen = set()
print("\n📋 Active PrizePicks Players:\n")

for item in data["included"]:
    if item["type"] == "new_player":
        name = item["attributes"]["name"].strip()
        if name not in players_seen:
            players_seen.add(name)
            mapped = "✅" if name in mapped_names else "❌"
            print(f"{mapped} {name}")

unmapped = [name for name in players_seen if name not in mapped_names]
print(f"\n🟡 Total Players on PrizePicks: {len(players_seen)}")
print(f"🔴 Missing Mappings: {len(unmapped)}")
