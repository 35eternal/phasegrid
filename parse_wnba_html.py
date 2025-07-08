import requests
from bs4 import BeautifulSoup
import re
import json

url = "https://app.prizepicks.com/projections/wnba"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

print(f"Fetching: {url}")
response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for __INITIAL_STATE__
    found_state = False
    for script in soup.find_all('script'):
        if script.string and 'window.__INITIAL_STATE__' in script.string:
            print("Found __INITIAL_STATE__!")
            
            # Try to extract it
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
            if match:
                try:
                    state_data = json.loads(match.group(1))
                    print(f"Successfully parsed state data!")
                    
                    # Look for projections
                    def find_projections(obj, path=""):
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                if k in ['projections', 'props', 'lines', 'players']:
                                    print(f"Found key '{k}' at path: {path}.{k}")
                                    if isinstance(v, list) and len(v) > 0:
                                        print(f"  -> Contains {len(v)} items")
                                        print(f"  -> Sample: {str(v[0])[:100]}...")
                                    elif isinstance(v, dict) and len(v) > 0:
                                        print(f"  -> Contains {len(v)} keys")
                                find_projections(v, f"{path}.{k}")
                        elif isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
                            find_projections(obj[0], f"{path}[0]")
                    
                    find_projections(state_data)
                    found_state = True
                    
                    # Save the state for analysis
                    with open('wnba_state.json', 'w') as f:
                        json.dump(state_data, f, indent=2)
                    print("\nSaved state data to wnba_state.json")
                    
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
            else:
                print("Could not extract __INITIAL_STATE__")
    
    if not found_state:
        print("No __INITIAL_STATE__ found in page")
        
    # Look for any player/projection elements
    player_elements = soup.find_all(class_=re.compile(r'player|projection|prop', re.I))
    if player_elements:
        print(f"\nFound {len(player_elements)} potential player/projection elements")
        for i, elem in enumerate(player_elements[:3]):
            print(f"Element {i}: {elem.get('class')} - {elem.get_text()[:50]}...")
