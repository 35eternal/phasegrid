#!/usr/bin/env python3
"""Generate real betting slips from PrizePicks and WNBA data."""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import uuid

# Set up logging
logger = logging.getLogger(__name__)

class PrizePicksClient:
    """Client for interacting with PrizePicks API."""
    
    def __init__(self):
        """Initialize the PrizePicks client."""
        self.base_url = "https://api.prizepicks.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_projections(self, league: str = "WNBA") -> List[Dict[str, Any]]:
        """Fetch current projections from PrizePicks."""
        try:
            # Get projections endpoint
            url = f"{self.base_url}/projections"
            params = {
                'league_id': self._get_league_id(league),
                'per_page': 100,
                'single_stat': 'true'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"Error fetching PrizePicks projections: {e}")
            return []
    
    def _get_league_id(self, league: str) -> int:
        """Get league ID for PrizePicks API."""
        league_map = {
            'WNBA': 3,
            'NBA': 2,
            'NFL': 1,
            'MLB': 4
        }
        return league_map.get(league.upper(), 3)

class WNBADataEnricher:
    """Enrich slips with WNBA-specific data and analysis."""
    
    def __init__(self):
        """Initialize the data enricher."""
        # Load any existing phase data, player mappings, etc.
        self.phase_data = self._load_phase_data()
        self.player_mappings = self._load_player_mappings()
        
    def _load_phase_data(self) -> Dict[str, Any]:
        """Load menstrual cycle phase data if available."""
        phase_file = "data/phase_data.json"
        if os.path.exists(phase_file):
            with open(phase_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_player_mappings(self) -> Dict[str, str]:
        """Load player name mappings."""
        mapping_file = "data/player_mappings.json"
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                return json.load(f)
        return {}
    
    def enrich_projection(self, projection: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a projection with additional WNBA data."""
        player_name = projection.get('player_name', '')
        
        # Add phase data if available
        if player_name in self.phase_data:
            projection['phase_info'] = self.phase_data[player_name]
            
        # Add confidence based on your existing analysis
        projection['confidence'] = self._calculate_confidence(projection)
        
        return projection
    
    def _calculate_confidence(self, projection: Dict[str, Any]) -> float:
        """Calculate confidence score for a projection."""
        # Base confidence
        confidence = 0.5
        
        # Adjust based on prop type
        prop_type = projection.get('stat_type', '')
        if prop_type in ['points', 'rebounds', 'assists']:
            confidence += 0.1
        
        # Adjust based on line value vs recent performance
        # This would integrate with your existing backtesting data
        
        # Adjust based on phase data if available
        if 'phase_info' in projection:
            phase = projection['phase_info'].get('current_phase')
            if phase == 'peak':
                confidence += 0.15
            elif phase == 'low':
                confidence -= 0.1
                
        return min(max(confidence, 0.0), 1.0)

def generate_slips(start_date: str, end_date: str, 
                  max_slips: int = 10,
                  min_confidence: float = 0.65) -> List[Dict[str, Any]]:
    """
    Generate betting slips for the given date range.
    
    Args:
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        max_slips: Maximum number of slips to generate
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of betting slip dictionaries
    """
    logger.info(f"Generating slips from {start_date} to {end_date}")
    
    # Initialize clients
    prizepicks = PrizePicksClient()
    enricher = WNBADataEnricher()
    
    # Fetch current projections
    projections = prizepicks.get_projections("WNBA")
    logger.info(f"Fetched {len(projections)} projections from PrizePicks")
    
    # Filter and enrich projections
    slips = []
    
    for proj in projections:
        # Skip if not in date range
        game_date = proj.get('game_date', start_date)
        if game_date < start_date or game_date > end_date:
            continue
            
        # Enrich with additional data
        enriched = enricher.enrich_projection(proj)
        
        # Skip if confidence too low
        if enriched.get('confidence', 0) < min_confidence:
            continue
            
        # Create slip
        slip = {
            'slip_id': f"PG-{uuid.uuid4().hex[:8]}-{datetime.now().strftime('%Y%m%d')}",
            'date': game_date,
            'player': enriched.get('player_name', 'Unknown'),
            'team': enriched.get('team', 'Unknown'),
            'opponent': enriched.get('opponent', 'Unknown'),
            'prop_type': enriched.get('stat_type', 'unknown'),
            'line': enriched.get('line_score', 0),
            'pick': determine_pick(enriched),
            'odds': enriched.get('odds', -110),
            'confidence': enriched.get('confidence', 0.5),
            'amount': calculate_bet_amount(enriched),
            'reasoning': generate_reasoning(enriched),
            'phase_data': enriched.get('phase_info', {}),
            'prizepicks_id': enriched.get('id', ''),
            'game_time': enriched.get('game_time', ''),
            'status': 'pending'
        }
        
        slips.append(slip)
        
        # Stop if we have enough slips
        if len(slips) >= max_slips:
            break
    
    # Sort by confidence
    slips.sort(key=lambda x: x['confidence'], reverse=True)
    
    logger.info(f"Generated {len(slips)} slips with confidence >= {min_confidence}")
    return slips

def determine_pick(projection: Dict[str, Any]) -> str:
    """Determine whether to pick over or under."""
    # This is where you'd integrate your backtesting logic
    # For now, simple logic based on recent performance
    
    # Check if player tends to go over/under
    historical_trend = projection.get('historical_trend', 'neutral')
    
    if historical_trend == 'over':
        return 'over'
    elif historical_trend == 'under':
        return 'under'
    
    # Default logic: if line seems low compared to average, go over
    line = projection.get('line_score', 0)
    average = projection.get('season_average', line)
    
    if average > line * 1.1:  # 10% higher average
        return 'over'
    elif average < line * 0.9:  # 10% lower average
        return 'under'
    
    # Phase-based adjustment
    if 'phase_info' in projection:
        phase = projection['phase_info'].get('current_phase')
        if phase == 'peak':
            return 'over'
        elif phase == 'low':
            return 'under'
    
    # Default to over for high confidence
    return 'over' if projection.get('confidence', 0.5) > 0.7 else 'under'

def calculate_bet_amount(projection: Dict[str, Any]) -> float:
    """Calculate bet amount based on confidence and Kelly Criterion."""
    base_bankroll = float(os.getenv('BANKROLL', '1000'))
    
    # Kelly Criterion simplified
    confidence = projection.get('confidence', 0.5)
    odds = projection.get('odds', -110)
    
    # Convert American odds to decimal
    if odds < 0:
        decimal_odds = 1 + (100 / abs(odds))
    else:
        decimal_odds = 1 + (odds / 100)
    
    # Kelly fraction
    kelly_fraction = (confidence * decimal_odds - 1) / (decimal_odds - 1)
    
    # Apply safety factor (quarter Kelly)
    safe_fraction = kelly_fraction * 0.25
    
    # Calculate amount
    amount = base_bankroll * safe_fraction
    
    # Apply min/max limits
    min_bet = base_bankroll * 0.01  # 1% minimum
    max_bet = base_bankroll * 0.05  # 5% maximum
    
    return round(max(min_bet, min(amount, max_bet)), 2)

def generate_reasoning(projection: Dict[str, Any]) -> str:
    """Generate reasoning for the pick."""
    reasons = []
    
    # Confidence-based reasoning
    confidence = projection.get('confidence', 0.5)
    if confidence > 0.8:
        reasons.append("High confidence pick")
    elif confidence > 0.7:
        reasons.append("Strong value identified")
    
    # Trend-based reasoning
    trend = projection.get('historical_trend', 'neutral')
    if trend != 'neutral':
        reasons.append(f"Player trending {trend}")
    
    # Phase-based reasoning
    if 'phase_info' in projection:
        phase = projection['phase_info'].get('current_phase')
        if phase:
            reasons.append(f"Menstrual phase: {phase}")
    
    # Line value reasoning
    line = projection.get('line_score', 0)
    average = projection.get('season_average', line)
    if average > line * 1.15:
        reasons.append(f"Line ({line}) significantly below average ({average:.1f})")
    elif average < line * 0.85:
        reasons.append(f"Line ({line}) significantly above average ({average:.1f})")
    
    # Matchup reasoning
    opponent = projection.get('opponent', '')
    if opponent:
        reasons.append(f"Favorable matchup vs {opponent}")
    
    return "; ".join(reasons) if reasons else "Value play based on model analysis"

# For backward compatibility with existing code
def main():
    """Test function for slip generation."""
    today = datetime.now().strftime('%Y-%m-%d')
    slips = generate_slips(today, today)
    
    for slip in slips:
        print(f"Slip: {slip['player']} - {slip['prop_type']} "
              f"{slip['pick']} {slip['line']} @ {slip['odds']}")
        print(f"  Confidence: {slip['confidence']:.2%}")
        print(f"  Amount: ${slip['amount']}")
        print(f"  Reasoning: {slip['reasoning']}")
        print()

if __name__ == "__main__":
    main()