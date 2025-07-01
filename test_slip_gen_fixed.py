#!/usr/bin/env python3
"""Test fetching all projections, not just live"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the actual module functions
from slips_generator import generate_slips
from datetime import datetime

print("🔧 Testing slip generation without live filter...")

# Try generating slips
try:
    # Use the function directly
    slips = generate_slips(
        start_date="2025-07-01",
        end_date="2025-07-01",
        min_confidence=0.50  # Lower threshold for testing
    )
    print(f"✅ Generated {len(slips)} slips")
    
    if slips:
        print("\n📋 First slip:")
        print(slips[0])
except Exception as e:
    print(f"❌ Error: {e}")
    
# Check what's in the existing data files
import json

print("\n📁 Checking existing data files...")
try:
    with open('props.json', 'r') as f:
        props = json.load(f)
        print(f"props.json has {len(props) if isinstance(props, list) else 'data'}")
except:
    print("Could not read props.json")
    
try:
    with open('slips.json', 'r') as f:
        slips_data = json.load(f)
        print(f"slips.json has {len(slips_data) if isinstance(slips_data, list) else 'data'}")
except:
    print("Could not read slips.json")
