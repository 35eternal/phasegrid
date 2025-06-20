# train_model.py

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
import joblib

# Paths
DATA_PATH = "data/wnba_2024_gamelogs.csv"
MODEL_PATH = "models/prop_hit_predictor.joblib"
os.makedirs("models", exist_ok=True)

# Load and validate dataset
df = pd.read_csv(DATA_PATH)

# Convert MIN_SEC to float minutes
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

df["MIN"] = df["MIN_SEC"].apply(convert_min_sec)

# Define target prop threshold — e.g., did player score 15+ points?
POINTS_LINE = 15.0
df["HIT"] = (df["PTS"] >= POINTS_LINE).astype(int)

# Select features for the model
feature_cols = [
    "MIN", "FGA", "FG_PCT", "FG3A", "FG3_PCT", "FTA", "FT_PCT",
    "OREB", "DREB", "REB", "AST", "TOV", "STL", "BLK", "PFD"
]

# Drop rows with missing values
df = df[feature_cols + ["HIT"]].dropna()

print(f"✅ Found {len(df)} valid rows for training.")

if len(df) < 10:
    print("❌ Not enough valid rows to train.")
    exit()

# Define X and y
X = df[feature_cols]
y = df["HIT"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, y_train)

# Save model
joblib.dump(clf, MODEL_PATH)

# Evaluate model
y_pred = clf.predict(X_test)
print("\n📈 Classification Report:")
print(classification_report(y_test, y_pred))

# Show top predictive features
feature_importance = pd.DataFrame({
    "Feature": feature_cols,
    "Coefficient": clf.coef_[0]
}).sort_values(by="Coefficient", ascending=False)

print("\n🔥 Top Predictive Features:")
print(feature_importance.to_string(index=False))
