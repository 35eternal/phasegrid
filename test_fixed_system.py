#!/usr/bin/env python3
"""Test the FIXED slips generator"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🎯 TESTING FIXED SLIPS GENERATOR")
print("=" * 40)

# Wait for rate limit
print("Waiting 30 seconds for rate limit...")
time.sleep(30)

from slips_generator import generate_slips
import json

# Generate slips with correct league ID
print("\n📊 Generating slips with fixed league ID...")
slips = generate_slips(
    start_date="2025-07-01",
    end_date="2025-07-01",
    min_confidence=0.50  # Lower threshold
)

print(f"✅ Generated {len(slips)} slips")

if slips:
    # Check if we have real player names now
    first_slip = slips[0]
    player_name = first_slip.get('player', 'Unknown')
    
    if player_name != 'Unknown':
        print("\n🎉 SUCCESS! Got real player data!")
        print("\n📋 First 3 slips:")
        for slip in slips[:3]:
            print(f"\n{slip.get('player')} - {slip.get('prop_type')}")
            print(f"  {slip.get('pick').upper()} {slip.get('line')} @ {slip.get('odds')}")
            print(f"  Confidence: {slip.get('confidence', 0):.0%}")
            
        # Save successful slips
        with open('working_betting_card.json', 'w') as f:
            json.dump(slips, f, indent=2)
        print("\n💾 Saved to working_betting_card.json")
        
        # Run auto_paper
        print("\n🚀 Running full pipeline...")
        os.system("python auto_paper_fixed.py --production --bypass-guard-rail")
    else:
        print("\n⚠️ Still getting Unknown players - checking API response...")
        
        # Debug the API response
        from slips_generator import PrizePicksClient
        client = PrizePicksClient()
        projections = client.get_projections("WNBA")
        print(f"Raw projections count: {len(projections)}")
        if projections:
            print("\nFirst projection structure:")
            import pprint
            pprint.pprint(projections[0])
