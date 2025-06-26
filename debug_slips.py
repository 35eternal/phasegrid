#!/usr/bin/env python3
"""Debug script to check why no slips are being generated"""

from slips_generator import generate_slips
from datetime import datetime

print(f"Testing slip generation for today: {datetime.now().strftime('%Y-%m-%d')}")

# Try with different confidence thresholds
for min_conf in [0.1, 0.3, 0.5, 0.65]:
    slips = generate_slips(
        start_date=datetime.now().strftime('%Y-%m-%d'),
        end_date=datetime.now().strftime('%Y-%m-%d'),
        min_confidence=min_conf
    )
    print(f"With min_confidence={min_conf}: {len(slips)} slips generated")
    
    if slips and len(slips) > 0:
        print(f"  Sample slip: {slips[0].get('player', 'Unknown')} - {slips[0].get('confidence', 0)}")
