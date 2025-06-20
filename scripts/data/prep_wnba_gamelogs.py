import pandas as pd

INPUT_FILE = "data/wnba_2024_gamelogs.csv"
OUTPUT_FILE = "data/cleaned_gamelogs_2024.csv"

df = pd.read_csv(INPUT_FILE)

# Convert date to datetime
df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

# Filter to valid games only
df = df[df["MIN"].notna() & (df["MIN"] != 0)]

# Select core columns for modeling
keep_cols = [
    "PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "GAME_DATE", "MATCHUP", "WL",
    "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV", "PF", "PLUS_MINUS",
    "WNBA_FANTASY_PTS"
]
df = df[keep_cols]

# Sort chronologically
df = df.sort_values(["PLAYER_NAME", "GAME_DATE"])

# Save cleaned version
df.to_csv(OUTPUT_FILE, index=False)
print(f"✅ Cleaned game logs saved to {OUTPUT_FILE} ({len(df)} rows)")
