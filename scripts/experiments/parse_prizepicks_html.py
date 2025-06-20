import json
import re
import pandas as pd
from pathlib import Path

def extract_json_from_scripts(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    script_blocks = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
    json_candidates = []

    for script in script_blocks:
        # Clean leading JS assignments like: window.__PRELOADED_STATE__ = ...
        cleaned = re.sub(r"^\s*[\w.]+\s*=\s*", "", script.strip())
        cleaned = cleaned.rstrip(";")  # remove trailing semicolon

        try:
            data = json.loads(cleaned)
            json_candidates.append(data)
        except Exception:
            continue

    if not json_candidates:
        print("❌ Still no valid JSON found in script tags.")
        return None

    # Choose largest valid JSON blob
    best_json = max(json_candidates, key=lambda x: len(json.dumps(x)))
    return best_json

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
    html_path = Path("data/raw_html_prizepicks.html")
    output_path = Path("data/props_prizepicks.csv")

    json_blob = extract_json_from_scripts(html_path)
    if not json_blob:
        return

    df = parse_props(json_blob)
    if df.empty:
        print("⚠️ JSON parsed, but no WNBA props found.")
    else:
        df.to_csv(output_path, index=False)
        print(f"✅ Parsed {len(df)} props.")
        print(f"📁 Saved to: {output_path}")

if __name__ == "__main__":
    main()
