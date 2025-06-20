#!/usr/bin/env python3
"""
PrizePicks API-Based Scraper
Avoids browser automation detection by using direct API calls
"""

import json
import csv
from datetime import datetime
from pathlib import Path
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_prizepicks_props():
    """Fetch WNBA props using PrizePicks API"""
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    # PrizePicks API endpoints (discovered through network inspection)
    api_endpoints = [
        "https://api.prizepicks.com/projections",
        "https://projections.prizepicks.com/projections/wnba",
        "https://api.prizepicks.com/projections?league_id=3",  # 3 is WNBA
        "https://partner-api.prizepicks.com/projections"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://app.prizepicks.com/',
        'Origin': 'https://app.prizepicks.com'
    }
    
    props = []
    
    with httpx.Client() as client:
        for endpoint in api_endpoints:
            try:
                logger.info(f"Trying endpoint: {endpoint}")
                response = client.get(endpoint, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Success! Got response from {endpoint}")
                    
                    # Parse the response (structure varies by endpoint)
                    if isinstance(data, dict):
                        # Look for projections in various places
                        projections = (
                            data.get('data', []) or 
                            data.get('projections', []) or 
                            data.get('included', []) or
                            []
                        )
                    elif isinstance(data, list):
                        projections = data
                    else:
                        projections = []
                    
                    # Extract props
                    for proj in projections:
                        try:
                            # Common patterns in PrizePicks API
                            prop = {
                                "player_name": (
                                    proj.get('player_name') or 
                                    proj.get('name') or
                                    proj.get('attributes', {}).get('player_name', 'Unknown')
                                ),
                                "team_name": (
                                    proj.get('team') or
                                    proj.get('team_name') or
                                    proj.get('attributes', {}).get('team', 'Unknown')
                                ),
                                "stat_type": (
                                    proj.get('stat_type') or
                                    proj.get('projection_type') or
                                    proj.get('attributes', {}).get('stat_type', 'Unknown')
                                ),
                                "line": float(
                                    proj.get('line') or
                                    proj.get('projection') or
                                    proj.get('attributes', {}).get('line', 0)
                                ),
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            # Only add if it's WNBA (check league or other indicators)
                            if (proj.get('league') == 'WNBA' or 
                                proj.get('league_id') == 3 or
                                'wnba' in str(proj).lower()):
                                props.append(prop)
                                
                        except Exception as e:
                            logger.debug(f"Error parsing projection: {e}")
                            continue
                    
                    if props:
                        break  # Found data, no need to try other endpoints
                        
                else:
                    logger.warning(f"Got {response.status_code} from {endpoint}")
                    
            except Exception as e:
                logger.error(f"Error with {endpoint}: {e}")
                continue
    
    # If no API data, try scraping the initial page load data
    if not props:
        logger.info("Trying to extract from initial page data...")
        try:
            response = httpx.get("https://app.prizepicks.com/wnba", headers=headers)
            content = response.text
            
            # Look for JSON data in script tags
            import re
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'<script[^>]*>self\.__next_f\.push\(\[.*?"({.*?})"\]\)</script>',
                r'"projections":\s*(\[.*?\])',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    try:
                        data = json.loads(matches[0])
                        logger.info("Found embedded JSON data")
                        # Parse it similar to API response
                        break
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"Error extracting page data: {e}")
    
    # Save results
    if props:
        # JSON
        json_path = data_dir / "wnba_prizepicks_props.json"
        with open(json_path, 'w') as f:
            json.dump(props, f, indent=2)
            
        # CSV
        csv_path = data_dir / "wnba_prizepicks_props.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["player_name", "team_name", "stat_type", "line", "timestamp"])
            writer.writeheader()
            writer.writerows(props)
            
        print(f"\n✅ Saved {len(props)} WNBA props!")
        print(f"  JSON: {json_path}")
        print(f"  CSV: {csv_path}")
        
        # Show sample
        print("\nSample props:")
        for prop in props[:3]:
            print(f"  {prop['player_name']} - {prop['stat_type']}: {prop['line']}")
    else:
        print("\n⚠ No props found via API.")
        print("PrizePicks may have changed their API or there may be no WNBA games today.")
        print("\nCheck your existing data files:")
        print("  - data/wnba_prizepicks_props.csv")
        print("  - data/prizepicks_wnba_props.csv")


if __name__ == "__main__":
    fetch_prizepicks_props()