#!/usr/bin/env python3
"""Test system with local data"""
import json
import os
from datetime import datetime

print("🏀 TESTING WITH LOCAL DATA")
print("=" * 40)

# Create test projections
test_projections = [
    {
        "player_name": "A'ja Wilson",
        "stat_type": "Points",
        "line": 24.5,
        "odds": -110,
        "confidence": 0.72
    },
    {
        "player_name": "Breanna Stewart",
        "stat_type": "Rebounds", 
        "line": 8.5,
        "odds": -115,
        "confidence": 0.68
    },
    {
        "player_name": "Napheesa Collier",
        "stat_type": "Assists",
        "line": 4.5,
        "odds": -105,
        "confidence": 0.65
    }
]

# Generate test slips
slips = []
for i, proj in enumerate(test_projections):
    slip = {
        "slip_id": f"TEST-{i+1}-{datetime.now().strftime('%Y%m%d')}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "player": proj["player_name"],
        "prop_type": proj["stat_type"],
        "line": proj["line"],
        "pick": "over" if proj["confidence"] > 0.7 else "under",
        "odds": proj["odds"],
        "confidence": proj["confidence"],
        "amount": 50.0,
        "reasoning": "Test slip for system verification"
    }
    slips.append(slip)

# Save test slips
with open('test_betting_card.json', 'w') as f:
    json.dump(slips, f, indent=2)

print(f"✅ Created {len(slips)} test slips")
print("\n📋 Test Betting Card:")
for slip in slips:
    print(f"\n{slip['player']} - {slip['prop_type']}")
    print(f"  {slip['pick'].upper()} {slip['line']} @ {slip['odds']}")
    print(f"  Confidence: {slip['confidence']:.0%}")
    print(f"  Bet: ${slip['amount']}")

print("\n💾 Saved to test_betting_card.json")
print("\n⚠️ Note: PrizePicks has no WNBA data available currently")
print("📅 This might be because:")
print("  - It's too early for tonight's games")
print("  - The Commissioner's Cup championship hasn't opened betting yet")
print("  - No regular season games today")
