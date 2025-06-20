# scripts/patch_minutes.py

import pandas as pd

def convert_min_sec(val):
    try:
        if isinstance(val, str) and ":" in val:
            mins, secs = map(int, val.split(":"))
            return mins + secs / 60
        elif isinstance(val, (int, float)):
            return val
        else:
            return None
    except:
        return None

df = pd.read_csv("data/wnba_2024_gamelogs.csv")

# Convert MIN_SEC to float minutes
df["MIN"] = df["MIN_SEC"].apply(convert_min_sec)

# Overwrite the file with new float-style MIN
df.to_csv("data/wnba_2024_gamelogs.csv", index=False)

print("✅ Patched MIN column and saved updated game logs.")
