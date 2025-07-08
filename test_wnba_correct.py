import requests
import json

url = "https://api.prizepicks.com/projections"
params = {"league_id": 3, "per_page": 5}  # WNBA is ID 3!
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

response = requests.get(url, params=params, headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"WNBA (League ID 3) - Found {len(data.get('data', []))} projections")
    
    # Show some actual WNBA data
    for item in data.get('included', []):
        if item['type'] == 'new_player':
            player = item['attributes']
            print(f"\nPlayer: {player['name']}")
            print(f"Team: {player.get('team', 'N/A')}")
            print(f"Position: {player.get('position', 'N/A')}")
            break
            
    # Show a projection
    if data.get('data'):
        proj = data['data'][0]
        attrs = proj['attributes']
        print(f"\nFirst projection:")
        print(f"  Line: {attrs.get('line_score')}")
        print(f"  Description: {attrs.get('description')}")
        print(f"  Start time: {attrs.get('start_time')}")
