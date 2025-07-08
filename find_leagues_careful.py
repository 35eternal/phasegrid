import requests
import time
import json

url = "https://api.prizepicks.com/projections"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# Store found leagues
found_leagues = {}

print("Scanning league IDs with careful rate limiting...")
print("-" * 80)

for league_id in range(1, 15):  # Test IDs 1-14
    time.sleep(2)  # Longer delay to avoid rate limits
    
    params = {"league_id": league_id, "per_page": 1}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Testing ID {league_id}: Status {response.status_code}", end="")
        
        if response.status_code == 200:
            data = response.json()
            data_count = len(data.get('data', []))
            
            # Find league info in included data
            league_info = None
            for item in data.get('included', []):
                if item['type'] == 'league':
                    league_info = item['attributes']
                    break
            
            if league_info:
                name = league_info.get('name', 'Unknown')
                display = league_info.get('display_name', name)
                found_leagues[league_id] = {
                    'name': name,
                    'display_name': display,
                    'active_projections': data_count
                }
                print(f" -> {display} ({name}) - {data_count} projections")
            else:
                print(f" -> {data_count} projections (no league info)")
        elif response.status_code == 429:
            print(" -> Rate limited, waiting...")
            time.sleep(5)  # Extra wait on rate limit
        else:
            print("")
            
    except Exception as e:
        print(f" -> Error: {e}")

print("\n" + "="*80)
print("SUMMARY OF FOUND LEAGUES:")
print("-"*80)
for lid, info in found_leagues.items():
    print(f"ID {lid}: {info['display_name']} - {info['active_projections']} active projections")
    if 'WNBA' in info['display_name'] or 'WNBA' in info['name']:
        print("  ^^^ WNBA FOUND! ^^^")
