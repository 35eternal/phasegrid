#!/usr/bin/env python3
"""Check PrizePicks with correct parameters"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from odds_provider.prizepicks import PrizePicksClient
from datetime import datetime
import json

print("🔍 Fetching WNBA projections with CORRECT parameters...")

# Initialize the client
client = PrizePicksClient()

# Use correct parameters: league (not league_id) and include_live
projections = client.fetch_projections(league="WNBA", include_live=True)
print(f"\n📊 Found {len(projections)} projections")

# Try to understand the data structure
if projections:
    # Check if it's a dict with data inside
    if isinstance(projections, dict):
        print(f"📦 Response is a dict with keys: {list(projections.keys())[:5]}")
        
        # Look for the actual projections data
        if 'data' in projections:
            proj_list = projections['data']
            print(f"📊 Found {len(proj_list)} projections in 'data' key")
            
            # Show first projection structure
            if proj_list:
                first = proj_list[0]
                print(f"\n🔍 First projection structure:")
                print(f"Keys: {list(first.keys())}")
                
                # Try to find player info
                if 'attributes' in first:
                    attrs = first['attributes']
                    print(f"\nAttributes: {list(attrs.keys())[:10]}")
                    
                    # Show player name
                    if 'new_player' in attrs:
                        print(f"Player: {attrs['new_player'].get('name', 'No name')}")
                    if 'stat_type' in attrs:
                        print(f"Stat: {attrs['stat_type']}")
                    if 'line_score' in attrs:
                        print(f"Line: {attrs['line_score']}")
                        
    else:
        print(f"📦 Response is a {type(projections)}")
        
# Save for inspection
with open('prizepicks_correct.json', 'w') as f:
    json.dump(projections if isinstance(projections, dict) else {"data": projections[:3]}, f, indent=2, default=str)
print("\n💾 Saved to prizepicks_correct.json")
