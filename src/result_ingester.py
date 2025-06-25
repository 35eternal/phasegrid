"""
ResultIngester - Handles ingestion of betting results from various sources
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pandas as pd
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


class ResultIngester:
    """Ingests betting results from API and CSV sources."""
    
    def __init__(self):
        # API configuration from environment
        self.api_base_url = os.getenv('RESULTS_API_URL', 'https://api.prizepicks.com/v1')
        self.api_key = os.getenv('RESULTS_API_KEY', '')
        self.api_timeout = int(os.getenv('RESULTS_API_TIMEOUT', '30'))
        
        # Cache configuration
        self.cache_ttl = int(os.getenv('RESULTS_CACHE_TTL', '3600'))  # 1 hour default
        self._cache = {}
        
        # Rate limiting
        self.rate_limit_delay = float(os.getenv('API_RATE_LIMIT_DELAY', '0.5'))
        self._last_api_call = 0
        
        logger.info(f"ResultIngester initialized with API URL: {self.api_base_url}")
    
    def ingest_results(self, date: datetime) -> List[Dict[str, Any]]:
        """Ingest results for a specific date from all available sources."""
        logger.info(f"Ingesting results for {date.strftime('%Y-%m-%d')}")
        
        results = []
        
        # Try API first
        try:
            api_results = self._load_results_from_api(date)
            if api_results:
                results.extend(api_results)
                logger.info(f"Loaded {len(api_results)} results from API")
        except Exception as e:
            logger.error(f"Failed to load results from API: {e}")
        
        # Fallback to CSV if needed
        if not results:
            try:
                csv_results = self._load_results_from_csv(date)
                if csv_results:
                    results.extend(csv_results)
                    logger.info(f"Loaded {len(csv_results)} results from CSV")
            except Exception as e:
                logger.error(f"Failed to load results from CSV: {e}")
        
        # Process and validate results
        processed_results = self._process_results(results)
        
        return processed_results
    
    def _load_results_from_api(self, date: datetime) -> List[Dict[str, Any]]:
        """Load results from the PrizePicks API."""
        # Check cache first
        cache_key = f"api_results_{date.strftime('%Y%m%d')}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.debug(f"Returning cached results for {date}")
            return cached
        
        # Rate limiting
        self._apply_rate_limit()
        
        # Prepare API request
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
            'User-Agent': 'PhaseGrid/1.0'
        }
        
        # API endpoint for results
        endpoint = f"{self.api_base_url}/results"
        params = {
            'date': date.strftime('%Y-%m-%d'),
            'include_props': 'true',
            'status': 'settled'
        }
        
        try:
            response = requests.get(
                endpoint,
                headers=headers,
                params=params,
                timeout=self.api_timeout
            )
            response.raise_for_status()
            
            data = response.json()
            results = self._parse_api_response(data)
            
            # Cache the results
            self._set_cache(cache_key, results)
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            
            # If it's an auth error, log it specifically
            if hasattr(e, 'response') and e.response.status_code == 401:
                logger.error("API authentication failed. Check your API key.")
            
            raise
    
    def _parse_api_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse the API response into standardized result format."""
        results = []
        
        # Handle PrizePicks API response structure
        if 'data' in data:
            for entry in data['data']:
                try:
                    result = {
                        'player_name': entry.get('player', {}).get('name'),
                        'prop_type': entry.get('stat_type'),
                        'line': float(entry.get('line', 0)),
                        'actual': float(entry.get('score', 0)),
                        'hit': entry.get('is_over', False),
                        'game_id': entry.get('game_id'),
                        'timestamp': entry.get('updated_at'),
                        'sport': entry.get('league', 'NBA')
                    }
                    
                    # Validate required fields
                    if result['player_name'] and result['prop_type']:
                        results.append(result)
                        
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping malformed result entry: {e}")
                    continue
        
        return results
    
    def _load_results_from_csv(self, date: datetime) -> List[Dict[str, Any]]:
        """Load results from CSV file fallback."""
        date_str = date.strftime('%Y%m%d')
        csv_path = f"data/results_{date_str}.csv"
        
        if not os.path.exists(csv_path):
            logger.warning(f"No CSV results found for {date_str}")
            return []
        
        try:
            df = pd.read_csv(csv_path)
            
            # Convert DataFrame to list of dicts
            results = []
            for _, row in df.iterrows():
                result = {
                    'player_name': row.get('player_name'),
                    'prop_type': row.get('prop_type'),
                    'line': float(row.get('line', 0)),
                    'actual': float(row.get('actual', 0)),
                    'hit': bool(row.get('hit', False)),
                    'game_id': row.get('game_id'),
                    'timestamp': row.get('timestamp'),
                    'sport': row.get('sport', 'NBA')
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error reading CSV results: {e}")
            return []
    
    def _process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and validate results."""
        processed = []
        
        for result in results:
            # Validate required fields
            if not all(k in result for k in ['player_name', 'prop_type', 'line', 'actual']):
                logger.warning(f"Skipping incomplete result: {result}")
                continue
            
            # Calculate hit if not provided
            if 'hit' not in result:
                # Assuming 'over' props for now
                result['hit'] = result['actual'] > result['line']
            
            # Standardize prop types
            result['prop_type'] = self._standardize_prop_type(result['prop_type'])
            
            processed.append(result)
        
        return processed
    
    def _standardize_prop_type(self, prop_type: str) -> str:
        """Standardize prop type naming."""
        mappings = {
            'pts': 'points',
            'reb': 'rebounds',
            'ast': 'assists',
            'points': 'points',
            'rebounds': 'rebounds',
            'assists': 'assists',
            '3pm': 'three_pointers',
            'blk': 'blocks',
            'stl': 'steals',
            'to': 'turnovers'
        }
        
        return mappings.get(prop_type.lower(), prop_type.lower())
    
    def _apply_rate_limit(self):
        """Apply rate limiting between API calls."""
        current_time = time.time()
        time_since_last_call = current_time - self._last_api_call
        
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self._last_api_call = time.time()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired."""
        if key in self._cache:
            item, timestamp = self._cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return item
            else:
                # Remove expired item
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set item in cache with timestamp."""
        self._cache[key] = (value, time.time())
    
    def get_historical_results(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical results for a date range."""
        all_results = []
        current_date = start_date
        
        while current_date <= end_date:
            try:
                daily_results = self.ingest_results(current_date)
                for result in daily_results:
                    result['date'] = current_date
                    all_results.append(result)
            except Exception as e:
                logger.error(f"Failed to get results for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        # Convert to DataFrame for easier analysis
        if all_results:
            return pd.DataFrame(all_results)
        else:
            return pd.DataFrame()
    
    def validate_api_connection(self) -> bool:
        """Test the API connection and authentication."""
        try:
            # Try to fetch yesterday's results as a test
            test_date = datetime.now() - timedelta(days=1)
            results = self._load_results_from_api(test_date)
            
            if results:
                logger.info("API connection validated successfully")
                return True
            else:
                logger.warning("API connection successful but no results returned")
                return True
                
        except Exception as e:
            logger.error(f"API connection validation failed: {e}")
            return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize ingester
    ingester = ResultIngester()
    
    # Test API connection
    if ingester.validate_api_connection():
        print("✓ API connection validated")
    else:
        print("✗ API connection failed")
    
    # Ingest today's results
    today = datetime.now()
    results = ingester.ingest_results(today)
    
    print(f"\nIngested {len(results)} results for {today.strftime('%Y-%m-%d')}")
    
    # Show sample results
    if results:
        print("\nSample results:")
        for result in results[:5]:
            print(f"- {result['player_name']} {result['prop_type']}: "
                  f"{result['actual']} vs {result['line']} ({'HIT' if result['hit'] else 'MISS'})")
