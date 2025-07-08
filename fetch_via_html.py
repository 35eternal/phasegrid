import logging
import requests
import json
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def fetch_via_html(league="WNBA"):
    """Enhanced HTML scraping for PrizePicks projections."""
    
    # Based on PG-106, we know the league IDs
    LEAGUE_IDS = {
        "WNBA": 3,
        "NBA": 7,
        "MLB": 2,
        "NHL": 8,
        "NFL": 9
    }
    
    league_id = LEAGUE_IDS.get(league.upper(), 3)
    
    # Try the partner API endpoint directly
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
    
    logger.info(f"[fetch_via_html] Attempting HTML scrape for {league} (using API endpoint)")
    
    try:
        # Add delay to avoid rate limiting
        time.sleep(0.5)
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Process using the same logic as the existing code
            slips = []
            
            # Build lookup maps from included data
            players_map = {}
            stat_types_map = {}
            games_map = {}
            teams_map = {}
            
            for item in data.get("included", []):
                if item["type"] == "new_player":
                    players_map[item["id"]] = {
                        "name": item["attributes"]["name"],
                        "team": item["attributes"].get("team", ""),
                        "position": item["attributes"].get("position", "")
                    }
                elif item["type"] == "stat_type":
                    stat_types_map[item["id"]] = item["attributes"]["name"]
                elif item["type"] == "game":
                    games_map[item["id"]] = {
                        "start_time": item["attributes"]["start_time"],
                        "away_team": item["relationships"]["away_team_data"]["data"]["id"],
                        "home_team": item["relationships"]["home_team_data"]["data"]["id"]
                    }
                elif item["type"] == "team":
                    teams_map[item["id"]] = item["attributes"]["abbreviation"]
            
            # Process projections
            for projection in data.get("data", []):
                if projection["type"] != "projection":
                    continue
                
                attrs = projection["attributes"]
                relationships = projection["relationships"]
                
                # Skip if not active
                if attrs.get("status") != "pre_game":
                    continue
                
                # Get player info
                player_id = relationships["new_player"]["data"]["id"]
                player_info = players_map.get(player_id, {})
                
                # Get stat type
                stat_type_id = relationships["stat_type"]["data"]["id"]
                stat_type = stat_types_map.get(stat_type_id, attrs.get("stat_type", "Unknown"))
                
                # Get game info
                game_id = relationships["game"]["data"]["id"]
                game_info = games_map.get(game_id, {})
                
                # Determine opponent
                player_team = player_info.get("team", "")
                opponent = ""
                if game_info:
                    away_team_id = game_info.get("away_team")
                    home_team_id = game_info.get("home_team")
                    away_team = teams_map.get(away_team_id, "")
                    home_team = teams_map.get(home_team_id, "")
                    
                    if player_team == away_team:
                        opponent = f"@ {home_team}"
                    else:
                        opponent = f"vs {away_team}"
                
                # Create slip in expected format
                slip = {
                    "player_name": player_info.get("name", "Unknown"),
                    "player_team": player_team,
                    "player_position": player_info.get("position", ""),
                    "stat_type": stat_type,
                    "line_score": float(attrs.get("line_score", 0)),
                    "start_time": attrs.get("start_time", ""),
                    "opponent": opponent,
                    "league": league,
                    "is_promo": attrs.get("is_promo", False),
                    "projection_id": projection["id"]
                }
                
                slips.append(slip)
            
            logger.info(f"[fetch_via_html] Successfully fetched {len(slips)} projections")
            return slips
            
        elif response.status_code == 403:
            logger.warning(f"[fetch_via_html] Got 403 Forbidden. Cloudflare protection likely active.")
            return []
        else:
            logger.warning(f"[fetch_via_html] API returned status {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"[fetch_via_html] Error: {e}")
        return []


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Test the function
    projections = fetch_via_html("WNBA")
    print(f"\nTotal projections fetched: {len(projections)}")
    
    if projections:
        print("\nFirst 3 projections:")
        for i, proj in enumerate(projections[:3]):
            print(f"\n{i+1}. {proj['player_name']} ({proj['player_team']}) {proj['opponent']}")
            print(f"   {proj['stat_type']}: {proj['line_score']}")
            print(f"   Start: {proj['start_time']}")
