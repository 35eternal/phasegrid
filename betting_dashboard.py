import pandas as pd
from datetime import datetime

# Load upcoming bets
bets = pd.read_csv('upcoming_cycle_bets.csv')
bets['date'] = pd.to_datetime(bets['date'])

# Separate by phase
pre_dip = bets[bets['phase'] == 'PRE_DIP'].head(10)
recovery = bets[bets['phase'] == 'RECOVERY'].head(10)

print("="*60)
print("🎲 WNBA CYCLE BETTING DASHBOARD")
print("="*60)
print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

print("\n💰 HIGHEST VALUE BETS (PRE-DIP PHASE):")
print("-"*60)
print("DATE        PLAYER                 STAT  CONFIDENCE  DROP%")
print("-"*60)
for _, bet in pre_dip.iterrows():
    conf_pct = bet['confidence'] * 100
    print(f"{bet['date'].strftime('%m/%d')}       {bet['player']:<20} {bet['stat']}    {conf_pct:.1f}%      {bet['expected_drop']:.0f}%")
    if conf_pct >= 90:
        print("            ⭐ PREMIUM BET - 90%+ CONFIDENCE!")

print("\n📈 RECOVERY PLAYS (BOUNCE-BACK BETS):")
print("-"*60)
print("DATE        PLAYER                 STAT  CONFIDENCE")
print("-"*60)
for _, bet in recovery.iterrows():
    conf_pct = bet['confidence'] * 100
    print(f"{bet['date'].strftime('%m/%d')}       {bet['player']:<20} {bet['stat']}    {conf_pct:.1f}%")

# Calculate expected value
print("\n💵 EXPECTED VALUE ANALYSIS:")
print("-"*60)

# Assuming $100 bets and standard -110 odds
bet_amount = 100
win_payout = 190.91  # $100 bet wins $90.91 at -110

high_conf_bets = bets[bets['confidence'] > 0.8]
total_bets = len(high_conf_bets)
expected_wins = high_conf_bets['confidence'].sum()
expected_value = (expected_wins * win_payout) - (total_bets * bet_amount)

print(f"High confidence bets (80%+): {total_bets}")
print(f"Expected wins: {expected_wins:.1f}")
print(f"Expected profit on ${total_bets * bet_amount} wagered: ${expected_value:.2f}")
print(f"ROI: {(expected_value / (total_bets * bet_amount)) * 100:.1f}%")

# Best single bet
best_bet = bets.loc[bets['confidence'].idxmax()]
print(f"\n🏆 BEST SINGLE BET:")
print(f"{best_bet['date']} - {best_bet['player']} {best_bet['stat']} {best_bet['bet_type']}")
print(f"Confidence: {best_bet['confidence'] * 100:.1f}%")

# Save summary
summary = {
    'generated': datetime.now().isoformat(),
    'total_opportunities': len(bets),
    'next_7_days': len(bets[bets['date'] <= datetime.now() + pd.Timedelta(days=7)]),
    'high_confidence_bets': len(high_conf_bets),
    'best_bet': f"{best_bet['player']} {best_bet['stat']} {best_bet['bet_type']} on {best_bet['date']}"
}

import json
with open('betting_dashboard.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\n✅ Dashboard saved to 'betting_dashboard.json'")
