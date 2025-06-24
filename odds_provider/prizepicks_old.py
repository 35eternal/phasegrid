"""
PrizePicks WNBA Board Scraper
Fetches current lines from PrizePicks API and saves to CSV
"""
import os
import csv
import json
import requests
from datetime import datetime
from typing import List, Dict, Any


class PrizePicksScraper:
    """Scraper for PrizePicks WNBA lines"""
    
    BASE_URL = "https://api.prizepicks.com/projections"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def fetch_current_board(self, output_dir: str = "data") -> str:
        """
        Fetch current WNBA board from PrizePicks
        
        Args:
            output_dir: Directory to save CSV output
            
        Returns:
            Path to generated CSV file
        """
        try:
            # Fetch projections - adjust parameters as needed for WNBA
            params = {
                "league_id": 7,  # WNBA league ID (verify this)
                "per_page": 250,
                "single_stat": True,
                "live": True
            }
            
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            lines = self._parse_projections(data)
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename with today's date
            today = datetime.now().strftime("%Y%m%d")
            output_path = os.path.join(output_dir, f"prizepicks_lines_{today}.csv")
            
            # Write to CSV
            self._write_csv(lines, output_path)
            
            print(f"Successfully fetched {len(lines)} lines and saved to {output_path}")
            return output_path
            
        except requests.RequestException as e:
            print(f"Error fetching PrizePicks data: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    
    def _parse_projections(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse projections from API response"""
        lines = []
        
        # Handle both direct data and included relationships
        projections = data.get("data", [])
        included = data.get("included", [])
        
        # Create lookup maps for related data
        players_map = {}
        stat_types_map = {}
        
        for item in included:
            if item.get("type") == "new_player":
                players_map[item["id"]] = item["attributes"]["name"]
            elif item.get("type") == "stat_type":
                stat_types_map[item["id"]] = item["attributes"]["name"]
        
        for projection in projections:
            if projection.get("type") != "projection":
                continue
                
            attrs = projection.get("attributes", {})
            relationships = projection.get("relationships", {})
            
            # Skip if not active or missing data
            if not attrs.get("is_active", True):
                continue
            
            # Extract player and stat info
            player_id = relationships.get("new_player", {}).get("data", {}).get("id")
            stat_type_id = relationships.get("stat_type", {}).get("data", {}).get("id")
            
            player_name = players_map.get(player_id, attrs.get("player_name", "Unknown"))
            prop_type = stat_types_map.get(stat_type_id, attrs.get("stat_type", "Unknown"))
            
            line_data = {
                "player": player_name,
                "prop_type": prop_type,
                "line": attrs.get("line_score", 0),
                "over_odds": attrs.get("odds_type_over", -110),
                "under_odds": attrs.get("odds_type_under", -110),
                "start_time": attrs.get("start_time", ""),
                "game_id": attrs.get("game_id", "")
            }
            
            lines.append(line_data)
        
        return lines
    
    def _write_csv(self, lines: List[Dict[str, Any]], output_path: str):
        """Write lines to CSV file"""
        if not lines:
            print("No lines to write")
            return
        
        fieldnames = ["player", "prop_type", "line", "over_odds", "under_odds", "start_time", "game_id"]
        
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lines)


def fetch_current_board(output_dir: str = "data") -> str:
    """
    Main entry point for fetching current board
    
    Args:
        output_dir: Directory to save CSV output
        
    Returns:
        Path to generated CSV file
    """
    scraper = PrizePicksScraper()
    return scraper.fetch_current_board(output_dir)


if __name__ == "__main__":
    # Test the scraper
    fetch_current_board()