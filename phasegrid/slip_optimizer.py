"""
Slip optimization module for PhaseGrid system.
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SlipOptimizer:
    """Optimizes slip generation based on various parameters."""
    
    def __init__(self, 
                 bankroll: float = 1000.0,
                 max_bet_pct: float = 0.05,
                 min_edge: float = 0.05,
                 correlation_threshold: float = 0.5):
        """Initialize optimizer with configuration."""
        self.bankroll = bankroll
        self.max_bet_pct = max_bet_pct
        self.min_edge = min_edge
        self.correlation_threshold = correlation_threshold
        logger.info(f"Initialized SlipOptimizer with bankroll=${bankroll}")
    
    def optimize(self, props: List[Dict[str, Any]], 
                 date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Optimize prop selection for slip generation.
        
        Args:
            props: List of available props
            date: Target date for optimization
            
        Returns:
            List of optimized slips
        """
        if not props:
            return []
            
        # Filter props by minimum edge
        filtered_props = [
            prop for prop in props 
            if prop.get('edge', 0) >= self.min_edge
        ]
        
        # Calculate Kelly fraction for each prop
        for prop in filtered_props:
            prop['kelly_fraction'] = self.calculate_kelly_fraction(
                prop.get('edge', 0),
                prop.get('odds', 2.0)
            )
            prop['bet_size'] = min(
                prop['kelly_fraction'] * self.bankroll,
                self.bankroll * self.max_bet_pct
            )
        
        # Sort by expected value
        filtered_props.sort(
            key=lambda x: x.get('edge', 0) * x.get('bet_size', 0),
            reverse=True
        )
        
        # Apply correlation filter
        optimized_slips = self._apply_correlation_filter(filtered_props)
        
        logger.info(f"Optimized {len(props)} props to {len(optimized_slips)} slips")
        return optimized_slips
    
    def calculate_kelly_fraction(self, edge: float, odds: float) -> float:
        """
        Calculate Kelly fraction for bet sizing.
        
        Args:
            edge: Expected edge (as decimal, e.g., 0.05 for 5%)
            odds: Decimal odds
            
        Returns:
            Kelly fraction
        """
        if edge <= 0 or odds <= 1:
            return 0.0
            
        # Kelly formula: f = (p*b - q) / b
        # where p = probability of winning, q = probability of losing, b = odds-1
        p = (1 + edge) / odds  # Implied probability + edge
        q = 1 - p
        b = odds - 1
        
        kelly = (p * b - q) / b if b > 0 else 0
        
        # Apply Kelly divisor for safety (quarter Kelly)
        return max(0, min(kelly / 4, self.max_bet_pct))
    
    def _apply_correlation_filter(self, props: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply correlation filter to reduce correlated bets."""
        if not props:
            return []
            
        selected = [props[0]]  # Always include the best prop
        
        for prop in props[1:]:
            # Check correlation with already selected props
            is_correlated = False
            for selected_prop in selected:
                if self._calculate_correlation(prop, selected_prop) > self.correlation_threshold:
                    is_correlated = True
                    break
                    
            if not is_correlated:
                selected.append(prop)
                
        return selected
    
    def _calculate_correlation(self, prop1: Dict[str, Any], prop2: Dict[str, Any]) -> float:
        """Calculate correlation between two props."""
        # Simple correlation based on same player/game
        if prop1.get('player_id') == prop2.get('player_id'):
            return 0.8
        if prop1.get('game_id') == prop2.get('game_id'):
            return 0.5
        return 0.0
    
    def validate_edge(self, edge: float) -> bool:
        """Validate edge is within acceptable range."""
        return 0 <= edge <= 1
    
    def apply_bankroll_constraint(self, bet_size: float) -> float:
        """Apply bankroll constraint to bet size."""
        return min(bet_size, self.bankroll * self.max_bet_pct)
