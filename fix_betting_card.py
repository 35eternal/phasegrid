import pandas as pd

# Read your betting card
df = pd.read_csv('output/daily_betting_card.csv')

# Check if there's a Kelly-related column with different name
kelly_columns = [col for col in df.columns if 'kelly' in col.lower()]
print(f"Found Kelly-related columns: {kelly_columns}")

# If there's a kelly column with different name, rename it
if kelly_columns and 'raw_kelly' not in df.columns:
    df['raw_kelly'] = df[kelly_columns[0]]
elif 'edge' in df.columns:
    # If no Kelly column, calculate from edge (simplified)
    df['raw_kelly'] = df['edge'] * 0.5  # Conservative Kelly
else:
    # Default fallback
    df['raw_kelly'] = 0.02  # 2% default

# Save the fixed file
df.to_csv('daily_betting_card_fixed.csv', index=False)
print("Fixed betting card saved!")
