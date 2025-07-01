#!/usr/bin/env python3
"""Direct slip generation test"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slips_generator import generate_slips
from datetime import datetime
import json

print("🎯 DIRECT SLIP GENERATION TEST")
print("=" * 40)

# Try with very low confidence
for confidence in [0.30, 0.40, 0.50, 0.60]:
    print(f"\n📊 Testing with confidence threshold: {confidence}")
    
    slips = generate_slips(
        start_date="2025-07-01",
        end_date="2025-07-01",
        min_confidence=confidence
    )
    
    print(f"✅ Generated {len(slips)} slips")
    
    if slips:
        print("\n📋 First 3 slips:")
        for slip in slips[:3]:
            print(f"  {slip.get('player', 'Unknown')} - {slip.get('prop_type', 'Unknown')}")
            print(f"    {slip.get('pick', 'Unknown')} {slip.get('line', 'N/A')} @ {slip.get('odds', 'N/A')}")
            print(f"    Confidence: {slip.get('confidence', 0):.2%}")
            
        # Save the working slips
        with open(f'working_slips_{int(confidence*100)}.json', 'w') as f:
            json.dump(slips, f, indent=2)
        print(f"\n💾 Saved to working_slips_{int(confidence*100)}.json")
        break
