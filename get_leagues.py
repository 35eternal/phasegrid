import requests
import json

url = "https://api.prizepicks.com/leagues"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://app.prizepicks.com/"
}

print("Trying leagues endpoint after delay...")
response = requests.get(url, headers=headers, timeout=10)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Response type: {type(data)}")
    
    # If it's a list of leagues
    if isinstance(data, list):
        print(f"\nFound {len(data)} leagues:")
        for league in data:
            if isinstance(league, dict):
                print(f"  - {league.get('name', 'Unknown')} (ID: {league.get('id', '?')})")
    
    # If it's a dict with data key
    elif isinstance(data, dict) and 'data' in data:
        print(f"\nFound {len(data['data'])} leagues:")
        for league in data['data']:
            attrs = league.get('attributes', {})
            print(f"  - {attrs.get('name', 'Unknown')} (ID: {league.get('id', '?')})")
            
    # Save for analysis
    with open('leagues_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("\nSaved full response to leagues_response.json")
else:
    print(f"Response: {response.text[:200]}")
