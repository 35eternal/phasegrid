import pandas as pd

# Let's check the actual date format in your data
df = pd.read_csv("data/wnba_combined_gamelogs.csv")
print("Sample GAME_DATE values:")
print(df['GAME_DATE'].head(10).tolist())
print(f"Date type: {type(df['GAME_DATE'].iloc[0])}")
print(f"Unique date count: {df['GAME_DATE'].nunique()}")
print(f"Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
