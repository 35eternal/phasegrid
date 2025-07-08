import requests
import json

# Try to find a leagues endpoint
endpoints = [
    "https://api.prizepicks.com/leagues",
    "https://api.prizepicks.com/sports",
    "https://api.prizepicks.com/leagues/all",
    "https://api.prizepicks.com/config"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

for endpoint in endpoints:
    print(f"Trying: {endpoint}")
    try:
        response = requests.get(endpoint, headers=headers, timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response type: {type(data)}")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:5]}...")
            elif isinstance(data, list) and len(data) > 0:
                print(f"  List with {len(data)} items")
                print(f"  First item: {json.dumps(data[0], indent=2)[:200]}...")
    except Exception as e:
        print(f"  Error: {type(e).__name__}")
    print()
