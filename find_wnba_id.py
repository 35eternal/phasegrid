import requests
import time

url = "https://api.prizepicks.com/projections"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

print("Scanning all league IDs to find WNBA...")
print("-" * 60)

for league_id in range(1, 20):  # Test IDs 1-19
    time.sleep(0.5)  # Rate limit
    
    params = {"league_id": league_id, "per_page": 1}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('included'):
                for item in data['included']:
                    if item['type'] == 'league':
                        league_name = item['attributes'].get('name', 'Unknown')
                        display_name = item['attributes'].get('display_name', league_name)
                        print(f"ID {league_id}: {display_name} ({league_name})")
                        
                        # If we found WNBA, show more details
                        if 'WNBA' in display_name or 'WNBA' in league_name:
                            print(f"  -> FOUND WNBA! Data count: {len(data.get('data', []))}")
                        break
        elif response.status_code != 429:
            # Only print non-rate-limit errors
            pass
    except Exception as e:
        pass
