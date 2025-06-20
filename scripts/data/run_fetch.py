import pandas as pd
from scripts.gamelog_scraper import fetch_gamelog
from scripts.prop_mapper import load_props_and_map_players

# Paths
PROPS_PATH = "data/wnba_prizepicks_props.json"
MAPPING_PATH = "data/player_final_mapping.csv"
OUTPUT_PATH = "data/merged_props_with_gamelogs.csv"

# Step 1: Load and map props
print("🔗 Loading and mapping PrizePicks props...")
df_props = load_props_and_map_players(PROPS_PATH, MAPPING_PATH)

# Drop entries without mapped BBRef IDs
df_props = df_props.dropna(subset=["BBRefID"])

# Step 2: Fetch gamelogs for each player
all_gamelogs = []

print("📊 Fetching gamelogs...")
for _, row in df_props.iterrows():
    name = row["Player Name"]
    bbref_id = row["BBRefID"]
    print(f"📁 Fetching gamelog for {name} ({bbref_id})...")
    try:
        gamelog = fetch_gamelog(bbref_id)
        gamelog["BBRefID"] = bbref_id
        gamelog["Player Name"] = name
        gamelog["Stat Type"] = row["Stat Type"]
        gamelog["Line"] = row["Line"]
        all_gamelogs.append(gamelog)
    except Exception as e:
        print(f"❌ Failed to fetch gamelog for {name}: {e}")

# Step 3: Combine and save
if all_gamelogs:
    final_df = pd.concat(all_gamelogs, ignore_index=True)
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Combined data saved to {OUTPUT_PATH}")
else:
    print("⚠️ No gamelogs fetched.")
