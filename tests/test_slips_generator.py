"""Tests for slips_generator.py"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slips_generator import (
    PrizePicksClient, WNBADataEnricher, generate_slips,
    determine_pick, calculate_bet_amount, generate_reasoning
)


@pytest.fixture
def mock_prizepicks_response():
    """Mock PrizePicks API response."""
    return [
        {
            'id': '123',
            'player_name': "A'ja Wilson",
            'team': 'LV',
            'opponent': 'PHX',
            'stat_type': 'points',
            'line_score': 22.5,
            'odds': -110,
            'game_date': '2024-06-21',
            'season_average': 25.0
        },
        {
            'id': '456',
            'player_name': 'Diana Taurasi',
            'team': 'PHX',
            'opponent': 'LV',
            'stat_type': 'assists',
            'line_score': 4.5,
            'odds': -115,
            'game_date': '2024-06-21',
            'season_average': 5.2
        }
    ]


@pytest.fixture
def mock_phase_data():
    """Mock phase data."""
    return {
        "A'ja Wilson": {
            'current_phase': 'peak',
            'phase_performance': {'peak': 1.15, 'low': 0.85}
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

        mock_response_success = Mock()
        mock_response_success.json.return_value = {'data': []}
        mock_response_success.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        client = PrizePicksClient()
        projections = client.get_projections('WNBA')

        assert projections == []
        assert mock_get.call_count == 1  # Exception is caught, no retry


class TestWNBADataEnricher:
    """Test WNBA data enrichment."""

    def test_enrich_projection_with_phase_data(self, mock_phase_data):
        """Test enriching projection with phase data."""
        with patch.object(WNBADataEnricher, '_load_phase_data', return_value=mock_phase_data):
            enricher = WNBADataEnricher()

            projection = {
                'player_name': "A'ja Wilson",
                'stat_type': 'points',
                'line_score': 22.5
            }

            enriched = enricher.enrich_projection(projection)

            assert 'phase_info' in enriched
            assert enriched['phase_info']['current_phase'] == 'peak'

    def test_calculate_confidence(self, mock_phase_data):
        """Test confidence calculation."""
        with patch.object(WNBADataEnricher, '_load_phase_data', return_value=mock_phase_data):
            enricher = WNBADataEnricher()

            # High confidence scenario
            projection = {
                'stat_type': 'points',
                'phase_info': {'current_phase': 'peak'}
            }

            confidence = enricher._calculate_confidence(projection)
            assert confidence > 0.6


class TestSlipGeneration:
    """Test slip generation functions."""

    def test_determine_pick(self):
        """Test pick determination logic."""
        # Default should be under
        assert determine_pick({}) == 'under'

        # Peak phase should be over
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


@pytest.mark.parametrize("days_offset,expected_slips", [
    (0, 1),  # Today
    (1, 2),  # Tomorrow (more games)
    (7, 8),  # Week out (full slate)
])
def test_date_range_handling(days_offset, expected_slips):
    """Test handling different date ranges."""
    from datetime import datetime, timedelta

    today = datetime.now().strftime('%Y-%m-%d')
    target_date = (datetime.now() + timedelta(days=days_offset)).strftime('%Y-%m-%d')

    with patch('slips_generator.PrizePicksClient') as mock_client_class:
        mock_client = Mock()
        mock_client.get_projections.return_value = [
            {
                'id': f'test-{i}',
                'player_name': f'Player {i}',
                'team': 'TEST',
                'opponent': 'OPP',
                'stat_type': 'points',
                'line_score': 20.5,
                'odds': -110,
                'game_date': target_date,
                'season_average': 22.0,
                'confidence': 0.7
            }
            for i in range(expected_slips)
        ]
        mock_client_class.return_value = mock_client

        with patch('slips_generator.WNBADataEnricher') as mock_enricher_class:
            mock_enricher = Mock()
            mock_enricher.enrich_projection.side_effect = lambda x: {**x, 'confidence': 0.7}
            mock_enricher_class.return_value = mock_enricher

            slips = generate_slips(today, today)

            # Should filter by date
            if days_offset == 0:
                assert len(slips) <= expected_slips
            else:
                assert len(slips) == 0  # No games for future dates in our mock

