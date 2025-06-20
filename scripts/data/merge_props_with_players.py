import pandas as pd

props = pd.read_csv("data/props_live.csv")
names = pd.read_csv("data/prizepicks_id_name_map.csv")

# Ensure both keys are same type
props["player_id"] = props["player_id"].astype(str)
names["player_id"] = names["player_id"].astype(str)

merged = props.merge(names, on="player_id", how="left")
merged.to_csv("data/merged_props.csv", index=False)

print("✅ Merged with names. Sample:\n", merged.head())
