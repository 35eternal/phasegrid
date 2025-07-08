import requests
import json

# Test 1: Try without any auth (current behavior)
print("Test 1: No auth")
response = requests.get(
    "https://api.prizepicks.com/projections",
    params={"league_id": 7, "per_page": 10},
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
)
print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")

# Test 2: Check what the API returns
if response.status_code != 200:
    print(f"\nResponse body: {response.text[:500]}")
else:
    data = response.json()
    print(f"\nGot data! Keys: {list(data.keys())}")
    print(f"Data count: {len(data.get('data', []))}")
