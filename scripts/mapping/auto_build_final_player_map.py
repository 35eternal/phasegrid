import pandas as pd
from rapidfuzz import process, fuzz

# Load files
pp_df = pd.read_csv("data/prizepicks_id_name_map.csv")  # PrizePicks data
br_df = pd.read_csv("data/player_directory.csv")        # BBRef master

# Clean names
pp_df["name_clean"] = pp_df["name"].str.lower().str.strip()
br_df["name_clean"] = br_df["Name"].str.lower().str.strip()

# Build mapping using fuzzy matching
matched = []
for name in pp_df["name_clean"]:
    match, score, _ = process.extractOne(name, br_df["name_clean"], scorer=fuzz.token_sort_ratio)
    if score >= 90:
        bbref_row = br_df[br_df["name_clean"] == match].iloc[0]
        matched.append({
            "name_clean": name,
            "Name": bbref_row["Name"],
            "URL": bbref_row["URL"],
            "score": score
        })
    else:
        matched.append({
            "name_clean": name,
            "Name": None,
            "URL": None,
            "score": score
        })

# Merge with original
matched_df = pd.DataFrame(matched)
final = pp_df.merge(matched_df, on="name_clean", how="left")

# Save final file
final[["player_id", "name", "Name", "URL"]].to_csv("data/player_final_mapping.csv", index=False)
print("✅ Auto-mapping complete. Saved to data/player_final_mapping.csv")
