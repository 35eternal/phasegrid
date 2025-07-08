import requests
import json
import re
import time
from typing import List, Dict, Any

def debug_api_response(league="WNBA"):
    """Debug what we're getting from the PrizePicks API"""
    
    # Based on PG-106, we know the league IDs
    LEAGUE_IDS = {
        "WNBA": 3,
        "NBA": 7,
        "MLB": 2,
        "NHL": 8,
        "NFL": 9
    }
    
    league_id = LEAGUE_IDS.get(league.upper(), 3)
    
    # Try the partner API endpoint
    api_url = f"https://partner-api.prizepicks.com/projections?league_id={league_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://app.prizepicks.com",
        "Referer": "https://app.prizepicks.com/",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }
    
    print(f"[DEBUG] Fetching from: {api_url}")
    
    try:
        response = requests.get(api_url, headers=headers)
        print(f"[DEBUG] Status Code: {response.status_code}")
        print(f"[DEBUG] Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print the structure
            print(f"\n[DEBUG] Top-level keys: {list(data.keys())}")
            
            # Check data key
            if 'data' in data:
                print(f"[DEBUG] 'data' type: {type(data['data'])}")
                if isinstance(data['data'], list):
                    print(f"[DEBUG] 'data' length: {len(data['data'])}")
                    if data['data']:
                        print(f"[DEBUG] First item in 'data': {json.dumps(data['data'][0], indent=2)}")
            
            # Check included key
            if 'included' in data:
                print(f"\n[DEBUG] 'included' type: {type(data['included'])}")
                if isinstance(data['included'], list):
                    print(f"[DEBUG] 'included' length: {len(data['included'])}")
                    # Group by type
                    types = {}
                    for item in data['included']:
                        item_type = item.get('type', 'unknown')
                        types[item_type] = types.get(item_type, 0) + 1
                    print(f"[DEBUG] Types in 'included': {types}")
                    
                    # Show a sample of each type
                    shown_types = set()
                    for item in data['included'][:10]:
                        item_type = item.get('type', 'unknown')
                        if item_type not in shown_types:
                            print(f"\n[DEBUG] Sample {item_type}:")
                            print(json.dumps(item, indent=2))
                            shown_types.add(item_type)
            
            # Save full response for inspection
            with open("debug_api_response.json", "w") as f:
                json.dump(data, f, indent=2)
            print("\n[DEBUG] Full response saved to debug_api_response.json")
            
        else:
            print(f"[DEBUG] Response text: {response.text[:500]}")
            
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_response("WNBA")
