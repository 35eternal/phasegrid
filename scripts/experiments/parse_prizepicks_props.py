# scripts/parse_prizepicks_props.py

import json
import pandas as pd
import os

input_file = "data/prizepicks_props.json"
output_file = "data/props_live.csv"

with open(input_file, "r", encoding="utf-8") as f:
    raw = json.load(f)

props = raw.get("data", [])
parsed = []

for item in props:
    attr = item.get("attributes", {})
    parsed.append({
        "projection_id": item.get("id"),
        "player_id": attr.get("player_id"),
        "game_id": attr.get("game_id"),
        "team": attr.get("team"),
        "stat_type": attr.get("stat_type"),
        "line_score": attr.get("line_score"),
        "start_time": attr.get("start_time"),
        "updated_at": attr.get("updated_at"),
        "status": attr.get("status"),
        "odds_type": attr.get("odds_type"),
        "is_live": attr.get("is_live"),
        "is_promo": attr.get("is_promo")
    })

df = pd.DataFrame(parsed)
df.to_csv(output_file, index=False)
print(f"✅ Parsed and saved {len(df)} props to {output_file}")
