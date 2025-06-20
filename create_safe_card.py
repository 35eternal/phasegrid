import pandas as pd

# Load enhanced card
df = pd.read_csv("output/daily_betting_card_adjusted.csv")

# Remove menstrual phase bets
df_safe = df[df["adv_phase"] != "menstrual"]

# Summary
print(f"Original bets: {len(df)}")
print(f"After removing menstrual: {len(df_safe)}")
print(f"Removed {len(df) - len(df_safe)} risky bets")

# Save
df_safe.to_csv("output/daily_betting_card_safe.csv", index=False)
print("\nSafe betting card saved to: output/daily_betting_card_safe.csv")

# Show top 10 bets
print("\nTop 10 safest bets:")
top10 = df_safe.nlargest(10, "kelly_used")[["player_name", "stat_type", "kelly_used", "adv_phase"]]
print(top10)
