import os
import json
import pandas as pd

DATA_DIR = "data/network_logs"
OUT_PATH = "data/props_prizepicks.csv"

def extract_props_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            return []

    props = []
    # Search for player projections
    try:
        included = data.get("included", [])
        for item in included:
            if item.get("type") != "projection":
                continue

            attr = item.get("attributes", {})
            player_name = attr.get("name")
            stat_type = attr.get("stat_type")
            line_score = attr.get("line_score")
            team = attr.get("team", "")
            game_date = attr.get("game_date", "")

            if player_name and stat_type:
                props.append({
                    "Player": player_name,
                    "Stat Type": stat_type,
                    "Line": line_score,
                    "Team": team,
                    "Game Date": game_date
                })
    except Exception:
        pass

    return props

def main():
    all_props = []

    print("🔍 Scanning debug JSON files for props...")
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            path = os.path.join(DATA_DIR, filename)
            props = extract_props_from_file(path)
            all_props.extend(props)

    if not all_props:
        print("❌ No props found in any debug files.")
    else:
        df = pd.DataFrame(all_props)
        df.to_csv(OUT_PATH, index=False)
        print(f"✅ Saved props: {OUT_PATH}")
        print(df.head())

if __name__ == "__main__":
    main()
