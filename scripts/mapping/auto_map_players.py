import pandas as pd
from fuzzywuzzy import process

# Load BBRef player directory (your player_directory.csv)
bbref_df = pd.read_csv("data/player_directory.csv")

# Clean the BBRef names
bbref_df["name_clean"] = bbref_df["Name"].astype(str).str.lower().str.replace(r"[^a-z ]", "", regex=True).str.strip()

# Load PrizePicks player data
pp_df = pd.read_csv("data/prizepicks_player_map.csv")

# Clean PrizePicks names
pp_df["player_name_clean"] = pp_df["player_name"].astype(str).str.lower().str.replace(r"[^a-z ]", "", regex=True).str.strip()

# Match each PrizePicks player to the closest BBRef name
mapped_data = []
for _, row in pp_df.iterrows():
    name = row["player_name_clean"]
    best_match, score = process.extractOne(name, bbref_df["name_clean"])
    matched_row = bbref_df[bbref_df["name_clean"] == best_match].iloc[0]
    mapped_data.append({
        "player_name": row["player_name"],
        "player_id": row["player_id"],
        "matched_name": matched_row["Name"],
        "BBRefID": matched_row["ID"],
        "match_score": score
    })

# Save the result
mapped_df = pd.DataFrame(mapped_data)
mapped_df.to_csv("data/player_final_mapping.csv", index=False)

print("✅ Auto-mapping complete! Saved to data/player_final_mapping.csv")
