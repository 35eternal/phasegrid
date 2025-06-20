import pandas as pd

# Load final props
props = pd.read_csv('data/final_props_with_advanced_cycles.csv')

# Filter for today's best bets
strong_bets = props[props['adv_risk_tag'].str.contains('STRONG')].sort_values('adv_confidence', ascending=False)

print("🎯 TARS TOP 5 BETS FOR TODAY:")
print("-" * 50)

for i, (_, bet) in enumerate(strong_bets.head(5).iterrows(), 1):
    print(f"{i}. {bet['player_name']} - {bet['stat_type']}")
    print(f"   PLAY: OVER {bet['line']}")
    print(f"   Confidence: {bet['adv_confidence']*100:.0f}%")
    print(f"   Phase: {bet['adv_phase']} (modifier: {bet['adv_modifier']})")
    print()

# Save to clipboard format
clipboard_text = []
for _, bet in strong_bets.head(10).iterrows():
    clipboard_text.append(f"{bet['player_name']} {bet['stat_type']} O{bet['line']}")

with open('output/betting_slip.txt', 'w') as f:
    f.write('\n'.join(clipboard_text))

print("Betting slip saved to output/betting_slip.txt")
