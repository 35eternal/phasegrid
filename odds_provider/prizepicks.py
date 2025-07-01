"""
PrizePicks API Client with Authentication and Retry Logic
Enhanced version with real API integration and HTML fallback
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
import re
from bs4 import BeautifulSoup

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
    """Production-ready PrizePicks API Client with authentication and HTML fallback"""

    BASE_URL = "https://api.prizepicks.com"
    WEB_URL = "https://prizepicks.com"
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
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

    def fetch_html_fallback(self, league: str = "NBA") -> List[Dict[str, Any]]:
        """
        Fallback method to scrape projections from PrizePicks website HTML
        
        Args:
            league: Sport league (NBA, NFL, etc.)
            
        Returns:
            List of scraped projections
        """
        logger.warning(f"Using HTML fallback for {league} projections")
        
        # Map league to URL path
        league_paths = {
            "NBA": "nba",
            "NFL": "nfl", 
            "MLB": "mlb",
            "NHL": "nhl",
            "WNBA": "wnba",
            "NCAAF": "cfb",
            "NCAAB": "cbb"
        }
        
        league_path = league_paths.get(league.upper(), "nba")
        url = f"{self.WEB_URL}/projections/{league_path}"
        
        try:
            # Fetch the page
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for script tags containing projection data
            projections = []
            
            # Try to find JSON data in script tags
            for script in soup.find_all('script'):
                if script.string and 'window.__INITIAL_STATE__' in script.string:
                    # Extract JSON from the script
                    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            # Extract projections from the state
                            projections = self._extract_projections_from_state(data)
                            if projections:
                                logger.info(f"Successfully extracted {len(projections)} projections from HTML")
                                return projections
                        except json.JSONDecodeError:
                            logger.error("Failed to parse JSON from HTML")
            
            # Fallback: Try to scrape visible projection cards
            projection_cards = soup.find_all('div', class_=re.compile(r'projection-card|player-projection'))
            
            for card in projection_cards:
                try:
                    projection = self._parse_projection_card(card)
                    if projection:
                        projections.append(projection)
                except Exception as e:
                    logger.warning(f"Failed to parse projection card: {e}")
            
            logger.info(f"Scraped {len(projections)} projections from HTML")
            return projections
            
        except Exception as e:
            logger.error(f"HTML fallback failed: {e}")
            return []

    def _extract_projections_from_state(self, state_data: Dict) -> List[Dict[str, Any]]:
        """Extract projections from the React state data"""
        projections = []
        
        # Navigate through the state structure (this varies by site version)
        try:
            # Common paths where projections might be stored
            paths = [
                ['projections', 'data'],
                ['api', 'projections', 'data'],
                ['leagues', 'current', 'projections'],
                ['props', 'projections']
            ]
            
            for path in paths:
                data = state_data
                for key in path:
                    if isinstance(data, dict) and key in data:
                        data = data[key]
                    else:
                        break
                else:
                    # Found projections data
                    if isinstance(data, list):
                        return self._parse_state_projections(data)
                    elif isinstance(data, dict):
                        return self._parse_state_projections(list(data.values()))
                        
        except Exception as e:
            logger.warning(f"Failed to extract projections from state: {e}")
            
        return projections

    def _parse_state_projections(self, projections_data: List) -> List[Dict[str, Any]]:
        """Parse projections from state data format"""
        slips = []
        
        for proj in projections_data:
            try:
                slip = {
                    "slip_id": f"PP_HTML_{proj.get('id', '')}_{datetime.now().strftime('%Y%m%d')}",
                    "player": proj.get('player_name', '') or proj.get('new_player', {}).get('name', 'Unknown'),
                    "team": proj.get('team', '') or proj.get('new_player', {}).get('team', ''),
                    "prop_type": proj.get('stat_type', '') or proj.get('market', ''),
                    "line": float(proj.get('line', 0) or proj.get('line_score', 0)),
                    "projection": None,
                    "pick": None,
                    "over_odds": int(proj.get('over_odds', -110) or -110),
                    "under_odds": int(proj.get('under_odds', -110) or -110),
                    "start_time": proj.get('start_time', ''),
                    "game_id": proj.get('game_id', ''),
                    "source": "prizepicks_html",
                    "fetched_at": datetime.now().isoformat(),
                    "projection_id": proj.get('id', ''),
                    "flash_sale": proj.get('flash_sale', False),
                    "is_promo": proj.get('is_promo', False)
                }
                
                if slip['player'] != 'Unknown' and slip['line'] > 0:
                    slips.append(slip)
                    
            except Exception as e:
                logger.warning(f"Failed to parse projection: {e}")
                
        return slips

    def _parse_projection_card(self, card_element) -> Optional[Dict[str, Any]]:
        """Parse a single projection card from HTML"""
        try:
            # This is a simplified parser - actual implementation would need to match current HTML structure
            player_name = card_element.find(class_=re.compile(r'player-name'))
            stat_type = card_element.find(class_=re.compile(r'stat-type|market-type'))
            line_value = card_element.find(class_=re.compile(r'line-value|projection-value'))
            
            if player_name and stat_type and line_value:
                return {
                    "slip_id": f"PP_HTML_CARD_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "player": player_name.get_text(strip=True),
                    "team": "",  # Would need to extract from card
                    "prop_type": stat_type.get_text(strip=True),
                    "line": float(re.search(r'[\d.]+', line_value.get_text()).group()),
                    "projection": None,
                    "pick": None,
                    "over_odds": -110,
                    "under_odds": -110,
                    "source": "prizepicks_html_card",
                    "fetched_at": datetime.now().isoformat()
                }
        except Exception as e:
            logger.warning(f"Failed to parse card element: {e}")
            
        return None

    def parse_projections_to_slips(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert API projections to slip format"""
        # Check if we got an empty response
        if not data or not data.get("data"):
            logger.warning("Empty or invalid API response, will use HTML fallback")
            return []
            
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
        Fetch current board and save to CSV, with HTML fallback if API fails
        
        Returns:
            Tuple of (csv_path, slips_list)
        """
        slips = []
        
        try:
            # Try API first
            data = self.fetch_projections(league=league)
            slips = self.parse_projections_to_slips(data)
            
            # Check if we got valid data
            if not slips:
                logger.warning("API returned no projections, trying HTML fallback")
                slips = self.fetch_html_fallback(league=league)
                
        except Exception as api_error:
            logger.error(f"API fetch failed: {api_error}, trying HTML fallback")
            
            # Try HTML fallback
            try:
                slips = self.fetch_html_fallback(league=league)
            except Exception as html_error:
                logger.error(f"Both API and HTML methods failed: {html_error}")
                raise Exception(f"Failed to fetch projections via API or HTML: API error: {api_error}, HTML error: {html_error}")

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
            logger.warning("No slips found to save from either API or HTML")

        return output_path, slips


# Backward compatibility function
def fetch_current_board(output_dir: str = "data", league: str = "NBA") -> str:
    """Legacy function for backward compatibility"""
    client = PrizePicksClient()
    csv_path, _ = client.fetch_current_board(output_dir, league)
    return csv_path


if __name__ == "__main__":
    # Test the enhanced client with fallback
    import argparse

    parser = argparse.ArgumentParser(description="Fetch PrizePicks lines")
    parser.add_argument("--league", default="NBA", help="Sport league (NBA, NFL, etc.)")
    parser.add_argument("--output-dir", default="data", help="Output directory")
    parser.add_argument("--test-html", action="store_true", help="Test HTML fallback")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    client = PrizePicksClient()
    
    if args.test_html:
        # Test HTML fallback directly
        slips = client.fetch_html_fallback(args.league)
        print(f"\nHTML Fallback: Fetched {len(slips)} slips")
        if slips:
            print("\nSample HTML slip:")
            print(json.dumps(slips[0], indent=2))
    else:
        # Normal operation with automatic fallback
        csv_path, slips = client.fetch_current_board(args.output_dir, args.league)
        print(f"\nFetched {len(slips)} slips")
        print(f"CSV saved to: {csv_path}")

        # Show sample
        if slips:
            print("\nSample slip:")
            print(json.dumps(slips[0], indent=2))