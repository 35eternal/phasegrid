import requests

urls = [
    "https://prizepicks.com/projections/wnba",
    "https://app.prizepicks.com/projections/wnba", 
    "https://prizepicks.com/wnba",
    "https://api.prizepicks.com/projections"
]

for url in urls:
    try:
        resp = requests.head(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        print(f"{url} - Status: {resp.status_code}")
    except Exception as e:
        print(f"{url} - Error: {e}")
