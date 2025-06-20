import pandas as pd
import numpy as np

print("[TARS] Finalizing Advanced Cycle Intelligence...")

# Load all data
adv_logs = pd.read_csv('data/wnba_gamelogs_advanced_cycles.csv')
props = pd.read_csv('data/props_with_corrected_risk_tags.csv')

# Get latest cycle info per player
latest_cycles = adv_logs.sort_values('GAME_DATE').groupby('PLAYER_NAME').last()

# Map advanced cycle data to props
enhanced_props = []
for idx, prop in props.iterrows():
    prop_dict = prop.to_dict()
    
    if prop['player_name'] in latest_cycles.index:
        player_data = latest_cycles.loc[prop['player_name']]
        prop_dict['adv_phase'] = player_data['adv_cycle_phase']
        prop_dict['adv_risk_tag'] = player_data['adv_risk_tag']
        prop_dict['adv_modifier'] = round(player_data['adv_perf_modifier'], 3)
        prop_dict['adv_confidence'] = round(player_data['adv_risk_confidence'], 2)
        
        # Adjust prediction with modifier
        if 'predicted_value' in prop_dict:
            prop_dict['adjusted_prediction'] = round(
                prop_dict['predicted_value'] * player_data['adv_perf_modifier'], 1
            )
    else:
        prop_dict['adv_phase'] = 'unknown'
        prop_dict['adv_risk_tag'] = 'NO_DATA'
        prop_dict['adv_modifier'] = 1.0
        prop_dict['adv_confidence'] = 0.5
        prop_dict['adjusted_prediction'] = prop_dict.get('predicted_value', 0)
    
    enhanced_props.append(prop_dict)

# Create final dataframe
final_props = pd.DataFrame(enhanced_props)

# Save final props
final_props.to_csv('data/final_props_with_advanced_cycles.csv', index=False)

print(f"\n[TARS] Enhanced {len(final_props)} props with advanced cycle intelligence")

# Generate betting card
print("\n" + "="*60)
print("TARS ADVANCED CYCLE BETTING CARD - 2025-06-17")
print("="*60)

# Strong plays
strong_plays = final_props[
    (final_props['adv_risk_tag'].str.contains('STRONG')) & 
    (final_props['adv_confidence'] >= 0.65)
].sort_values('adv_confidence', ascending=False)

print(f"\n🎯 STRONG PLAYS ({len(strong_plays)} total):")
for _, p in strong_plays.head(10).iterrows():
    action = 'OVER' if 'TARGET' in p['adv_risk_tag'] else 'UNDER'
    print(f"  {p['player_name']:<20} {p['stat_type']:<10} {action} {p['line']:<5} "
          f"[{p['adv_phase']}, conf: {p['adv_confidence']}]")

# Regular high-confidence plays
high_conf = final_props[
    (final_props['adv_confidence'] >= 0.60) & 
    (~final_props['adv_risk_tag'].str.contains('STRONG')) &
    (final_props['adv_risk_tag'] != 'NEUTRAL')
].sort_values('adv_confidence', ascending=False)

print(f"\n📊 HIGH CONFIDENCE PLAYS ({len(high_conf)} total):")
for _, p in high_conf.head(10).iterrows():
    action = 'OVER' if 'TARGET' in p['adv_risk_tag'] else 'UNDER'
    edge = abs(p.get('adjusted_prediction', p['line']) - p['line'])
    print(f"  {p['player_name']:<20} {p['stat_type']:<10} {action} {p['line']:<5} "
          f"[edge: {edge:.1f}]")

# Phase summary
print("\n📈 PHASE DISTRIBUTION:")
phase_counts = final_props['adv_phase'].value_counts()
for phase, count in phase_counts.items():
    if phase != 'unknown':
        print(f"  {phase}: {count} props")

# Save betting card
with open('output/tars_betting_card_20250617.txt', 'w') as f:
    f.write("TARS ADVANCED CYCLE BETTING CARD\n")
    f.write(f"Generated: {pd.Timestamp.now()}\n\n")
    
    f.write("STRONG PLAYS:\n")
    for _, p in strong_plays.head(20).iterrows():
        action = 'OVER' if 'TARGET' in p['adv_risk_tag'] else 'UNDER'
        f.write(f"{p['player_name']},{p['stat_type']},{action},{p['line']},{p['adv_risk_tag']},{p['adv_confidence']}\n")

print("\n[TARS] Betting card saved to output/tars_betting_card_20250617.txt")
print("\n🤖 TARS ADVANCED CYCLE INTELLIGENCE FULLY OPERATIONAL")
