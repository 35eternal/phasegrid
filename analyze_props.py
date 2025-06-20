# Additional analysis script
import pandas as pd
from core.backtester import HistoricalBacktester, BacktestConfig

# Re-create the backtester with same config
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

# Load data
df = pd.read_csv("data/wnba_combined_gamelogs.csv")
df = df.rename(columns=column_mapping)
backtester.historical_data = df

# Just generate props to see the synthetic line patterns
backtester.historical_data['Date'] = pd.to_datetime(backtester.historical_data['Date'])
start_date = pd.to_datetime(config.start_date)
end_date = pd.to_datetime(config.end_date)
backtester.historical_data = backtester.historical_data[
    (backtester.historical_data['Date'] >= start_date) & 
    (backtester.historical_data['Date'] <= end_date)
].sort_values(['Player', 'Date']).reset_index(drop=True)

backtester.load_historical_props()

print(f"Generated {len(backtester.synthetic_props)} props")
print("Sample props:")
for i, prop in enumerate(backtester.synthetic_props[:10]):
    print(f"{prop.player_name} {prop.stat_type} {prop.line_value} on {prop.game_date}")
