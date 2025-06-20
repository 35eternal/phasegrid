import sys
sys.path.append('.')  # Add current directory to path

from modules.wnba_betting_modules import BettingSystemEnhancer
import pandas as pd

# Check the betting card format first
df = pd.read_csv('output/daily_betting_card.csv')
print(f"Current columns: {list(df.columns)}")

# Initialize enhancer
enhancer = BettingSystemEnhancer()

try:
    # Use the fixed file if we created one
    input_file = 'daily_betting_card_fixed.csv' if 'daily_betting_card_fixed.csv' else 'output/daily_betting_card.csv'
    
    enhanced_card = enhancer.enhance_betting_card(
        input_path=input_file,
        output_path='output/daily_betting_card_adjusted.csv',
        live_odds_path='live_odds.csv'
    )
    print("Enhancement successful!")
    print(enhanced_card[['player_name', 'stat_type', 'kelly_used', 'actual_odds']].head())
except Exception as e:
    print(f"Error: {e}")
