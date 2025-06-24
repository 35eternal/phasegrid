"""
Results API Client Module
Handles communication with the production Results API
"""
import os
import json
import time
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class ResultsAPIError(Exception):
    """Custom exception for Results API errors"""
    pass

class ResultsAPIClient:
    """Client for interacting with the Results API"""
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Results API client
        
        Args:
            api_url: Base URL for Results API. Defaults to RESULTS_API_URL env var
            api_key: API key for authentication. Defaults to RESULTS_API_KEY env var
        """
        self.api_url = api_url or os.environ.get('RESULTS_API_URL')
        self.api_key = api_key or os.environ.get('RESULTS_API_KEY')
        
        if not self.api_url:
            raise ValueError("No API URL provided. Set RESULTS_API_URL env var")
        if not self.api_key:
            raise ValueError("No API key provided. Set RESULTS_API_KEY env var")
        
        # Ensure URL ends with /
        if not self.api_url.endswith('/'):
            self.api_url += '/'
        
        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"Initialized Results API client for: {self.api_url}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to API with error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data as dictionary
            
        Raises:
            ResultsAPIError: On API errors
        """
        url = urljoin(self.api_url, endpoint)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204:
                return {}
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise ResultsAPIError(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            raise ResultsAPIError(error_msg) from e
        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout: {str(e)}"
            logger.error(error_msg)
            raise ResultsAPIError(error_msg) from e
        except ValueError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error(error_msg)
            raise ResultsAPIError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            raise ResultsAPIError(error_msg) from e
    
    def submit_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Submit grading results to the API
        
        Args:
            results: List of result dictionaries
            
        Returns:
            API response data
        """
        logger.info(f"Submitting {len(results)} results to API")
        
        # Validate results format
        for result in results:
            required_fields = ['player_id', 'game_date', 'score', 'grade']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                raise ValueError(f"Result missing required fields: {missing_fields}")
        
        response = self._make_request(
            'POST',
            'results/submit',
            json={'results': results}
        )
        
        logger.info(f"Successfully submitted results. Response: {response}")
        return response
    
    def get_results(self, game_date: Optional[str] = None, player_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve results from the API
        
        Args:
            game_date: Optional date filter (YYYY-MM-DD format)
            player_id: Optional player ID filter
            
        Returns:
            List of result dictionaries
        """
        params = {}
        if game_date:
            params['game_date'] = game_date
        if player_id:
            params['player_id'] = player_id
        
        logger.info(f"Fetching results with params: {params}")
        
        response = self._make_request('GET', 'results', params=params)
        results = response.get('results', [])
        
        logger.info(f"Retrieved {len(results)} results")
        return results
    
    def update_result(self, result_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing result
        
        Args:
            result_id: ID of result to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated result data
        """
        logger.info(f"Updating result {result_id} with: {updates}")
        
        response = self._make_request(
            'PUT',
            f'results/{result_id}',
            json=updates
        )
        
        logger.info(f"Successfully updated result: {response}")
        return response
    
    def delete_result(self, result_id: str) -> bool:
        """
        Delete a result
        
        Args:
            result_id: ID of result to delete
            
        Returns:
            True if successful
        """
        logger.info(f"Deleting result {result_id}")
        
        self._make_request('DELETE', f'results/{result_id}')
        
        logger.info("Successfully deleted result")
        return True
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status
        
        Returns:
            Health status data
        """
        try:
            response = self._make_request('GET', 'health')
            logger.info(f"API health check passed: {response}")
            return response
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    def batch_submit(self, results: List[Dict[str, Any]], batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        Submit results in batches to avoid overwhelming the API
        
        Args:
            results: List of all results to submit
            batch_size: Number of results per batch
            
        Returns:
            List of all API responses
        """
        responses = []
        total_batches = (len(results) + batch_size - 1) // batch_size
        
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Submitting batch {batch_num}/{total_batches} ({len(batch)} results)")
            
            try:
                response = self.submit_results(batch)
                responses.append(response)
                
                # Rate limiting - wait between batches
                if batch_num < total_batches:
                    time.sleep(0.5)
                    
            except ResultsAPIError as e:
                logger.error(f"Failed to submit batch {batch_num}: {e}")
                # Continue with other batches
                responses.append({'error': str(e), 'batch': batch_num})
        
        return responses

# Singleton instance
_client = None

def get_results_api_client() -> ResultsAPIClient:
    """Get or create singleton API client instance"""
    global _client
    if not _client:
        _client = ResultsAPIClient()
    return _client
