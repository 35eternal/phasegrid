import requests
import json
from datetime import datetime

leagues = ["NBA", "NFL", "MLB", "NHL", "WNBA", "NCAAF", "NCAAB"]
league_ids = {"NBA": 2, "NFL": 1, "MLB": 3, "NHL": 4, "WNBA": 7, "NCAAF": 5, "NCAAB": 6}

print(f"Testing PrizePicks API at {datetime.now()}")
print("-" * 50)

for league in leagues:
    response = requests.get(
        "https://api.prizepicks.com/projections",
        params={
            "league_id": league_ids[league],
            "per_page": 5,
            "single_stat": True
        },
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        count = len(data.get("data", []))
        print(f"{league}: {response.status_code} - {count} projections")
    else:
        print(f"{league}: {response.status_code} - {response.text[:100]}")
