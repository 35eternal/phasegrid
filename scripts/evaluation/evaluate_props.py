# scripts/evaluate_props.py

import pandas as pd
import joblib
from scripts.model_features import FEATURE_COLUMNS
from scripts.utils import calculate_implied_prob, calculate_ev

MODEL_PATH = "models/prop_hit_predictor.joblib"
LOG_PATH = "data/wnba_2024_gamelogs.csv"
PROP_PATH = "data/prizepicks_wnba_props.csv"
OUTPUT_PATH = "data/predicted_props.csv"

def evaluate_props():
    # Load data
    try:
        props = pd.read_csv(PROP_PATH)
        logs = pd.read_csv(LOG_PATH)
        clf = joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"❌ Failed to load: {e}")
        return

    props = props[props["stat"] == "points"]  # Focus on PTS for now
    output = []

    for _, row in props.iterrows():
        player_name = row["player"]
        line = row["line"]
        try:
            # Use most recent game averages for prediction
            recent = logs[logs["PLAYER_NAME"] == player_name]
            if recent.empty:
                continue

            features = recent[FEATURE_COLUMNS].mean().values.reshape(1, -1)
            prob = clf.predict_proba(features)[0][1] * 100
            implied = calculate_implied_prob(-115)
            ev = calculate_ev(prob, -115)

            output.append({
                "Player": player_name,
                "Line": line,
                "Hit Prob (%)": round(prob, 2),
                "Implied Prob (%)": round(implied, 2),
                "Expected Value": round(ev, 2),
                "Model EV+": "✅" if ev > 0 else ""
            })
        except Exception as e:
            print(f"⚠️ Failed to evaluate {player_name}: {e}")

    df = pd.DataFrame(output)
    df.sort_values("Expected Value", ascending=False).to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Saved predictions to {OUTPUT_PATH} — {len(df)} props evaluated.")

if __name__ == "__main__":
    evaluate_props()
