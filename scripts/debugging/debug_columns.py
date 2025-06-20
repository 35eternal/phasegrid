import pandas as pd

df = pd.read_csv("data/merged_props_with_gamelogs.csv")

print("🧾 Columns in merged file:\n")
for col in df.columns:
    print(f"- {col}")
