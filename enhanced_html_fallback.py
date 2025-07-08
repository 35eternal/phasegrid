import re
import json
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any

def enhanced_fetch_html_fallback(self, league: str = "NBA") -> List[Dict[str, Any]]:
    """
    Enhanced HTML fallback that actually fetches projections from the API endpoint
    
    Args:
        league: Sport league (NBA, NFL, etc.)
        
    Returns:
        List of projections in slip format
    """
    logger.warning(f"Using enhanced HTML fallback for {league} projections")
    
    # Get league ID
    league_id = self.LEAGUE_IDS.get(league.upper())
    if not league_id:
        logger.error(f"Unknown league: {league}")
        return []
    
    # Try the partner API endpoint directly (discovered during HTML analysis)
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
    
    try:
        # Add delay to avoid rate limiting
        self._rate_limit()
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Use the existing parse_projections_to_slips method
            slips = self.parse_projections_to_slips(data)
            
            logger.info(f"Enhanced HTML fallback successfully fetched {len(slips)} projections")
            return slips
            
        elif response.status_code == 403:
            logger.warning("Got 403 Forbidden. Trying BeautifulSoup scraping...")
            # Fall back to the original HTML scraping method
            return self._original_html_fallback(league)
        else:
            logger.warning(f"API returned status {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Enhanced HTML fallback failed: {e}")
        # Try the original HTML scraping as last resort
        try:
            return self._original_html_fallback(league)
        except Exception as e2:
            logger.error(f"Original HTML fallback also failed: {e2}")
            return []

def _original_html_fallback(self, league: str) -> List[Dict[str, Any]]:
    """Keep the original HTML scraping as backup"""
    # This would contain the original fetch_html_fallback code
    # for BeautifulSoup-based scraping
    logger.info("Using BeautifulSoup-based HTML scraping...")
    
    self._rate_limit()
    
    league_paths = {
        "NBA": "nba",
        "NFL": "nfl", 
        "MLB": "mlb",
        "NHL": "nhl",
        "WNBA": "wnba",
        "NCAAF": "ncaaf",
        "NCAAB": "ncaab"
    }
    
    league_path = league_paths.get(league.upper(), "nba")
    url = f"{self.WEB_URL}/{league_path}"
    
    try:
        response = self.session.get(url, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch HTML: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Rest of the original HTML parsing logic...
        # (keeping it as fallback in case the API approach fails)
        
        return []  # Placeholder
        
    except Exception as e:
        logger.error(f"BeautifulSoup HTML fallback failed: {e}")
        return []
