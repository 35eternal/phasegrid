import requests
import json
from datetime import datetime

# Test the raw API directly
url = "https://api.prizepicks.com/projections"
params = {
    "league_id": 7,  # WNBA
    "per_page": 250,
    "single_stat": True,
    "include": "stat_type,new_player,league,game"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://app.prizepicks.com/"
}

print(f"Testing PrizePicks API at {datetime.now()}")
print(f"URL: {url}")
print(f"Params: {params}")
print("-" * 80)

response = requests.get(url, params=params, headers=headers)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResponse Keys: {list(data.keys())}")
    print(f"Data count: {len(data.get('data', []))}")
    print(f"Included count: {len(data.get('included', []))}")
    
    # Check if there's pagination info
    if 'links' in data:
        print(f"Links: {data['links']}")
    if 'meta' in data:
        print(f"Meta: {data['meta']}")
    
    # If we have data, show a sample
    if data.get('data'):
        print(f"\nFirst item type: {data['data'][0].get('type')}")
        print(f"First item: {json.dumps(data['data'][0], indent=2)[:500]}...")
else:
    print(f"Error: {response.text[:500]}")

# Also try without the 'live' parameter
print("\n" + "="*80)
print("Testing without 'live' parameter...")
params_no_live = params.copy()
response2 = requests.get(url, params=params_no_live, headers=headers)
if response2.status_code == 200:
    data2 = response2.json()
    print(f"Data count (no live): {len(data2.get('data', []))}")
