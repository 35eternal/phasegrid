import json
import pandas as pd

# Load JSON
with open("data/prizepicks_props.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract and flatten projections
records = []
for entry in data["data"]:
    attr = entry.get("attributes", {})
    rel = entry.get("relationships", {})
    
    records.append({
        "projection_id": entry.get("id"),
        "player_id": rel.get("new_player", {}).get("data", {}).get("id"),
        "game_id": attr.get("game_id"),
        "team": attr.get("description"),
        "stat_type": attr.get("stat_display_name"),
        "line_score": attr.get("line_score"),
        "start_time": attr.get("start_time"),
        "updated_at": attr.get("updated_at"),
        "status": attr.get("status"),
        "odds_type": attr.get("odds_type"),
        "is_live": attr.get("is_live"),
        "is_promo": attr.get("is_promo"),
    })

# Convert to DataFrame
df = pd.DataFrame(records)

# Save to CSV
df.to_csv("data/props_live.csv", index=False)
print("✅ Saved parsed props to data/props_live.csv")
