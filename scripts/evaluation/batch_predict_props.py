import pandas as pd
import joblib
import numpy as np
from model_features import get_model_input_features
from sklearn.linear_model import LogisticRegression

MODEL_PATH = "models/prop_hit_predictor.joblib"
DATA_PATH = "data/prizepicks_wnba_props.csv"
OUTPUT_PATH = "data/profitable_props.csv"

def implied_prob_from_odds(odds):
    odds = float(odds)
    return abs(odds) / (abs(odds) + 100) if odds > 0 else 100 / (abs(odds) + 100)

def run_batch_prediction():
    print("📊 Running batch EV predictions...")
    df = pd.read_csv(DATA_PATH)
    model = joblib.load(MODEL_PATH)

    profitable_rows = []

    for _, row in df.iterrows():
        player_name = row.get("player")
        line = row.get("line")
        side = row.get("PICK_TYPE")
        odds = row.get("ODDS")

        try:
            features = get_model_input_features(player_name)

            # Skip if features are missing or contain NaNs
            if features is None or np.isnan(features).any():
                print(f"⚠️ Skipped: {player_name} (missing or invalid features)")
                continue

            proba = model.predict_proba([features])[0][1]  # probability of hitting the over
            if side.upper() == "UNDER":
                proba = 1 - proba

            implied = implied_prob_from_odds(odds)
            expected_value = 100 * (proba - implied)

            if expected_value > 0:
                row["MODEL_PROB"] = round(proba * 100, 2)
                row["EXPECTED_VALUE"] = round(expected_value, 2)
                profitable_rows.append(row)

        except Exception as e:
            print(f"❌ Error with {player_name}: {str(e)}")
            continue  # Skip broken rows

    if profitable_rows:
        result_df = pd.DataFrame(profitable_rows)
        result_df.to_csv(OUTPUT_PATH, index=False)
        print(f"✅ Found {len(result_df)} +EV props. Saved to {OUTPUT_PATH}")
    else:
        print("❌ No profitable props found.")

if __name__ == "__main__":
    run_batch_prediction()
