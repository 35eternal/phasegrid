import json
import os
from datetime import datetime

print("📁 Checking local data files...")

# Check props.json
if os.path.exists('props.json'):
    with open('props.json', 'r') as f:
        props = json.load(f)
        print(f"\n📊 props.json contains {len(props)} items")
        if props:
            print(f"Sample: {list(props[0].keys()) if isinstance(props, list) else list(props.keys())[:5]}")

# Check slips.json  
if os.path.exists('slips.json'):
    with open('slips.json', 'r') as f:
        slips = json.load(f)
        print(f"\n📋 slips.json contains {len(slips)} items")
        
# Check live_odds.csv
if os.path.exists('live_odds.csv'):
    size = os.path.getsize('live_odds.csv')
    print(f"\n📈 live_odds.csv: {size} bytes")
    # Show first few lines
    with open('live_odds.csv', 'r') as f:
        lines = f.readlines()[:5]
        print("First few lines:")
        for line in lines:
            print(f"  {line.strip()}")
