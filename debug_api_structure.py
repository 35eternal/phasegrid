#!/usr/bin/env python3
"""Debug PrizePicks API response structure"""
import sys
import os
import time
import json
import pprint
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 DEBUGGING PRIZEPICKS API STRUCTURE")
print("=" * 40)

# Wait for rate limit
print("Waiting 60 seconds for rate limit...")
time.sleep(60)

from slips_generator import PrizePicksClient

client = PrizePicksClient()

# Get WNBA projections
print("\n📊 Fetching WNBA projections...")
projections = client.get_projections("WNBA")

print(f"✅ Got {len(projections)} projections")

if projections:
    # Save raw response
    with open('raw_api_response.json', 'w') as f:
        json.dump(projections[:3], f, indent=2)
    
    print("\n🔍 First projection structure:")
    first = projections[0]
    
    # Print all keys
    print(f"\nTop-level keys: {list(first.keys())}")
    
    # Check for different possible structures
    if 'attributes' in first:
        print(f"\nAttributes keys: {list(first['attributes'].keys())[:10]}")
        attrs = first['attributes']
        
        # Look for player info
        for key in ['new_player', 'player', 'participant', 'name']:
            if key in attrs:
                print(f"\n{key}: {attrs[key]}")
                
        # Look for stat info
        for key in ['stat_type', 'stat', 'market', 'projection_type']:
            if key in attrs:
                print(f"\n{key}: {attrs[key]}")
                
        # Look for line info
        for key in ['line_score', 'line', 'projection', 'value']:
            if key in attrs:
                print(f"\n{key}: {attrs[key]}")
    
    # Pretty print the whole first projection
    print("\n📝 Full first projection:")
    pprint.pprint(first, width=120, depth=3)
else:
    print("❌ No projections returned")
    
    # Try direct API call to see what's happening
    import requests
    
    print("\n🌐 Trying direct API call...")
    url = "https://api.prizepicks.com/projections"
    params = {
        "league_id": 7,
        "per_page": 10,
        "single_stat": "true"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response has keys: {list(data.keys())}")
            if 'data' in data:
                print(f"Found {len(data['data'])} items in data")
    except Exception as e:
        print(f"Error: {e}")
