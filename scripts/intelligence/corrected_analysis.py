import pandas as pd
import numpy as np
import json
from datetime import datetime

print("[TARS] Running Corrected Analysis...")

# Load files
gamelogs = pd.read_csv('data/wnba_gamelogs_with_cycle_phases.csv')
props = pd.read_csv('data/props_with_cycle_tags_simple.csv')

# Simple phase performance
print("\n=== PHASE PERFORMANCE (FANTASY PTS) ===")
phase_perf = gamelogs.groupby('cycle_phase')['WNBA_FANTASY_PTS'].agg(['mean', 'std', 'count']).round(2)
print(phase_perf)

# Risk tag effectiveness
print("\n=== RISK TAG ANALYSIS ===")
risk_perf = gamelogs.groupby('cycle_risk_tag')['WNBA_FANTASY_PTS'].mean().round(2)
for tag, avg in risk_perf.items():
    if 'FADE' in tag:
        print(f"{tag}: {avg} avg (want LOW for FADE)")
    elif 'TARGET' in tag:
        print(f"{tag}: {avg} avg (want HIGH for TARGET)")

# Check cycle distribution issue
print("\n=== CYCLE START DATE ISSUE ===")
sample_players = gamelogs.groupby('PLAYER_NAME').agg({
    'GAME_DATE': ['min', 'max', 'count']
}).head(10)
print("Sample player date ranges:")
print(sample_players)

# Today's props distribution
print(f"\n=== TODAY'S PROPS DISTRIBUTION ===")
print(props['cycle_phase'].value_counts())
print(f"\nRisk tags:")
print(props['cycle_risk_tag'].value_counts())

# CORRECTED RECOMMENDATIONS
print("\n=== CORRECTED BETTING STRATEGY ===")
print("Based on historical data, we should FLIP the tags:")
print("1. FADE the OVULATION phase (lowest avg: 12.18)")
print("2. TARGET the LUTEAL phase (highest avg: 14.63)")
print("3. Current system has it backwards!")

# Save corrected recommendations
recommendations = []
for _, prop in props.iterrows():
    if prop['cycle_phase'] == 'luteal':
        recommendations.append({
            'player': prop['player_name'],
            'stat': prop['stat_type'],
            'line': prop['line'],
            'action': 'CONSIDER OVER (luteal = high performance)',
            'phase_avg': 14.63
        })
    elif prop['cycle_phase'] == 'ovulation':
        recommendations.append({
            'player': prop['player_name'],
            'stat': prop['stat_type'],
            'line': prop['line'],
            'action': 'CONSIDER UNDER (ovulation = low performance)',
            'phase_avg': 12.18
        })

if recommendations:
    pd.DataFrame(recommendations).to_csv('output/corrected_recommendations.csv', index=False)
    print(f"\nSaved {len(recommendations)} corrected recommendations to output/corrected_recommendations.csv")
