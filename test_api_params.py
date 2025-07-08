import requests
from datetime import datetime

base_url = "https://api.prizepicks.com/projections"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# Different parameter combinations to try
test_params = [
    {"league_id": 7},  # Minimal
    {"league_id": 7, "per_page": 10},  # Small page
    {"league_id": 7, "single_stat": True},  # Single stat only
    {"league_id": 7, "include": "stat_type,new_player"},  # Different includes
    {"league_id": 7, "is_live": False},  # Explicitly not live
    {"league_id": 7, "date": datetime.now().strftime("%Y-%m-%d")},  # Today's date
]

for i, params in enumerate(test_params):
    print(f"\nTest {i+1}: {params}")
    response = requests.get(base_url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"  Status: 200 OK")
        print(f"  Data count: {len(data.get('data', []))}")
        if data.get('data'):
            print(f"  First item: {data['data'][0].get('type', 'unknown')}")
    else:
        print(f"  Status: {response.status_code}")
