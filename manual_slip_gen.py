#!/usr/bin/env python3
"""Quick test to generate slips for any available games"""
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import what we need
from odds_provider.prizepicks import PrizePicksClient
from slips_generator import generate_slips

print("🏀 PHASEGRID MANUAL SLIP GENERATOR")
print("=" * 40)

# Initialize PrizePicks client
client = PrizePicksClient()

# Fetch ALL projections, not just live
print("\n📊 Fetching all WNBA projections...")
projections = client.fetch_projections(league_id=7, live=False)
print(f"✅ Found {len(projections)} projections")

# Generate slips with lower threshold
print("\n🎯 Generating slips...")
slips = generate_slips(
    start_date=datetime.now().strftime("%Y-%m-%d"),
    end_date=datetime.now().strftime("%Y-%m-%d"),
    min_confidence=0.50
)

print(f"\n📋 Generated {len(slips)} slips")

if slips:
    print("\n🏆 TOP 3 SLIPS:")
    for i, slip in enumerate(slips[:3], 1):
        print(f"\n--- Slip {i} ---")
        print(f"Player: {slip.get('player')}")
        print(f"Prop: {slip.get('prop_type')} {slip.get('pick')} {slip.get('line')}")
        print(f"Odds: {slip.get('odds')}")
        print(f"Confidence: {slip.get('confidence', 0):.1%}")
        
    # Save to file
    import json
    with open('manual_slips.json', 'w') as f:
        json.dump(slips, f, indent=2)
    print("\n💾 Saved all slips to manual_slips.json")
else:
    print("\n⚠️ No slips generated. Checking why...")
    print("Possible reasons:")
    print("- No games scheduled for today")
    print("- Confidence calculations too strict")
    print("- Missing player/phase data")
