"""
Debug ESPN API Response Structure
Helps understand how ESPN returns WNBA player statistics
"""

import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_espn_game_response():
    """Debug what ESPN actually returns for a WNBA game"""
    
    # Test with a specific game ID from the logs
    game_id = "401736112"  # First game: ATL @ WSH
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba"
    
    # Try different ESPN endpoints
    endpoints_to_test = [
        f"{base_url}/summary?event={game_id}",
        f"{base_url}/boxscore?event={game_id}",
        f"{base_url}/gamecast?event={game_id}",
        f"{base_url}/playbyplay?event={game_id}"
    ]
    
    for endpoint in endpoints_to_test:
        logger.info(f"\n=== TESTING ENDPOINT: {endpoint} ===")
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Save full response to file for inspection
                endpoint_name = endpoint.split('/')[-1].split('?')[0]
                filename = f"debug_{endpoint_name}_{game_id}.json"
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.info(f"✅ Success! Saved response to {filename}")
                
                # Print key structure
                logger.info("Top-level keys:")
                if isinstance(data, dict):
                    for key in data.keys():
                        logger.info(f"  - {key}")
                        
                    # Look for boxscore/statistics
                    if 'boxscore' in data:
                        logger.info("\nBoxscore structure:")
                        boxscore = data['boxscore']
                        if isinstance(boxscore, dict):
                            for key in boxscore.keys():
                                logger.info(f"  boxscore.{key}")
                                
                    # Look for competitions
                    if 'header' in data and 'competitions' in data['header']:
                        comp = data['header']['competitions'][0]
                        if 'competitors' in comp:
                            logger.info(f"\nFound {len(comp['competitors'])} competitors")
                            for i, competitor in enumerate(comp['competitors']):
                                if 'statistics' in competitor:
                                    logger.info(f"  Competitor {i} has statistics")
                                if 'roster' in competitor:
                                    logger.info(f"  Competitor {i} has roster")
                
            else:
                logger.error(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Exception: {str(e)}")

def check_alternative_endpoints():
    """Check alternative ESPN endpoints that might have player stats"""
    
    game_id = "401736112"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Alternative endpoints to try
    alternatives = [
        f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/wnba/events/{game_id}/competitions/{game_id}/competitors",
        f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/wnba/events/{game_id}",
        f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/wnba/statistics/byevent?event={game_id}",
        f"https://site.api.espn.com/apis/v2/sports/basketball/wnba/events/{game_id}"
    ]
    
    logger.info("\n=== TESTING ALTERNATIVE ENDPOINTS ===")
    
    for endpoint in alternatives:
        logger.info(f"\nTesting: {endpoint}")
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=30)
            logger.info(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Success!")
                
                # Save response
                filename = f"debug_alt_{hash(endpoint) % 10000}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Saved to {filename}")
                
        except Exception as e:
            logger.error(f"Exception: {str(e)}")

if __name__ == "__main__":
    print("🔍 Debugging ESPN API responses for WNBA game data...")
    debug_espn_game_response()
    check_alternative_endpoints()
    print("🔍 Debug complete! Check the generated JSON files.")