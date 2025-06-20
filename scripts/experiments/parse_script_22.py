import json
import re
import pandas as pd
from pathlib import Path

def extract_json_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Remove JS assignment like "window.__INITIAL_STATE__ = "
    cleaned = re.sub(r"^\s*[\w.]+\s*=\s*", "", content)
    cleaned = cleaned.rstrip(";")  # Remove trailing semicolon

    try:
        return json.loads(cleaned)
    except Exception as e:
        print(f"❌ Failed to parse JSON: {e}")
        return None

def parse_props(json_blob):
    try:
        projections = json_blob["projections"]["byId"]
        players = json_blob["players"]["byId"]
    except KeyError:
        print("❌ Required keys not found in JSON blob.")
        return pd.DataFrame()

    rows = []
    for proj in projections.values():
        if proj.get("league") != "wnba":
            continue

        stat_type = proj.get("stat_type")
        line_score = proj.get("line_score")
        player_id = proj.get("player_id")
        player = players.get(str(player_id), {})
        name = player.get("full_name", "Unknown")
        team = player.get("team", "Unknown")

        rows.append({
            "Name": name,
            "Team": team,
            "Stat": stat_type,
            "Line": line_score
        })

    return pd.DataFrame(rows)

def main():
    input_file = Path("data/network_logs/script_22.txt")
    output_file = Path("data/props_prizepicks.csv")

    json_blob = extract_json_from_file(input_file)
    if not json_blob:
        return

    df = parse_props(json_blob)
    if df.empty:
        print("⚠️ JSON parsed, but no WNBA props found.")
    else:
        df.to_csv(output_file, index=False)
        print(f"✅ Parsed {len(df)} props.")
        print(f"📁 Saved to: {output_file}")

if __name__ == "__main__":
    main()
