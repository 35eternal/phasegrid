import pandas as pd
import os

# File paths (relative to project root)
PROP_CSV = "data/wnba_prizepicks_props.csv"
PLAYER_DIR_CSV = "data/player_directory.csv"
OUTPUT_MATCHED = "data/wnba_props_with_names.csv"
OUTPUT_MISSING = "data/missing_player_ids.csv"

def map_player_names():
    if not os.path.exists(PROP_CSV):
        print(f"❌ Missing prop CSV: {PROP_CSV}")
        return
    if not os.path.exists(PLAYER_DIR_CSV):
        print(f"❌ Missing player directory: {PLAYER_DIR_CSV}")
        return

    print("📂 Loading data...")
    df_props = pd.read_csv(PROP_CSV)
    df_dir = pd.read_csv(PLAYER_DIR_CSV)

    # Ensure consistent naming
    if "player_id" not in df_props.columns:
        print("❌ 'player_id' column missing in props CSV.")
        return
    if "ID" not in df_dir.columns or "Name" not in df_dir.columns:
        print("❌ 'ID' or 'Name' column missing in player directory.")
        return

    # Ensure both columns are integers
    df_props["player_id"] = pd.to_numeric(df_props["player_id"], errors="coerce").astype("Int64")
    df_dir["ID"] = pd.to_numeric(df_dir["ID"], errors="coerce").astype("Int64")

    print("🔍 Attempting to map player_id → Name...")

    # Merge on player_id
    df_merged = pd.merge(df_props, df_dir, how="left", left_on="player_id", right_on="ID")

    matched = df_merged[~df_merged["Name"].isna()]
    missing = df_merged[df_merged["Name"].isna()]

    print(f"✅ {len(matched)} players matched.")
    print(f"⚠️ {len(missing)} players unmatched. Logging to {OUTPUT_MISSING}")

    # Output files
    matched.to_csv(OUTPUT_MATCHED, index=False)
    missing.to_csv(OUTPUT_MISSING, index=False)

    print(f"📁 Saved matched props to: {OUTPUT_MATCHED}")
    print(f"📁 Saved unmatched player_ids to: {OUTPUT_MISSING}")

if __name__ == "__main__":
    map_player_names()
