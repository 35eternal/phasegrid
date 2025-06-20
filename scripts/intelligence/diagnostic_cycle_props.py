import pandas as pd
import numpy as np

print("[TARS] Analyzing file structures...")

# Load both files
props = pd.read_csv('data/wnba_clean_props_for_betting.csv')
cycles = pd.read_csv('data/wnba_gamelogs_with_cycle_phases.csv')

print(f"\nProps shape: {props.shape}")
print(f"Props columns: {list(props.columns)}")
print(f"\nFirst 3 props rows:")
print(props.head(3))

print(f"\n\nCycles shape: {cycles.shape}")
print(f"Unique players in cycles: {cycles['PLAYER_ID'].nunique()}")

# Check if we can match by player name
print("\n[TARS] Checking player name matches...")
props_players = set(props['player_name'].unique())
cycles_players = set(cycles['PLAYER_NAME'].unique())

matches = props_players.intersection(cycles_players)
print(f"Matching players: {len(matches)} out of {len(props_players)} in props")

# Extract date from timestamp if it exists
if 'timestamp' in props.columns:
    print(f"\nTimestamp format: {props['timestamp'].iloc[0]}")
    try:
        props['extracted_date'] = pd.to_datetime(props['timestamp']).dt.date
        print(f"Date extraction successful. Sample dates: {props['extracted_date'].unique()[:3]}")
    except:
        print("Could not extract date from timestamp")

# Check what dates are in the gamelogs
print(f"\nGamelog date range: {cycles['GAME_DATE'].min()} to {cycles['GAME_DATE'].max()}")

# Try to create a simplified backtest dataset
print("\n[TARS] Creating simplified dataset for backtesting...")

# Get most recent cycle data per player
latest_cycles = cycles.sort_values('GAME_DATE').groupby('PLAYER_NAME').last()

# Create a mapping
player_cycle_map = latest_cycles[['cycle_phase', 'cycle_risk_tag', 'perf_trend', 'phase_volatility']].to_dict('index')

# Apply to props
props['cycle_phase'] = props['player_name'].map(lambda x: player_cycle_map.get(x, {}).get('cycle_phase', 'unknown'))
props['cycle_risk_tag'] = props['player_name'].map(lambda x: player_cycle_map.get(x, {}).get('cycle_risk_tag', 'NEUTRAL'))
props['perf_trend'] = props['player_name'].map(lambda x: player_cycle_map.get(x, {}).get('perf_trend', 1.0))

# Save simplified version
props.to_csv('data/props_with_cycle_tags_simple.csv', index=False)
print("\nSaved simplified props with cycle tags to: data/props_with_cycle_tags_simple.csv")

# Show sample
print("\nSample of enhanced props:")
print(props[['player_name', 'stat_type', 'predicted_value', 'cycle_phase', 'cycle_risk_tag', 'perf_trend']].head(10))
