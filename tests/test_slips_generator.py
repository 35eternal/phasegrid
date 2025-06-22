#!/usr/bin/env python3
"""Tests for slips_generator.py"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slips_generator import (
    generate_slips, 
    PrizePicksClient,
    WNBADataEnricher,
    determine_pick,
    calculate_bet_amount,
    generate_reasoning
)

@pytest.fixture
def mock_prizepicks_response():
    """Mock PrizePicks API response."""
    return [
        {
            'id': '12345',
            'player_name': "A'ja Wilson",
            'team': 'LVA',
            'opponent': 'LA',
            'stat_type': 'points',
            'line_score': 25.5,
            'odds': -110,
            'game_date': '2024-06-21',
            'game_time': '19:00:00',
            'season_average': 27.3
        },
        {
            'id': '12346',
            'player_name': 'Breanna Stewart',
            'team': 'NY',
            'opponent': 'CHI',
            'stat_type': 'rebounds',
            'line_score': 8.5,
            'odds': -115,
            'game_date': '2024-06-21',
            'game_time': '19:30:00',
            'season_average': 9.1
        }
    ]

@pytest.fixture
def mock_phase_data():
    """Mock menstrual phase data."""
    return {
        "A'ja Wilson": {
            'current_phase': 'peak',
            'confidence_modifier': 0.15
        },
        'Breanna Stewart': {
            'current_phase': 'luteal',
            'confidence_modifier': 0.05
        }
    }

class TestPrizePicksClient:
    """Test PrizePicks API client."""
    
    @patch('requests.get')
    def test_get_projections_success(self, mock_get, mock_prizepicks_response):
        """Test successful API call."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': mock_prizepicks_response}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = PrizePicksClient()
        projections = client.get_projections('WNBA')
        
        assert len(projections) == 2
        assert projections[0]['player_name'] == "A'ja Wilson"
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_projections_retry_on_failure(self, mock_get):
        """Test retry logic on API failure."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
mock_response_fail.raise_for_status.side_effect = Exception('API Error')
        mock_response_fail.json.side_effect = Exception('API Error')
        mock_get.side_effect = [
            mock_response_fail,
            Mock(json=Mock(return_value={'data': []}), raise_for_status=Mock())
        ]
        
        client = PrizePicksClient()
        projections = client.get_projections('WNBA')
        
        assert projections == []
        assert mock_get.call_count == 2

class TestWNBADataEnricher:
    """Test WNBA data enrichment."""
    
    def test_enrich_projection_with_phase_data(self, mock_phase_data):
        """Test enriching projection with phase data."""
        with patch.object(WNBADataEnricher, '_load_phase_data', return_value=mock_phase_data):
            enricher = WNBADataEnricher()
            
            projection = {
                'player_name': "A'ja Wilson",
                'stat_type': 'points'
            }
            
            enriched = enricher.enrich_projection(projection)
            
            assert 'phase_info' in enriched
            assert enriched['phase_info']['current_phase'] == 'peak'
            assert enriched['confidence'] > 0.5
    
    def test_calculate_confidence(self):
        """Test confidence calculation."""
        enricher = WNBADataEnricher()
        
        # Test base confidence
        projection = {'stat_type': 'points'}
        conf = enricher._calculate_confidence(projection)
        assert 0.5 <= conf <= 1.0
        
        # Test with phase data
        projection['phase_info'] = {'current_phase': 'peak'}
        conf_with_phase = enricher._calculate_confidence(projection)
        assert conf_with_phase > conf

class TestSlipGeneration:
    """Test slip generation functions."""
    
    @patch('slips_generator.PrizePicksClient')
    @patch('slips_generator.WNBADataEnricher')
    def test_generate_slips(self, mock_enricher_class, mock_client_class, mock_prizepicks_response):
        """Test generating slips."""
        # Set up mocks
        mock_client = Mock()
        mock_client.get_projections.return_value = mock_prizepicks_response
                mock_client_class.return_value = mock_client

        # Mock enricher
        mock_enricher = Mock()
        mock_enricher.enrich_projection.side_effect = lambda x: {**x, 'confidence': 0.8}
        mock_enricher_class.return_value = mock_enricher
        
        mock_enricher = Mock()
        mock_enricher.enrich_projection.side_effect = lambda x: {**x, 'confidence': 0.75}
        mock_enricher_class.return_value = mock_enricher
        
        # Generate slips
        slips = generate_slips('2024-06-21', '2024-06-21', max_slips=5)
        
        assert len(slips) == 2
        assert all('slip_id' in slip for slip in slips)
        assert all('confidence' in slip for slip in slips)
        assert all(slip['confidence'] == 0.75 for slip in slips)
    
    def test_determine_pick(self):
        """Test pick determination logic."""
        # Test historical trend
        proj = {'historical_trend': 'over'}
        assert determine_pick(proj) == 'over'
        
        # Test based on average
        proj = {'line_score': 20, 'season_average': 25}
        assert determine_pick(proj) == 'over'
        
        proj = {'line_score': 20, 'season_average': 15}
        assert determine_pick(proj) == 'under'
        
        # Test phase-based
        proj = {'phase_info': {'current_phase': 'peak'}}
        assert determine_pick(proj) == 'over'
    
    @patch.dict(os.environ, {'BANKROLL': '1000'})
    def test_calculate_bet_amount(self):
        """Test bet amount calculation."""
        # Test with negative odds
        projection = {'confidence': 0.7, 'odds': -110}
        amount = calculate_bet_amount(projection)
        
        assert 10 <= amount <= 50  # Between 1% and 5% of bankroll
        
        # Test with positive odds
        projection = {'confidence': 0.8, 'odds': 150}
        amount = calculate_bet_amount(projection)
        
        assert 10 <= amount <= 50
    
    def test_generate_reasoning(self):
        """Test reasoning generation."""
        projection = {
            'confidence': 0.85,
            'historical_trend': 'over',
            'phase_info': {'current_phase': 'peak'},
            'line_score': 20,
            'season_average': 24,
            'opponent': 'LA'
        }
        
        reasoning = generate_reasoning(projection)
        
        assert 'High confidence' in reasoning
        assert 'trending over' in reasoning
        assert 'peak' in reasoning
        assert 'LA' in reasoning

class TestIntegration:
    """Integration tests."""
    
        @patch('slips_generator.WNBADataEnricher')
    @patch('slips_generator.PrizePicksClient')
    def test_full_slip_generation_flow(self, mock_client_class, mock_enricher_class):
        """Test complete slip generation workflow."""
        # Mock API response
        mock_client = Mock()
        mock_client.get_projections.return_value = [
            {
                'id': '123',
                'player_name': 'Test Player',
                'team': 'TEST',
                'opponent': 'OPP',
                'stat_type': 'points',
                'line_score': 20.5,
                'odds': -110,
                'game_date': '2024-06-21',
                'season_average': 22.0
            }
        ]
                mock_client_class.return_value = mock_client

        # Mock enricher
        mock_enricher = Mock()
        mock_enricher.enrich_projection.side_effect = lambda x: {**x, 'confidence': 0.8}
        mock_enricher_class.return_value = mock_enricher
        
        # Generate slips
        slips = generate_slips('2024-06-21', '2024-06-21')
        
        # Verify slip structure
        assert len(slips) >= 1
        slip = slips[0]
        
        # Check all required fields
        required_fields = [
            'slip_id', 'date', 'player', 'team', 'opponent',
            'prop_type', 'line', 'pick', 'odds', 'confidence',
            'amount', 'reasoning', 'prizepicks_id', 'status'
        ]
        
        for field in required_fields:
            assert field in slip, f"Missing required field: {field}"
        
        # Verify slip_id format
        assert slip['slip_id'].startswith('PG-')
        assert len(slip['slip_id']) > 10
        
        # Verify pick is valid
        assert slip['pick'] in ['over', 'under']
        
        # Verify confidence is in range
        assert 0 <= slip['confidence'] <= 1
        
        # Verify amount is positive
        assert slip['amount'] > 0

@pytest.mark.parametrize("days_back,expected_calls", [
    (0, 1),  # Just today
    (1, 2),  # Today and yesterday
    (7, 8),  # Week
])
def test_date_range_handling(days_back, expected_calls):
    """Test handling of date ranges."""
    with patch('slips_generator.PrizePicksClient') as mock_client_class:
        mock_client = Mock()
        mock_client.get_projections.return_value = []
                mock_client_class.return_value = mock_client

        # Mock enricher
        mock_enricher = Mock()
        mock_enricher.enrich_projection.side_effect = lambda x: {**x, 'confidence': 0.8}
        mock_enricher_class.return_value = mock_enricher
        
        today = datetime.now().strftime('%Y-%m-%d')
        slips = generate_slips(today, today)
        
        # Should only call API once for single day
        assert mock_client.get_projections.call_count == 1






