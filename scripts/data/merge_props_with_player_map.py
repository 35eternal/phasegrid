import pandas as pd

print("🔄 Merging props with player map...")

# Load the data
props = pd.read_csv("data/props_live.csv")
player_map = pd.read_csv("data/player_final_mapping.csv")

# Merge on player_id
merged = props.merge(player_map, on="player_id", how="left")

# Save result
merged.to_csv("data/merged_props.csv", index=False)

print(f"✅ Merged and saved {len(merged)} props to data/merged_props.csv")
