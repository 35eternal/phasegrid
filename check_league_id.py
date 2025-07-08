import requests
import json

url = "https://api.prizepicks.com/projections"
params = {"league_id": 2, "per_page": 3}  # What we think is NBA
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

response = requests.get(url, params=params, headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"League ID 2 has {len(data.get('data', []))} projections")
    
    # Check what sport this actually is
    for item in data.get('included', []):
        if item['type'] == 'league':
            print(f"League name: {item['attributes']['name']}")
            print(f"League display name: {item['attributes'].get('display_name', 'N/A')}")
            
        if item['type'] == 'new_player':
            print(f"Sample player: {item['attributes']['name']} - {item['attributes'].get('team', 'N/A')}")
            break
            
    # Show a sample projection to identify the sport
    if data.get('data'):
        print(f"\nFirst projection:")
        print(json.dumps(data['data'][0], indent=2)[:500])
