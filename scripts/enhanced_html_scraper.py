import requests
import json
import re
import time
from typing import List, Dict, Any

def fetch_via_html(league="WNBA"):
    """Enhanced HTML scraping for PrizePicks projections using their API directly."""
    
    # Based on PG-106, we know the league IDs
    LEAGUE_IDS = {
        "WNBA": 3,
        "NBA": 7,
        "MLB": 2,
        "NHL": 8,
        "NFL": 9
    }
    
    league_id = LEAGUE_IDS.get(league.upper(), 3)  # Default to WNBA
    
    # Try to fetch from the API endpoint we found in the HTML
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
    
    print(f"[fetch_via_html] Attempting to fetch {league} projections from API endpoint...")
    
    try:
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            projections = data.get('included', [])
            
            # Filter for projections
            player_projections = [
                item for item in projections 
                if item.get('type') == 'projection' or item.get('type') == 'new_player_projection'
            ]
            
            print(f"[fetch_via_html] Found {len(player_projections)} projections via API")
            
            # Transform to expected format
            transformed_projections = []
            for proj in player_projections:
                attrs = proj.get('attributes', {})
                transformed = {
                    'player_name': attrs.get('name', 'Unknown'),
                    'stat_type': attrs.get('stat_type', 'Unknown'),
                    'line_score': attrs.get('line_score', 0),
                    'start_time': attrs.get('start_time', ''),
                    'league': league,
                    'team': attrs.get('team', ''),
                    'opponent': attrs.get('opponent', ''),
                    'projection_id': proj.get('id', '')
                }
                transformed_projections.append(transformed)
            
            return transformed_projections
            
        elif response.status_code == 403:
            print(f"[fetch_via_html] Got 403 Forbidden. Trying alternative approach...")
            # Fall back to fetching the main page and extracting data
            return fetch_via_javascript_state(league)
        else:
            print(f"[fetch_via_html] API returned status {response.status_code}")
            return []
            
    except Exception as e:
        print(f"[fetch_via_html] Error: {e}")
        return []

def fetch_via_javascript_state(league="WNBA"):
    """Try to extract data from the JavaScript state on the main page."""
    
    url = "https://app.prizepicks.com/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    print(f"[fetch_via_javascript_state] Fetching main page...")
    
    try:
        # Add delay to avoid rate limiting
        time.sleep(0.5)
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Look for inline data in various formats
            patterns = [
                r'window\.__INITIAL_DATA__\s*=\s*({.*?});',
                r'window\.initialData\s*=\s*({.*?});',
                r'<script[^>]*>window\.prizepicks\s*=\s*({.*?});</script>',
                r'data-initial-state="([^"]*)"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text, re.DOTALL)
                if match:
                    try:
                        # Handle escaped JSON in data attributes
                        json_str = match.group(1)
                        if pattern == r'data-initial-state="([^"]*)"':
                            json_str = json_str.replace('&quot;', '"')
                        
                        data = json.loads(json_str)
                        print(f"[fetch_via_javascript_state] Found data with pattern: {pattern}")
                        
                        # Extract projections from the data structure
                        # This will vary based on how PrizePicks structures their data
                        projections = extract_projections_from_data(data, league)
                        if projections:
                            return projections
                    except json.JSONDecodeError:
                        continue
            
            print(f"[fetch_via_javascript_state] No parseable data found in HTML")
            
        else:
            print(f"[fetch_via_javascript_state] Page returned status {response.status_code}")
            
    except Exception as e:
        print(f"[fetch_via_javascript_state] Error: {e}")
    
    return []

def extract_projections_from_data(data: Dict[str, Any], league: str) -> List[Dict[str, Any]]:
    """Extract projections from various possible data structures."""
    
    projections = []
    
    # Try different possible paths where projections might be stored
    possible_paths = [
        lambda d: d.get('projections', []),
        lambda d: d.get('data', {}).get('projections', []),
        lambda d: d.get('props', {}).get('data', []),
        lambda d: d.get('initialState', {}).get('projections', []),
    ]
    
    for path_func in possible_paths:
        try:
            items = path_func(data)
            if items and isinstance(items, list):
                print(f"[extract_projections] Found {len(items)} items")
                # Transform to expected format
                for item in items:
                    if isinstance(item, dict):
                        projection = {
                            'player_name': item.get('player_name', item.get('name', 'Unknown')),
                            'stat_type': item.get('stat_type', item.get('prop_type', 'Unknown')),
                            'line_score': item.get('line_score', item.get('line', 0)),
                            'start_time': item.get('start_time', item.get('game_time', '')),
                            'league': league,
                            'team': item.get('team', ''),
                            'opponent': item.get('opponent', ''),
                            'projection_id': item.get('id', item.get('projection_id', ''))
                        }
                        projections.append(projection)
                
                if projections:
                    return projections
        except Exception:
            continue
    
    return projections

if __name__ == "__main__":
    # Test the HTML fetch
    projections = fetch_via_html("WNBA")
    print(f"\nTotal projections fetched: {len(projections)}")
    if projections:
        print("\nSample projection:")
        print(json.dumps(projections[0], indent=2))
