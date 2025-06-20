import pandas as pd

# Load the data
pp_names = pd.read_csv("data/prizepicks_id_name_map.csv")
br_names = pd.read_csv("data/player_directory.csv")  # has Name, URL, ID

# Clean names for matching
pp_names["name_clean"] = pp_names["name"].str.lower().str.strip()
br_names["name_clean"] = br_names["Name"].str.lower().str.strip()

# Merge on name
name_map = pp_names.merge(br_names, on="name_clean", how="left")

# Save final mapping
name_map.to_csv("data/player_final_mapping.csv", index=False)

print("✅ Final player mapping saved to data/player_final_mapping.csv")
print(name_map[["name", "Name", "URL"]].head())
