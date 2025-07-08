import requests

# Possible API variations
endpoints = [
    "https://api.prizepicks.com/v1/projections",
    "https://api.prizepicks.com/v2/projections", 
    "https://api.prizepicks.com/api/projections",
    "https://api.prizepicks.com/projections/wnba",
    "https://api.prizepicks.com/leagues/7/projections",
    "https://api.prizepicks.com/sports/wnba/projections"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

print("Testing alternative API endpoints...")
print("-" * 60)

for endpoint in endpoints:
    try:
        response = requests.get(endpoint, headers=headers, timeout=5)
        print(f"{endpoint}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                print(f"  Data count: {len(data['data'])}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}")
    print()
