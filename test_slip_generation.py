#!/usr/bin/env python3
"""Test slip generation with debug info"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slips_generator import SlipsGenerator
from datetime import datetime

print("🔧 Testing slip generation with debug mode...")

generator = SlipsGenerator(min_confidence=0.65)
print(f"✅ Generator initialized with min_confidence=0.65")

# Generate slips for today
slips = generator.generate_slips(
    start_date=datetime(2025, 7, 1),
    end_date=datetime(2025, 7, 1)
)

print(f"\n📊 Generated {len(slips)} slips")

# If no slips, let's try with lower confidence
if len(slips) == 0:
    print("\n🔄 Trying with lower confidence (0.50)...")
    generator.min_confidence = 0.50
    slips = generator.generate_slips(
        start_date=datetime(2025, 7, 1),
        end_date=datetime(2025, 7, 1)
    )
    print(f"📊 Generated {len(slips)} slips with lower confidence")
    
# Check what the issue might be
print("\n🔍 Checking generator internals...")
print(f"League ID being used: {getattr(generator, 'league_id', 'Not set')}")
