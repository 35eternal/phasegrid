import pandas as pd

print("[TARS] Applying Risk Tag Inversion Fix...")

# Load props
props = pd.read_csv('data/props_with_cycle_tags_simple.csv')

# Invert the risk tags based on actual performance data
def fix_risk_tag(row):
    phase = row['cycle_phase']
    if phase == 'luteal':
        return 'TARGET_LUTEAL'  # High performance phase
    elif phase == 'ovulation':
        return 'FADE_OVULATION'  # Low performance phase
    elif phase == 'menstrual':
        return 'FADE_MENSTRUAL'  # Low performance phase
    elif phase == 'follicular' and row['cycle_day'] >= 10:
        return 'TARGET_FOLLICULAR'  # Good performance
    else:
        return 'NEUTRAL'

props['corrected_risk_tag'] = props.apply(fix_risk_tag, axis=1)

# Save corrected props
props.to_csv('data/props_with_corrected_risk_tags.csv', index=False)

# Show distribution
print("\nCorrected Risk Tags:")
print(props['corrected_risk_tag'].value_counts())

# Generate top plays
print("\n=== TOP BETTING PLAYS ===")
print("\nSTRONG OVER PLAYS (TARGET_LUTEAL):")
luteal_plays = props[props['corrected_risk_tag'] == 'TARGET_LUTEAL'].head(5)
for _, p in luteal_plays.iterrows():
    print(f"  {p['player_name']} {p['stat_type']} OVER {p['line']}")

print("\nSTRONG UNDER PLAYS (FADE_OVULATION):")
ovulation_plays = props[props['corrected_risk_tag'] == 'FADE_OVULATION'].head(5)
for _, p in ovulation_plays.iterrows():
    print(f"  {p['player_name']} {p['stat_type']} UNDER {p['line']}")
