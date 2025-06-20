import pandas as pd

# Load files
props = pd.read_csv('data/wnba_clean_props_for_betting.csv')
cycles = pd.read_csv('data/wnba_gamelogs_with_cycle_phases.csv')

# Show columns
print("Props columns:", props.columns.tolist()[:10])
print("Cycles columns:", cycles.columns.tolist()[:10])

# Select just the cycle info we need
cycle_info = cycles[['PLAYER_ID', 'GAME_DATE', 'cycle_phase', 'cycle_day', 
                     'phase_volatility', 'cycle_confidence', 'perf_trend', 'cycle_risk_tag']].copy()

# Handle column name mismatches
if 'player_id' in props.columns:
    cycle_info['player_id'] = cycle_info['PLAYER_ID']
    merge_cols = ['player_id']
else:
    merge_cols = ['PLAYER_ID']

# Check date column
if 'game_date' in props.columns:
    cycle_info['game_date'] = cycle_info['GAME_DATE']
    merge_cols.append('game_date')
else:
    merge_cols.append('GAME_DATE')

# Merge
try:
    props_enhanced = pd.merge(props, cycle_info, on=merge_cols, how='left')
    props_enhanced.to_csv('data/wnba_clean_props_for_betting_v2.csv', index=False)
    print("Success! Enhanced props saved.")
except Exception as e:
    print(f"Merge failed: {e}")
    print("Continuing without props enhancement...")
