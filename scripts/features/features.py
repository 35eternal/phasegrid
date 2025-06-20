import pandas as pd
import os

input_path = "data/unified_gamelogs_boosted.csv"
output_path = "data/unified_gamelogs_with_features.csv"

df = pd.read_csv(input_path)
df["GameDate"] = pd.to_datetime(df["GameDate"])
df = df.sort_values(by=["PlayerFileName", "GameDate"])

# Build 1-game averages (shifted last game stats)
for col in ["Points", "Assists", "Rebounds", "ThreesMade", "Steals", "Blocks", "Turnovers", "Minutes"]:
    df[f"{col}_avg_1g"] = df.groupby("PlayerFileName")[col].shift(1)
    df[f"{col}_delta"] = df.groupby("PlayerFileName")[col].diff()

# Days since last game + back-to-back
df["DaysSinceLastGame"] = df.groupby("PlayerFileName")["GameDate"].diff().dt.days
df["IsBackToBack"] = df["DaysSinceLastGame"] == 1

# Cycle-aware signal (placeholder)
df["CyclePhase"] = df.groupby("PlayerFileName").cumcount() % 28

# Only drop rows missing key recent stats
required_features = ["Points_avg_1g", "Assists_avg_1g", "Rebounds_avg_1g", "Minutes"]
df = df.dropna(subset=required_features)

# Check and save
if df.empty or len(df) < 10:
    print(f"❌ Not enough usable feature rows even after boosting. Found {len(df)}.")
else:
    df.to_csv(output_path, index=False)
    print(f"✅ Feature-enhanced dataset saved: {output_path} ({len(df)} rows)")
