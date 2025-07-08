#!/usr/bin/env python3
"""Slip optimizer with Power/Flex support and beam search for 2-6 legs."""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from itertools import combinations
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Bet:
    """Individual bet selection."""
    player: str
    prop_type: str
    line: float
    over_under: str
    odds: float
    confidence: float
    game: str
    
    def __hash__(self):
        return hash((self.player, self.prop_type, self.line, self.over_under))
        
    def __eq__(self, other):
        return (self.player, self.prop_type) == (other.player, other.prop_type)


@dataclass 
class Slip:
    """Betting slip with multiple legs."""
    bets: Tuple[Bet, ...]  # Fixed: Using tuple for hashability
    slip_type: str  # 'Power' or 'Flex'
    expected_value: float
    total_odds: float
    confidence: float
    
    def __hash__(self):
        return hash((self.bets, self.slip_type))
        
    @property
    def num_legs(self) -> int:
        return len(self.bets)
        
    def prop_usage_count(self) -> Dict[str, int]:
        """Count prop usage by player."""
        usage = {}
        for bet in self.bets:
            if bet.player not in usage:
                usage[bet.player] = 0
            usage[bet.player] += 1
        return usage


class SlipOptimizer:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize slip optimizer with payout configurations."""
        self.config_path = config_path or "config/payout_tables.json"
        self.payouts = self._load_payouts()
        
        # Constraints
        self.min_legs = 2
        self.max_legs = 6
        self.max_prop_usage_per_player = 3
        self.min_confidence = 0.45
        
        # Beam search parameters
        self.default_beam_width = 20
        
    def _load_payouts(self) -> Dict:
        """Load payout tables from configuration."""
        config_path = Path(self.config_path)
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load payout config: {e}")
                
        # Default payout structure
        return {
            'power': {
                '2': 2.5,
                '3': 6.0,
                '4': 12.5,
                '5': 25.0,
                '6': 50.0
            },
            'flex': {
                '2': {
                    '2': 2.3
                },
                '3': {
                    '2': 1.2,
                    '3': 5.0
                },
                '4': {
                    '2': 0.4,
                    '3': 2.0,
                    '4': 10.0
                },
                '5': {
                    '3': 1.5,
                    '4': 5.0,
                    '5': 20.0
                },
                '6': {
                    '4': 4.0,
                    '5': 12.0,
                    '6': 35.0
                }
            }
        }
        
    def optimize_slips(self,
                      available_bets: List[Dict],
                      target_slips: int = 5,
                      slip_types: List[str] = ['Power', 'Flex'],
                      beam_width: Optional[int] = None) -> List[Slip]:
        """
        Optimize slip selection using beam search.
        
        Args:
            available_bets: List of available betting opportunities
            target_slips: Number of slips to generate
            slip_types: Types of slips to generate
            beam_width: Beam width for search (None = use default)
            
        Returns:
            List of optimized slips
        """
        # Convert to Bet objects
        bets = [
            Bet(
                player=b['player'],
                prop_type=b['prop_type'],
                line=b['line'],
                over_under=b.get('over_under', 'over' if b.get('projection', b['line']) > b['line'] else 'under'),
                odds=b['odds'],
                confidence=b['confidence'],
                game=b.get('game', 'Unknown')
            )
            for b in available_bets
            if b['confidence'] >= self.min_confidence
        ]
        
        if not bets:
            return []
            
        beam_width = beam_width or self.default_beam_width
        optimized_slips = []
        
        # Generate slips for each type
        for slip_type in slip_types:
            if slip_type == 'Power':
                slips = self._generate_power_slips(bets, target_slips // len(slip_types), beam_width)
            else:  # Flex
                slips = self._generate_flex_slips(bets, target_slips // len(slip_types), beam_width)
                
            optimized_slips.extend(slips)
            
        # Sort by expected value and return top slips
        optimized_slips.sort(key=lambda s: s.expected_value, reverse=True)
        
        # Ensure no duplicate slips
        unique_slips = []
        seen = set()
        
        for slip in optimized_slips:
            if slip not in seen:
                unique_slips.append(slip)
                seen.add(slip)
                
        return unique_slips[:target_slips]
        
    def _generate_power_slips(self, bets: List[Bet], target_count: int, beam_width: int) -> List[Slip]:
        """Generate Power Play slips (all legs must win)."""
        slips = []
        
        # Focus on 2-3 leg Power plays with high confidence
        high_conf_bets = [b for b in bets if b.confidence >= 0.55]
        
        if len(high_conf_bets) < 2:
            high_conf_bets = sorted(bets, key=lambda b: b.confidence, reverse=True)[:10]
            
        # Use beam search for optimal combinations
        for num_legs in [2, 3]:
            if len(high_conf_bets) < num_legs:
                continue
                
            leg_slips = self._beam_search_slips(
                bets=high_conf_bets,
                num_legs=num_legs,
                slip_type='Power',
                beam_width=beam_width,
                max_slips=target_count // 2
            )
            
            slips.extend(leg_slips)
            
        return slips[:target_count]
        
    def _generate_flex_slips(self, bets: List[Bet], target_count: int, beam_width: int) -> List[Slip]:
        """Generate Flex Play slips (partial wins allowed)."""
        slips = []
        
        # Generate diverse leg counts
        leg_distribution = {
            2: int(target_count * 0.3),
            3: int(target_count * 0.3),
            4: int(target_count * 0.2),
            5: int(target_count * 0.1),
            6: int(target_count * 0.1)
        }
        
        for num_legs, count in leg_distribution.items():
            if len(bets) < num_legs or count == 0:
                continue
                
            # Use appropriate confidence threshold
            if num_legs <= 3:
                min_conf = 0.52
            else:
                min_conf = 0.48
                
            eligible_bets = [b for b in bets if b.confidence >= min_conf]
            
            if len(eligible_bets) >= num_legs:
                leg_slips = self._beam_search_slips(
                    bets=eligible_bets,
                    num_legs=num_legs,
                    slip_type='Flex',
                    beam_width=beam_width,
                    max_slips=count
                )
                
                slips.extend(leg_slips)
                
        return slips[:target_count]
        
    def _beam_search_slips(self,
                          bets: List[Bet],
                          num_legs: int,
                          slip_type: str,
                          beam_width: int,
                          max_slips: int) -> List[Slip]:
        """Use beam search to find optimal slip combinations."""
        # Initialize beam with single bets
        beam = [(bet,) for bet in bets[:beam_width * 2]]
        
        # Build up to desired number of legs
        for leg in range(2, num_legs + 1):
            new_beam = []
            
            for partial_slip in beam:
                # Get valid extensions
                extensions = self._get_valid_extensions(partial_slip, bets)
                
                for bet in extensions:
                    new_slip = partial_slip + (bet,)
                    
                    # Check constraints
                    if self._violates_constraints(new_slip):
                        continue
                        
                    new_beam.append(new_slip)
                    
            # Score and prune beam
            if new_beam:
                scored_beam = [
                    (self._score_partial_slip(slip, slip_type), slip)
                    for slip in new_beam
                ]
                scored_beam.sort(key=lambda x: x[0], reverse=True)
                beam = [slip for _, slip in scored_beam[:beam_width]]
            else:
                break
                
        # Convert to Slip objects and calculate final scores
        slips = []
        
        for bet_tuple in beam:
            if len(bet_tuple) == num_legs:
                slip = self._create_slip(bet_tuple, slip_type)
                if slip.expected_value > 0:
                    slips.append(slip)
                    
        # Sort by expected value
        slips.sort(key=lambda s: s.expected_value, reverse=True)
        
        return slips[:max_slips]
        
    def _get_valid_extensions(self, partial_slip: Tuple[Bet, ...], bets: List[Bet]) -> List[Bet]:
        """Get valid bets that can extend the partial slip."""
        used_props = set((bet.player, bet.prop_type) for bet in partial_slip)
        used_games = set(bet.game for bet in partial_slip)
        
        valid = []
        
        for bet in bets:
            # Skip if already used this prop
            if (bet.player, bet.prop_type) in used_props:
                continue
                
            # Prefer diverse games
            if len(used_games) < 3 and bet.game in used_games:
                continue
                
            valid.append(bet)
            
        return valid
        
    def _violates_constraints(self, bet_tuple: Tuple[Bet, ...]) -> bool:
        """Check if slip violates constraints."""
        # Check prop usage per player
        player_counts = {}
        
        for bet in bet_tuple:
            if bet.player not in player_counts:
                player_counts[bet.player] = 0
            player_counts[bet.player] += 1
            
            if player_counts[bet.player] > self.max_prop_usage_per_player:
                return True
                
        return False
        
    def _score_partial_slip(self, bet_tuple: Tuple[Bet, ...], slip_type: str) -> float:
        """Score a partial slip for beam search."""
        # Average confidence
        avg_confidence = sum(b.confidence for b in bet_tuple) / len(bet_tuple)
        
        # Diversity bonus
        unique_players = len(set(b.player for b in bet_tuple))
        diversity_bonus = unique_players / len(bet_tuple) * 0.1
        
        # Game diversity
        unique_games = len(set(b.game for b in bet_tuple))
        game_bonus = unique_games / len(bet_tuple) * 0.05
        
        return avg_confidence + diversity_bonus + game_bonus
        
    def _create_slip(self, bet_tuple: Tuple[Bet, ...], slip_type: str) -> Slip:
        """Create a Slip object with calculated expected value."""
        # Calculate combined odds and confidence
        combined_odds = 1.0
        combined_confidence = 1.0
        
        for bet in bet_tuple:
            # Convert American to decimal odds
            if bet.odds < 0:
                decimal_odds = (-100 / bet.odds) + 1
            else:
                decimal_odds = (bet.odds / 100) + 1
                
            combined_odds *= decimal_odds
            combined_confidence *= bet.confidence
            
        # Calculate expected value
        if slip_type == 'Power':
            # Power play: all must win
            ev = combined_confidence * combined_odds - 1
            
        else:  # Flex
            # Calculate expected value across all possible outcomes
            num_legs = len(bet_tuple)
            flex_payouts = self.payouts['flex'].get(str(num_legs), {})
            
            ev = 0
            
            # Calculate probability of each outcome
            for correct in range(num_legs + 1):
                # Binomial probability (simplified - assumes equal confidence)
                avg_conf = sum(b.confidence for b in bet_tuple) / num_legs
                prob = self._binomial_probability(num_legs, correct, avg_conf)
                
                # Get payout for this outcome
                payout_mult = flex_payouts.get(str(correct), 0)
                
                ev += prob * payout_mult
                
            ev -= 1  # Subtract stake
            
        return Slip(
            bets=bet_tuple,
            slip_type=slip_type,
            expected_value=ev,
            total_odds=combined_odds,
            confidence=combined_confidence
        )
        
    def _binomial_probability(self, n: int, k: int, p: float) -> float:
        """Calculate binomial probability."""
        from math import comb
        return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
        
    def format_slip_details(self, slip: Slip, stake: float) -> Dict:
        """Format slip details for output."""
        details = {
            'slip_type': slip.slip_type,
            'num_legs': slip.num_legs,
            'stake': round(stake, 2),
            'expected_value': round(slip.expected_value, 3),
            'legs': []
        }
        
        # Add leg details
        for bet in slip.bets:
            details['legs'].append({
                'player': bet.player,
                'prop': bet.prop_type,
                'line': bet.line,
                'pick': bet.over_under,
                'odds': bet.odds,
                'confidence': round(bet.confidence, 3)
            })
            
        # Calculate potential payouts
        if slip.slip_type == 'Power':
            details['potential_payout'] = round(stake * slip.total_odds, 2)
            
        else:  # Flex
            flex_payouts = self.payouts['flex'].get(str(slip.num_legs), {})
            details['payout_tiers'] = {}
            
            for correct, multiplier in flex_payouts.items():
                details['payout_tiers'][f"{correct}_correct"] = round(stake * multiplier, 2)
                
        return details
        
    def get_payout_table(self, slip_type: str, num_legs: int) -> Dict:
        """Get payout table for given slip type and legs."""
        if slip_type == 'Power':
            return {'all_correct': self.payouts['power'].get(str(num_legs), 0)}
        else:
            return self.payouts['flex'].get(str(num_legs), {})


if __name__ == "__main__":
    # Example usage
    optimizer = SlipOptimizer()
    
    # Sample bets
    sample_bets = [
        {
            'player': 'A. Wilson',
            'prop_type': 'points',
            'line': 22.5,
            'odds': -115,
            'confidence': 0.58,
            'projection': 24.2,
            'game': 'LAS @ LA'
        },
        {
            'player': 'S. Stewart',
            'prop_type': 'rebounds', 
            'line': 8.5,
            'odds': -110,
            'confidence': 0.62,
            'projection': 9.8,
            'game': 'LAS @ LA'
        },
        {
            'player': 'B. Jones',
            'prop_type': 'assists',
            'line': 5.5,
            'odds': -120,
            'confidence': 0.55,
            'projection': 6.1,
            'game': 'NY @ CHI'
        },
        {
            'player': 'A. Wilson',
            'prop_type': 'rebounds',
            'line': 6.5,
            'odds': -105,
            'confidence': 0.53,
            'projection': 7.2,
            'game': 'LAS @ LA'
        }
    ]
    
    # Optimize slips
    slips = optimizer.optimize_slips(
        available_bets=sample_bets,
        target_slips=3,
        slip_types=['Power', 'Flex']
    )
    
    # Display results
    print("=== Optimized Slips ===")
    for i, slip in enumerate(slips, 1):
        print(f"\nSlip {i}:")
        details = optimizer.format_slip_details(slip, stake=10.0)
        print(f"  Type: {details['slip_type']}")
        print(f"  Legs: {details['num_legs']}")
        print(f"  Expected Value: {details['expected_value']:.1%}")
        
        for j, leg in enumerate(details['legs'], 1):
            print(f"  Leg {j}: {leg['player']} {leg['prop']} {leg['pick']} {leg['line']} @ {leg['odds']}")
            
    # Show payout tables
    print("\n=== Payout Tables ===")
    print("\nFlex 4-leg payouts:")
    print(optimizer.get_payout_table('Flex', 4))
    
    print("\nFlex 5-leg payouts:")
    print(optimizer.get_payout_table('Flex', 5))
    
    print("\nFlex 6-leg payouts:")
    print(optimizer.get_payout_table('Flex', 6))