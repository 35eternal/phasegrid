"""
PrizePicks API Client with Authentication and Retry Logic
Enhanced version with real API integration and error handling
"""
import os
import csv
import json
import time
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def exponential_backoff_retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for exponential backoff with jitter"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, requests.Timeout) as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = delay * 0.1 * (0.5 - time.time() % 1)  # Add 10% jitter
                    actual_delay = delay + jitter
                    
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {actual_delay:.2f}s: {str(e)}")
                    time.sleep(actual_delay)
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class PrizePicksClient:
    """Production-ready PrizePicks API Client with authentication"""
    
    BASE_URL = "https://api.prizepicks.com"
    PROJECTIONS_ENDPOINT = "/projections"
    
    # Sport league IDs
    LEAGUE_IDS = {
        "NBA": 2,
        "NFL": 1,
        "MLB": 3,
        "NHL": 4,
        "WNBA": 7,
        "NCAAF": 5,
        "NCAAB": 6
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with optional API key for authenticated requests"""
        self.session = requests.Session()
        self.api_key = api_key or os.getenv('PRIZEPICKS_API_KEY')
        
        # Set up headers
        self.session.headers.update({
            "User-Agent": "PhaseGrid/1.0",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json"
        })
        
        # Add authentication if available
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
            logger.info("PrizePicks client initialized with authentication")
        else:
            logger.warning("PrizePicks client initialized without authentication - rate limits may apply")
    
    @exponential_backoff_retry(max_retries=3, base_delay=1.0)
    def fetch_projections(self, league: str = "NBA", include_live: bool = True) -> Dict[str, Any]:
        """
        Fetch current projections/lines from PrizePicks
        
        Args:
            league: Sport league (NBA, NFL, etc.)
            include_live: Include live/in-play lines
            
        Returns:
            API response data
        """
        league_id = self.LEAGUE_IDS.get(league.upper())
        if not league_id:
            raise ValueError(f"Unknown league: {league}. Valid options: {list(self.LEAGUE_IDS.keys())}")
        
        params = {
            "league_id": league_id,
            "per_page": 250,
            "single_stat": True,
            "include": "stat_type,new_player,league,game"
        }
        
        if include_live:
            params["live"] = True
            
        url = f"{self.BASE_URL}{self.PROJECTIONS_ENDPOINT}"
        logger.info(f"Fetching projections from {url} with params: {params}")
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    def parse_projections_to_slips(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert API projections to slip format"""
        slips = []
        
        # Build lookup maps from included data
        players_map = {}
        stat_types_map = {}
        games_map = {}
        
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
                    "home_team": item["attributes"].get("home_team", ""),
                    "away_team": item["attributes"].get("away_team", ""),
                    "start_time": item["attributes"].get("start_time", ""),
                    "game_id": item["id"]
                }
        
        # Process projections
        for projection in data.get("data", []):
            if projection["type"] != "projection":
                continue
                
            attrs = projection["attributes"]
            relationships = projection["relationships"]
            
            # Skip inactive projections
            if not attrs.get("is_active", True):
                continue
            
            # Extract IDs
            player_id = relationships.get("new_player", {}).get("data", {}).get("id")
            stat_type_id = relationships.get("stat_type", {}).get("data", {}).get("id")
            game_id = relationships.get("game", {}).get("data", {}).get("id")
            
            # Get mapped data
            player_info = players_map.get(player_id, {})
            stat_type = stat_types_map.get(stat_type_id, "Unknown")
            game_info = games_map.get(game_id, {})
            
            # Create slip entry
            slip = {
                "slip_id": f"PP_{projection['id']}_{datetime.now().strftime('%Y%m%d')}",
                "player": player_info.get("name", "Unknown"),
                "team": player_info.get("team", ""),
                "prop_type": stat_type,
                "line": float(attrs.get("line_score", 0)),
                "projection": None,  # To be filled by model
                "pick": None,  # To be determined
                "over_odds": attrs.get("odds_type_over", -110),
                "under_odds": attrs.get("odds_type_under", -110),
                "start_time": game_info.get("start_time", attrs.get("start_time", "")),
                "game_id": game_info.get("game_id", ""),
                "home_team": game_info.get("home_team", ""),
                "away_team": game_info.get("away_team", ""),
                "source": "prizepicks",
                "fetched_at": datetime.now().isoformat(),
                "projection_id": projection["id"],
                "flash_sale": attrs.get("flash_sale", False),
                "is_promo": attrs.get("is_promo", False)
            }
            
            slips.append(slip)
        
        return slips
    
    def fetch_current_board(self, output_dir: str = "data", league: str = "NBA") -> Tuple[str, List[Dict]]:
        """
        Fetch current board and save to CSV
        
        Returns:
            Tuple of (csv_path, slips_list)
        """
        try:
            # Fetch data
            data = self.fetch_projections(league=league)
            slips = self.parse_projections_to_slips(data)
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"prizepicks_{league.lower()}_{timestamp}.csv")
            
            # Write to CSV
            if slips:
                fieldnames = list(slips[0].keys())
                with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(slips)
                
                logger.info(f"Saved {len(slips)} slips to {output_path}")
            else:
                logger.warning("No slips found to save")
            
            return output_path, slips
            
        except Exception as e:
            logger.error(f"Error fetching board: {str(e)}")
            raise


# Backward compatibility function
def fetch_current_board(output_dir: str = "data", league: str = "NBA") -> str:
    """Legacy function for backward compatibility"""
    client = PrizePicksClient()
    csv_path, _ = client.fetch_current_board(output_dir, league)
    return csv_path


if __name__ == "__main__":
    # Test the enhanced client
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch PrizePicks lines")
    parser.add_argument("--league", default="NBA", help="Sport league (NBA, NFL, etc.)")
    parser.add_argument("--output-dir", default="data", help="Output directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    client = PrizePicksClient()
    csv_path, slips = client.fetch_current_board(args.output_dir, args.league)
    print(f"\nFetched {len(slips)} slips")
    print(f"CSV saved to: {csv_path}")
    
    # Show sample
    if slips:
        print("\nSample slip:")
        print(json.dumps(slips[0], indent=2))