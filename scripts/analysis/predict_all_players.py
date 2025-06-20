import os
import pandas as pd
import numpy as np
from xgboost import XGBRegressor

def predict_all_players(data_dir="data/player_gamelogs", year=2024):
    predictions = []

    for filename in os.listdir(data_dir):
        if not filename.endswith(f"_{year}.csv"):
            continue

        player_name = filename.replace(f"_{year}.csv", "").replace("_", " ")

        try:
            df = pd.read_csv(os.path.join(data_dir, filename))
            df["PTS"] = pd.to_numeric(df["PTS"], errors="coerce")
            df["Date"] = pd.to_datetime(df["Date"].str.strip(), format="%b %d", errors="coerce")
            df["Date"] = df["Date"].apply(lambda d: d.replace(year=year) if pd.notnull(d) else d)
            df = df.dropna(subset=["PTS", "Date"]).sort_values("Date")

            df["Rolling_3"] = df["PTS"].rolling(3).mean()
            df["Rolling_5"] = df["PTS"].rolling(5).mean()
            df["Game_Num"] = range(1, len(df) + 1)
            df["Prev_PTS"] = df["PTS"].shift(1)
            df = df.dropna()

            features = ["Game_Num", "Rolling_3", "Rolling_5", "Prev_PTS"]
            X = df[features]
            y = df["PTS"]

            if len(X) < 3:
                continue  # not enough data to model

            model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, verbosity=0)
            model.fit(X, y)

            latest = df.iloc[-1]
            next_input = pd.DataFrame([{
                "Game_Num": latest["Game_Num"] + 1,
                "Rolling_3": latest["Rolling_3"],
                "Rolling_5": latest["Rolling_5"],
                "Prev_PTS": latest["PTS"],
            }])

            prediction = model.predict(next_input)[0]
            predictions.append((player_name, prediction))

        except Exception as e:
            print(f"❌ Failed on {player_name}: {e}")

    # Output leaderboard
    if predictions:
        leaderboard = pd.DataFrame(predictions, columns=["Player", "Predicted_PTS"])
        leaderboard = leaderboard.sort_values("Predicted_PTS", ascending=False).reset_index(drop=True)
        print("\n🏀 Predicted Next Game Points Leaderboard:")
        print(leaderboard)
    else:
        print("⚠️ No valid predictions were generated.")

if __name__ == "__main__":
    predict_all_players()
