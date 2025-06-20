import pandas as pd
import numpy as np
import json
from datetime import datetime

print("[TARS] Running Cycle Phase Performance Analysis...")

# Load the enhanced gamelogs
gamelogs = pd.read_csv('data/wnba_gamelogs_with_cycle_phases.csv')

# Analyze historical performance by cycle phase
print("\n=== HISTORICAL PERFORMANCE BY CYCLE PHASE ===")
phase_analysis = gamelogs.groupby('cycle_phase').agg({
    'WNBA_FANTASY_PTS': ['mean', 'std', 'count'],
    'PTS': ['mean', 'std'],
    'REB': ['mean', 'std'],
    'AST': ['mean', 'std'],
    'perf_trend': ['mean', 'std']
}).round(2)

print(phase_analysis)

# Analyze risk tag effectiveness
print("\n\n=== RISK TAG PERFORMANCE ANALYSIS ===")
risk_analysis = gamelogs.groupby('cycle_risk_tag').agg({
    'WNBA_FANTASY_PTS': ['mean', 'std', 'count'],
    'perf_trend': ['mean', 'std']
}).round(2)

print(risk_analysis)

# Calculate over/under rates by phase
print("\n\n=== PHASE VOLATILITY ANALYSIS ===")
# Group by phase and calculate variance from mean
for phase in gamelogs['cycle_phase'].unique():
    phase_data = gamelogs[gamelogs['cycle_phase'] == phase]
    
    # Calculate each player's variance from their own mean
    player_variances = []
    for player_id in phase_data['PLAYER_ID'].unique():
        player_phase_data = phase_data[phase_data['PLAYER_ID'] == player_id]
        if len(player_phase_data) > 2:
            variance = player_phase_data['WNBA_FANTASY_PTS'].std() / player_phase_data['WNBA_FANTASY_PTS'].mean()
            player_variances.append(variance)
    
    if player_variances:
        avg_variance = np.mean(player_variances)
        print(f"{phase}: {avg_variance:.3f} avg coefficient of variation (n={len(player_variances)} players)")

# Create recommendations for today's props
props = pd.read_csv('data/props_with_cycle_tags_simple.csv')

print("\n\n=== TODAY'S BETTING RECOMMENDATIONS ===")

# High confidence plays
high_conf_fade = props[props['cycle_risk_tag'].str.contains('FADE')]
high_conf_target = props[props['cycle_risk_tag'].str.contains('TARGET')]

print(f"\nFADE RECOMMENDATIONS ({len(high_conf_fade)} total):")
for _, row in high_conf_fade.head(5).iterrows():
    print(f"  - {row['player_name']} {row['stat_type']} UNDER {row['line']} ({row['cycle_phase']} phase)")

print(f"\nTARGET RECOMMENDATIONS ({len(high_conf_target)} total):")
for _, row in high_conf_target.head(5).iterrows():
    print(f"  - {row['player_name']} {row['stat_type']} OVER {row['line']} ({row['cycle_phase']} phase)")

# Save detailed report
report = {
    'generated_at': datetime.now().isoformat(),
    'phase_performance': phase_analysis.to_dict(),
    'risk_tag_performance': risk_analysis.to_dict(),
    'todays_props': {
        'total': len(props),
        'by_phase': props['cycle_phase'].value_counts().to_dict(),
        'by_risk_tag': props['cycle_risk_tag'].value_counts().to_dict()
    },
    'recommendations': {
        'fade_count': len(high_conf_fade),
        'target_count': len(high_conf_target)
    }
}

with open('output/cycle_analysis_report.json', 'w') as f:
    json.dump(report, f, indent=2, default=str)

print("\n[TARS] Full report saved to output/cycle_analysis_report.json")

# Final summary
print("\n\n=== EXECUTIVE SUMMARY ===")
print(f"1. Best FADE phase: {risk_analysis.loc[risk_analysis.index.str.contains('FADE'), ('WNBA_FANTASY_PTS', 'mean')].idxmin()}")
print(f"2. Best TARGET phase: {risk_analysis.loc[risk_analysis.index.str.contains('TARGET'), ('WNBA_FANTASY_PTS', 'mean')].idxmax()}")
print(f"3. Today's props: {len(high_conf_fade)} FADE plays, {len(high_conf_target)} TARGET plays")
