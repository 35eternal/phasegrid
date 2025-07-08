import pytest
from unittest.mock import patch, MagicMock
from odds_provider.prizepicks import PrizePicksClient
import requests


class TestPrizePicksClient:
    """Test PrizePicks client functionality"""
    
    def test_init(self):
        """Test client initialization"""
        client = PrizePicksClient()
        assert client.BASE_URL == "https://api.prizepicks.com"
        assert client.WEB_URL == "https://app.prizepicks.com"
        assert client.min_request_interval == 0.5
        
    def test_league_ids(self):
        """Test league ID mapping - UPDATED with correct IDs"""
        client = PrizePicksClient()
        assert client.LEAGUE_IDS["WNBA"] == 3  # Fixed from 7
        assert client.LEAGUE_IDS["NBA"] == 7   # Fixed from 2
        assert client.LEAGUE_IDS["MLB"] == 2   # Fixed from 3
        assert client.LEAGUE_IDS["NHL"] == 8   # Fixed from 4
        assert client.LEAGUE_IDS["NFL"] == 9   # Fixed from 1
        
    @patch('requests.Session.get')
    def test_fetch_projections_success(self, mock_get):
        """Test successful API fetch"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"type": "projection", "id": "123"}],
            "included": []
        }
        mock_get.return_value = mock_response
        
        client = PrizePicksClient()
        result = client.fetch_projections("WNBA")
        
        assert "data" in result
        assert len(result["data"]) == 1
        
    @patch('requests.Session.get')
    def test_rate_limit_retry(self, mock_get):
        """Test rate limit handling with retry"""
        # First call returns 429, second succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = requests.HTTPError(response=mock_response_429)
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": []}
        
        mock_get.side_effect = [mock_response_429, mock_response_200]
        
        client = PrizePicksClient()
        result = client.fetch_projections("WNBA")
        
        assert mock_get.call_count == 2
        assert "data" in result
        
    def test_parse_projections_empty(self):
        """Test parsing empty projections"""
        client = PrizePicksClient()
        result = client.parse_projections_to_slips({})
        assert result == []
        
        result = client.parse_projections_to_slips({"data": []})
        assert result == []
        
    @patch('odds_provider.prizepicks.PrizePicksClient.fetch_projections')
    @patch('odds_provider.prizepicks.PrizePicksClient.fetch_html_fallback')
    def test_fetch_current_board_with_fallback(self, mock_html, mock_api):
        """Test fetch with fallback to mock data"""
        # Both API and HTML return empty
        mock_api.return_value = {"data": []}
        mock_html.return_value = []
        
        client = PrizePicksClient()
        path, slips = client.fetch_current_board(league="WNBA")
        
        # Should use mock data when no real data available
        assert len(slips) == 8
        assert slips[0]["source"] == "mock"
        # Path should contain 'mock' when using mock data
        assert "prizepicks_wnba" in path.lower()
