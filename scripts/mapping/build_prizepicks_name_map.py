import json
import pandas as pd

# Load the raw PrizePicks data
with open("data/prizepicks_props.json", "r") as f:
    raw = json.load(f)

# Focus only on 'included' — that's where player data is
included = raw["included"]

# Extract player info from 'included'
players = []
for item in included:
    if item.get("type") == "new_player":
        attributes = item.get("attributes", {})
        players.append({
            "player_id": item.get("id"),
            "name": attributes.get("name"),
            "team": attributes.get("team"),
            "sport": attributes.get("sport"),
        })

# Save as CSV
df = pd.DataFrame(players)
df.to_csv("data/prizepicks_id_name_map.csv", index=False)

print("✅ Saved prizepicks_id_name_map.csv with", len(df), "players.")
print(df.head())
