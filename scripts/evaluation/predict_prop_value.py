# scripts/predict_prop_value.py

import pandas as pd
import numpy as np
import argparse
import joblib
import os

MODEL_PATH = "models/prop_hit_predictor.joblib"
DATA_PATH = "data/wnba_2024_gamelogs.csv"

FEATURES = [
    "MIN", "FGA", "FG_PCT", "FG3A", "FG3_PCT", "FTA", "FT_PCT",
    "OREB", "DREB", "REB", "AST", "TOV", "STL", "BLK", "PFD"
]

def convert_min_sec(val):
    try:
        if isinstance(val, str) and ":" in val:
            mins, secs = map(int, val.split(":"))
            return mins + secs / 60
        elif isinstance(val, (int, float)):
            return val
    except:
        return None
    return None

def predict_prop(player_name, line, bet_type, odds):
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at {MODEL_PATH}")
        return
    
    model = joblib.load(MODEL_PATH)
    df = pd.read_csv(DATA_PATH)

    df["MIN"] = df["MIN_SEC"].apply(convert_min_sec)
    player_df = df[df["PLAYER_NAME"].str.lower() == player_name.lower()]

    if player_df.empty:
        print(f"❌ No data found for player: {player_name}")
        return

    player_df = player_df.dropna(subset=FEATURES + ["PTS"])

    if player_df.empty:
        print(f"❌ No complete stat rows available for {player_name}")
        return

    # Average features
    avg_features = player_df[FEATURES].mean().values.reshape(1, -1)

    # Predict probability of hit
    prob = model.predict_proba(avg_features)[0][1]  # Prob of hitting OVER

    if bet_type.upper() == "UNDER":
        prob = 1 - prob

    # Convert American odds to implied probability
    if odds < 0:
        implied_prob = abs(odds) / (abs(odds) + 100)
    else:
        implied_prob = 100 / (odds + 100)

    expected_value = (prob * (100 if odds > 0 else abs(odds))) - ((1 - prob) * (abs(odds) if odds < 0 else 100))

    print(f"\n📊 Prediction for {player_name} {bet_type.upper()} {line} points:")
    print(f"🔮 Model Hit Probability: {prob:.2%}")
    print(f"📉 Implied Probability from Odds: {implied_prob:.2%}")
    print(f"💸 Expected Value: {expected_value:.2f} (positive = +EV)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", type=str, required=True, help="Player name")
    parser.add_argument("--line", type=float, required=True, help="Points line (e.g., 17.5)")
    parser.add_argument("--type", type=str, choices=["OVER", "UNDER"], required=True, help="Bet type")
    parser.add_argument("--odds", type=int, required=True, help="American odds (e.g., -115)")

    args = parser.parse_args()
    predict_prop(args.player, args.line, args.type, args.odds)
