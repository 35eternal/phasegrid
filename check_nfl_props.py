import requests
import json
from datetime import datetime

url = "https://api.prizepicks.com/projections"
params = {"league_id": 9, "per_page": 2}  # NFL supposedly
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

response = requests.get(url, params=params, headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"'NFL' League (ID 9) - Total projections: {len(data.get('data', []))}")
    
    # Look at the actual projections
    for i, proj in enumerate(data.get('data', [])[:2]):
        attrs = proj.get('attributes', {})
        print(f"\nProjection {i+1}:")
        print(f"  Line: {attrs.get('line_score')}")
        print(f"  Description: {attrs.get('description')}")
        print(f"  Start time: {attrs.get('start_time')}")
        print(f"  Stat type ID: {proj.get('relationships', {}).get('stat_type', {}).get('data', {}).get('id')}")
        
    # Check included data for more context
    print("\nChecking included data for context...")
    for item in data.get('included', []):
        if item['type'] == 'game':
            print(f"Game: {item['attributes'].get('name')} - {item['attributes'].get('start_time')}")
        elif item['type'] == 'stat_type':
            print(f"Stat type: {item['attributes'].get('name')}")
