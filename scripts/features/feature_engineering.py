import pandas as pd
import numpy as np

INPUT_FILE = "data/cleaned_gamelogs_2024.csv"
OUTPUT_FILE = "data/engineered_gamelogs_2024.csv"

ROLLING_WINDOWS = [3, 5, 10]
TARGET_STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "MIN"]

def add_rolling_features(df, windows=ROLLING_WINDOWS, stats=TARGET_STATS):
    df = df.copy()
    df.sort_values(["PLAYER_NAME", "GAME_DATE"], inplace=True)

    for stat in stats:
        for window in windows:
            colname = f"{stat}_{window}G_AVG"
            df[colname] = (
                df.groupby("PLAYER_NAME")[stat]
                .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
            )
            
            # Optional: Add rolling std/z-score for volatility modeling
            std_col = f"{stat}_{window}G_STD"
            z_col = f"{stat}_{window}G_Z"
            df[std_col] = (
                df.groupby("PLAYER_NAME")[stat]
                .transform(lambda x: x.shift(1).rolling(window, min_periods=1).std())
            )
            df[z_col] = (df[stat] - df[colname]) / df[std_col]
    
    return df

def main():
    df = pd.read_csv(INPUT_FILE)
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    
    # Add rolling averages and z-scores
    df = add_rolling_features(df)

    # Drop games without any history (first game or missing data)
    df = df.dropna(subset=[col for col in df.columns if "_AVG" in col])

    # Optional: Add target column for modeling (e.g., OVER 14.5 PTS)
    df["TARGET_OVER_14.5_PTS"] = (df["PTS"] > 14.5).astype(int)

    # Save output
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Engineered features saved to {OUTPUT_FILE} ({len(df)} rows)")

if __name__ == "__main__":
    main()
