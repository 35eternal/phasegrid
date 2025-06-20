# Analyze the UNDER bias by stat type - FIXED VERSION
import pandas as pd
from core.backtester import HistoricalBacktester, BacktestConfig

# Recreate backtester to analyze patterns
column_mapping = {
    'GAME_DATE': 'Date',
    'PLAYER_NAME': 'Player', 
    'FG3M': '3PM'
}

config = BacktestConfig(
    start_date="2024-07-01",
    end_date="2024-09-01",
    min_games_for_prediction=3
)

backtester = HistoricalBacktester(config)
df = pd.read_csv("data/wnba_combined_gamelogs.csv")
df = df.rename(columns=column_mapping)

# Fix the date parsing with mixed format
df['Date'] = pd.to_datetime(df['Date'], format='mixed')
backtester.historical_data = df

start_date = pd.to_datetime(config.start_date)
end_date = pd.to_datetime(config.end_date)
backtester.historical_data = backtester.historical_data[
    (backtester.historical_data['Date'] >= start_date) & 
    (backtester.historical_data['Date'] <= end_date)
].sort_values(['Player', 'Date']).reset_index(drop=True)

print(f"Loaded {len(backtester.historical_data)} games")

# Generate props and predictions
backtester.load_historical_props()
backtester.simulate_predictions()

# Analyze by stat type
placed_bets = [r for r in backtester.prediction_results if r.result != 'NO_BET']

print("=== DETAILED STAT ANALYSIS ===")
for stat in ['PTS', 'REB', 'AST', 'STL', 'BLK', '3PM']:
    stat_bets = [r for r in placed_bets if r.stat_type == stat]
    if stat_bets:
        wins = len([r for r in stat_bets if r.result == 'WIN'])
        win_rate = (wins / len(stat_bets)) * 100
        avg_line = sum([r.line_value for r in stat_bets]) / len(stat_bets)
        avg_actual = sum([r.actual_value for r in stat_bets]) / len(stat_bets)
        line_vs_actual = ((avg_actual - avg_line) / avg_line) * 100
        
        print(f"{stat}:")
        print(f"  Bets: {len(stat_bets)}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Avg Line: {avg_line:.1f}")
        print(f"  Avg Actual: {avg_actual:.1f}")
        print(f"  Line vs Actual: {line_vs_actual:.1f}% {'UNDER' if line_vs_actual < 0 else 'OVER'}")
        print()

# Check if synthetic lines are too high
print("=== LINE ANALYSIS ===")
total_line = sum([r.line_value for r in placed_bets])
total_actual = sum([r.actual_value for r in placed_bets])
avg_line = total_line / len(placed_bets)
avg_actual = total_actual / len(placed_bets)
overestimate = ((avg_line - avg_actual) / avg_actual) * 100

print(f"Average synthetic line: {avg_line:.2f}")
print(f"Average actual performance: {avg_actual:.2f}")
print(f"Lines overestimate by: {overestimate:.1f}%")

if overestimate > 5:
    print("🎯 SYNTHETIC LINES ARE TOO HIGH!")
    print("   This explains the UNDER bias")
    print("   Real books might have similar overpricing")
elif overestimate < -5:
    print("⚠️  Synthetic lines might be too low")
else:
    print("✅ Synthetic lines seem reasonable")

# Show sample predictions
print(f"\n=== SAMPLE PREDICTIONS ===")
sample_bets = placed_bets[:5]
for bet in sample_bets:
    outcome = "✅" if bet.result == "WIN" else "❌"
    print(f"{outcome} {bet.player_name} {bet.stat_type} UNDER {bet.line_value} (actual: {bet.actual_value})")
