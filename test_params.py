import requests
import time

base_url = "https://api.prizepicks.com/projections"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# Try different parameter names and values
test_params = [
    {"sport": "wnba"},
    {"league": "wnba"},
    {"league": "WNBA"},
    {"sport": "WNBA"},
    {"league_name": "WNBA"},
    {"filter[league]": "WNBA"},
    {"q": "WNBA"}
]

print("Testing different parameter formats for WNBA...")
print("-" * 60)

for params in test_params:
    print(f"\nTrying: {params}")
    response = requests.get(base_url, params=params, headers=headers, timeout=5)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        count = len(data.get('data', []))
        print(f"Found {count} projections")
        
        if count > 0:
            print("SUCCESS! This parameter works!")
            # Show first player
            for item in data.get('included', []):
                if item['type'] == 'new_player':
                    print(f"Sample player: {item['attributes']['name']}")
                    break
    
    time.sleep(1)  # Rate limit
