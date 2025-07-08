import requests
import json
import re
from bs4 import BeautifulSoup

def test_fetch_prizepicks_html():
    """Test fetching and parsing PrizePicks HTML"""
    url = "https://app.prizepicks.com/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        # Look for __INITIAL_STATE__ in the HTML
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', response.text, re.DOTALL)
        if match:
            print("Found __INITIAL_STATE__!")
            state_json = match.group(1)
            # Parse the JSON
            try:
                state_data = json.loads(state_json)
                print(f"Parsed JSON with keys: {list(state_data.keys())[:5]}...")
                # Look for projections
                if 'projections' in state_data:
                    print(f"Found {len(state_data['projections'])} projections")
                else:
                    print("No 'projections' key found. Searching nested structure...")
                    # Print structure to understand where projections might be
                    for key in state_data:
                        print(f"  - {key}: {type(state_data[key])}")
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
        else:
            print("No __INITIAL_STATE__ found in HTML")
            # Save HTML for inspection
            with open("prizepicks_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Saved HTML to prizepicks_page.html for inspection")
    else:
        print(f"Failed with status {response.status_code}")
        print(f"Response headers: {response.headers}")

if __name__ == "__main__":
    test_fetch_prizepicks_html()
