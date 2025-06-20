# analyze_gamelog.py

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/clark_2024_gamelog.csv")

# Parse minutes
df["MP_float"] = df["MP"].str.split(":").apply(lambda x: int(x[0]) + int(x[1])/60)
df["Date"] = pd.to_datetime(df["Date"])

# Rolling average of points and assists
df["PTS_roll"] = df["PTS"].rolling(window=3).mean()
df["AST_roll"] = df["AST"].rolling(window=3).mean()

# Plot
plt.figure(figsize=(12, 6))
plt.plot(df["Date"], df["PTS"], label="Points", marker="o")
plt.plot(df["Date"], df["PTS_roll"], label="Rolling PTS (3)", linestyle="--")
plt.plot(df["Date"], df["AST"], label="Assists", marker="x", alpha=0.6)
plt.plot(df["Date"], df["AST_roll"], label="Rolling AST (3)", linestyle="--", alpha=0.6)

plt.title("Caitlin Clark - Game Log Trends")
plt.xlabel("Date")
plt.ylabel("Stat Value")
plt.legend()
plt.tight_layout()
plt.show()
