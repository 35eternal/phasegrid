import pandas as pd
import os

input_path = "data/unified_gamelogs.csv"
output_path = "data/unified_gamelogs_boosted.csv"

df = pd.read_csv(input_path)

# Multiply each player’s dataset 3× with shifted game dates
boosted_frames = []

for i in range(3):
    temp_df = df.copy()
    temp_df["GameDate"] = pd.to_datetime(temp_df["GameDate"]) + pd.to_timedelta(i * 180, unit="D")
    temp_df["PlayerFileName"] = temp_df["PlayerFileName"] + f"_season{i+1}"
    boosted_frames.append(temp_df)

boosted = pd.concat(boosted_frames, ignore_index=True)
boosted = boosted.sort_values(by=["PlayerFileName", "GameDate"])
boosted.to_csv(output_path, index=False)

print(f"✅ Boosted dataset saved: {output_path}")
