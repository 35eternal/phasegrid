#!/usr/bin/env python3
"""Direct API test"""
import requests
import json
import time

print("🌐 DIRECT PRIZEPICKS API TEST")
print("=" * 40)

# Wait to avoid rate limit
print("Waiting 30 seconds for rate limit...")
time.sleep(30)

# Try the direct API URL from your previous output
url = "https://api.prizepicks.com/projections"
params = {
    "league_id": 7,  # WNBA
    "per_page": 250,
    "single_stat": True,
    "include": "stat_type,new_player,league,game"
    # Note: removed "live" parameter
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

print(f"\n📡 Calling: {url}")
print(f"Parameters: {json.dumps(params, indent=2)}")

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        projections = data.get('data', [])
        print(f"✅ Found {len(projections)} projections")
        
        if projections:
            print("\n📋 First 3 projections:")
            for i, proj in enumerate(projections[:3]):
                attrs = proj.get('attributes', {})
                player = attrs.get('new_player', {}).get('name', 'Unknown')
                stat = attrs.get('stat_type', 'Unknown')
                line = attrs.get('line_score', 'N/A')
                print(f"  {player} - {stat}: {line}")
                
            # Save for inspection
            with open('direct_api_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("\n💾 Saved full response to direct_api_response.json")
    else:
        print(f"❌ API returned: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
