import pandas as pd
import os
import glob

input_dir = "data/player_gamelogs"
output_path = "data/unified_gamelogs.csv"

# Collect all player log CSVs
csv_files = glob.glob(os.path.join(input_dir, "*.csv"))

frames = []

for file in csv_files:
    try:
        df = pd.read_csv(file)

        # Add filename-based player name fallback
        player_from_file = os.path.basename(file).replace("_2023.csv", "").replace("_", " ")
        df["PlayerFileName"] = player_from_file

        # Normalize key columns (adjust if necessary)
        df = df.rename(columns={
            "GAME_ID": "GameID",
            "GAME_DATE": "GameDate",
            "MATCHUP": "Matchup",
            "PTS": "Points",
            "AST": "Assists",
            "REB": "Rebounds",
            "MIN": "Minutes",
            "FG3M": "ThreesMade",
            "STL": "Steals",
            "BLK": "Blocks",
            "TOV": "Turnovers",
        })

        # Include only necessary columns for now
        core_cols = ["PlayerFileName", "GameID", "GameDate", "Matchup", "Points", "Assists", "Rebounds",
                     "ThreesMade", "Steals", "Blocks", "Turnovers", "Minutes"]
        df = df[[col for col in core_cols if col in df.columns]]

        frames.append(df)

    except Exception as e:
        print(f"❌ Failed to process {file}: {e}")

# Combine all
unified_df = pd.concat(frames, ignore_index=True)

# Clean
unified_df["GameDate"] = pd.to_datetime(unified_df["GameDate"])

# Sort by player + date
unified_df = unified_df.sort_values(by=["PlayerFileName", "GameDate"])

# Save
unified_df.to_csv(output_path, index=False)
print(f"✅ Unified dataset saved to: {output_path}")
