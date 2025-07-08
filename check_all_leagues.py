import requests
import time
from datetime import datetime

base_url = "https://api.prizepicks.com/projections"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

leagues = {
    "NBA": 2,
    "NFL": 1, 
    "MLB": 3,
    "NHL": 4,
    "WNBA": 7,
    "NCAAF": 5,
    "NCAAB": 6
}

print(f"Checking all leagues at {datetime.now()}")
print("-" * 60)

for league_name, league_id in leagues.items():
    # Add delay to avoid rate limiting
    time.sleep(1)
    
    params = {"league_id": league_id, "per_page": 5}
    response = requests.get(base_url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        count = len(data.get('data', []))
        print(f"{league_name} (ID {league_id}): {count} projections")
        
        # If we found data, show what sport is actually active
        if count > 0 and 'included' in data:
            for item in data['included']:
                if item.get('type') == 'league':
                    print(f"  -> Active: {item['attributes'].get('name', 'Unknown')}")
                    break
    else:
        print(f"{league_name} (ID {league_id}): Error {response.status_code}")
