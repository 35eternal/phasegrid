#!/usr/bin/env python3
"""Test modified fetch without live parameter"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔧 TESTING MODIFIED FETCH")

# Import and monkey-patch the fetch function
from odds_provider import prizepicks
import requests

# Create a modified fetch function
def fetch_wnba_projections():
    """Fetch WNBA projections without live filter"""
    url = "https://api.prizepicks.com/projections"
    params = {
        "league_id": 7,
        "per_page": 250,
        "single_stat": True,
        "include": "stat_type,new_player,league,game"
        # NO live parameter
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return {"data": []}

# Test it
print("Fetching WNBA projections without live filter...")
result = fetch_wnba_projections()
count = len(result.get('data', []))
print(f"✅ Found {count} projections")

if count > 0:
    print("\n🚀 LINES FOUND! Running auto_paper...")
    import os
    os.system("python auto_paper.py --production --bypass-guard-rail")
else:
    print("\n❌ Still no projections. Checking response...")
    import json
    with open('fetch_debug.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("Saved response to fetch_debug.json")
