#!/usr/bin/env python3
"""Try all possible API variations"""
import requests
import json
import time

print("🔍 TRYING ALL PRIZEPICKS API VARIATIONS")
print("=" * 40)

base_url = "https://api.prizepicks.com"

# Different endpoint variations to try
endpoints = [
    "/projections",
    "/projections/pickem",
    "/leagues/7/projections",
    "/v1/projections",
    "/api/projections"
]

# Different parameter combinations
param_sets = [
    {"league_id": 7, "per_page": 250, "single_stat": True, "game_mode": "pickem"},
    {"league_id": 7, "per_page": 250},
    {"league": "WNBA", "per_page": 250},
    {"sport_id": 7, "per_page": 250},
    {}  # No params
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://app.prizepicks.com/'
}

print("Waiting 30 seconds for rate limit...")
time.sleep(30)

found_data = False

for endpoint in endpoints:
    if found_data:
        break
        
    for params in param_sets:
        if found_data:
            break
            
        url = base_url + endpoint
        print(f"\n🔗 Trying: {url}")
        print(f"   Params: {params}")
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check different data structures
                projections = None
                if isinstance(data, dict):
                    projections = data.get('data', data.get('projections', data.get('items', [])))
                elif isinstance(data, list):
                    projections = data
                    
                if projections and len(projections) > 0:
                    print(f"   ✅ FOUND {len(projections)} PROJECTIONS!")
                    
                    with open('working_api_response.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    print("   💾 Saved to working_api_response.json")
                    found_data = True
                    
                    # Show sample
                    first = projections[0] if isinstance(projections, list) else list(projections.values())[0]
                    print(f"   Sample: {json.dumps(first, indent=2)[:200]}...")
                    
        except Exception as e:
            print(f"   Error: {str(e)[:50]}")
            
        time.sleep(2)  # Small delay between attempts

if not found_data:
    print("\n❌ No working endpoint found")
    print("\n🤔 Possible reasons:")
    print("1. Lines haven't been released to API yet")
    print("2. API requires authentication")
    print("3. Commissioner's Cup uses different endpoint")
