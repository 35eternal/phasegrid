import pandas as pd

df = pd.read_csv("output/phase_results_tracker.csv")

# Filter out unknown
df_clean = df[df["Phase"] != "Unknown"]

print("YOUR BETTING RESULTS:")
print("-"*40)
for _, row in df_clean.iterrows():
    result_symbol = "✓" if row["Result"] == "W" else "✗"
    print(f"{result_symbol} {row['Player']} - {row['Stat']} ({row['Phase']}) = {row['Payout']:+.3f}")

print(f"\nTOTAL: {df_clean['Payout'].sum():+.3f} units")
print(f"Luteal only: {df_clean[df_clean['Phase'] == 'luteal']['Payout'].sum():+.3f} units")
