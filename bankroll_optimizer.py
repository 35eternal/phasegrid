#!/usr/bin/env python3
"""Phase-aware Kelly criterion bankroll optimizer with dynamic divisors."""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Union, Tuple
from datetime import datetime


class BankrollOptimizer:
    def __init__(self, config_path: Optional[str] = None):
        """Initialize bankroll optimizer with phase-aware Kelly divisors."""
        self.config_path = config_path or "config/phase_kelly_divisors.json"
        self.divisors = self._load_divisors()
        
        # Default static divisors (fallback)
        self.static_divisors = {
            'menstrual': 8.0,
            'follicular': 6.0,
            'ovulatory': 4.0,
            'luteal': 5.0
        }
        
        # Risk parameters
        self.max_bet_fraction = 0.05  # Max 5% of bankroll per bet
        self.min_bet_amount = 5.0     # Minimum $5 bet
        
    def _load_divisors(self) -> Dict:
        """Load divisor configuration from JSON."""
        config_path = Path(self.config_path)
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config
            except Exception as e:
                print(f"Warning: Failed to load divisor config: {e}")
                
        # Return default structure if file doesn't exist
        return {
            'mode': 'static',
            'static_divisors': self.static_divisors,
            'dynamic_formulas': {
                'menstrual': "10 - (win_rate - 0.45) * 20",
                'follicular': "8 - (win_rate - 0.50) * 16", 
                'ovulatory': "6 - (win_rate - 0.55) * 12",
                'luteal': "7 - (win_rate - 0.52) * 14"
            }
        }
        
    def calculate_kelly_fraction(self, 
                               win_prob: float, 
                               odds: float,
                               phase: str,
                               win_rate: Optional[float] = None) -> float:
        """
        Calculate Kelly fraction with phase-aware adjustments.
        
        Args:
            win_prob: Probability of winning (0-1)
            odds: Decimal odds (e.g., 2.5 for +150)
            phase: Menstrual phase ('menstrual', 'follicular', 'ovulatory', 'luteal')
            win_rate: Historical win rate for dynamic divisor calculation
            
        Returns:
            Kelly fraction (0-1) for bet sizing
        """
        # Validate inputs
        if not 0 <= win_prob <= 1:
            raise ValueError(f"Invalid win_prob: {win_prob}")
            
        if odds <= 0:
            raise ValueError(f"Invalid odds: {odds}")
            
        # Calculate raw Kelly fraction: f = (p*b - q) / b
        # where p = win_prob, q = 1-p, b = odds-1
        q = 1 - win_prob
        b = odds - 1
        
        raw_kelly = (win_prob * b - q) / b
        
        # If negative expectation, don't bet
        if raw_kelly <= 0:
            return 0.0
            
        # Get phase-specific divisor
        divisor = self._get_divisor(phase, win_rate)
        
        # Apply divisor for conservative sizing
        adjusted_kelly = raw_kelly / divisor
        
        # Apply maximum bet constraint
        final_kelly = min(adjusted_kelly, self.max_bet_fraction)
        
        return final_kelly
        
    def _get_divisor(self, phase: str, win_rate: Optional[float] = None) -> float:
        """Get divisor based on phase and optional win rate."""
        # Normalize phase name
        phase = phase.lower()
        
        # Handle special case mapping
        if phase == 'high_confidence':
            phase = 'luteal'  # Or make this configurable
            
        if phase not in self.static_divisors:
            print(f"Warning: Unknown phase '{phase}', using follicular")
            phase = 'follicular'
            
        # Check if dynamic mode is enabled
        if self.divisors.get('mode') == 'dynamic' and win_rate is not None:
            return self._evaluate_dynamic_divisor(phase, win_rate)
        else:
            # Use static divisor
            return self.divisors.get('static_divisors', {}).get(phase, self.static_divisors[phase])
            
    def _evaluate_dynamic_divisor(self, phase: str, win_rate: float) -> float:
        """Evaluate dynamic divisor formula."""
        formulas = self.divisors.get('dynamic_formulas', {})
        
        if phase not in formulas:
            return self.static_divisors[phase]
            
        formula = formulas[phase]
        
        try:
            # Create safe evaluation context
            context = {
                'win_rate': win_rate,
                'min': min,
                'max': max,
                'abs': abs,
                'sqrt': np.sqrt,
                'log': np.log
            }
            
            # Evaluate formula
            divisor = eval(formula, {"__builtins__": {}}, context)
            
            # Ensure divisor is reasonable (between 2 and 20)
            divisor = max(2.0, min(20.0, float(divisor)))
            
            return divisor
            
        except Exception as e:
            print(f"Error evaluating dynamic divisor for {phase}: {e}")
            return self.static_divisors[phase]
            
    def calculate_stake(self,
                       bankroll: float,
                       win_prob: float,
                       odds: float,
                       phase: str,
                       win_rate: Optional[float] = None) -> float:
        """
        Calculate optimal stake amount.
        
        Args:
            bankroll: Current bankroll amount
            win_prob: Probability of winning
            odds: Decimal odds
            phase: Menstrual phase
            win_rate: Historical win rate
            
        Returns:
            Stake amount (rounded to 2 decimal places)
        """
        kelly_fraction = self.calculate_kelly_fraction(win_prob, odds, phase, win_rate)
        
        if kelly_fraction <= 0:
            return 0.0
            
        stake = bankroll * kelly_fraction
        
        # Apply minimum bet constraint
        if stake < self.min_bet_amount:
            return 0.0  # Don't bet if we can't meet minimum
            
        # Round to 2 decimal places
        return round(stake, 2)
        
    def optimize_portfolio(self,
                          bankroll: float,
                          opportunities: list,
                          phase: str,
                          win_rate: Optional[float] = None,
                          max_bets: int = 10) -> list:
        """
        Optimize betting portfolio across multiple opportunities.
        
        Args:
            bankroll: Total bankroll
            opportunities: List of betting opportunities with win_prob and odds
            phase: Current menstrual phase
            win_rate: Historical win rate
            max_bets: Maximum number of concurrent bets
            
        Returns:
            List of optimized bets with stake amounts
        """
        # Calculate Kelly fraction for each opportunity
        for opp in opportunities:
            opp['kelly_fraction'] = self.calculate_kelly_fraction(
                win_prob=opp['win_prob'],
                odds=opp['odds'],
                phase=phase,
                win_rate=win_rate
            )
            opp['expected_growth'] = opp['kelly_fraction'] * (opp['win_prob'] * opp['odds'] - 1)
            
        # Sort by expected growth rate
        opportunities.sort(key=lambda x: x['expected_growth'], reverse=True)
        
        # Select top opportunities
        selected = []
        allocated_bankroll = 0
        
        for opp in opportunities[:max_bets]:
            if opp['kelly_fraction'] <= 0:
                continue
                
            # Calculate stake with remaining bankroll
            remaining = bankroll - allocated_bankroll
            stake = self.calculate_stake(
                bankroll=remaining,
                win_prob=opp['win_prob'],
                odds=opp['odds'],
                phase=phase,
                win_rate=win_rate
            )
            
            if stake >= self.min_bet_amount:
                opp['stake'] = stake
                selected.append(opp)
                allocated_bankroll += stake
                
                # Stop if we've allocated too much
                if allocated_bankroll >= bankroll * 0.25:  # Max 25% total exposure
                    break
                    
        return selected
        
    def simulate_growth(self,
                       initial_bankroll: float,
                       num_bets: int,
                       avg_win_prob: float,
                       avg_odds: float,
                       phase_distribution: Dict[str, float],
                       win_rate_by_phase: Dict[str, float]) -> Dict:
        """
        Simulate bankroll growth over multiple bets.
        
        Args:
            initial_bankroll: Starting bankroll
            num_bets: Number of bets to simulate
            avg_win_prob: Average win probability
            avg_odds: Average decimal odds
            phase_distribution: Probability of each phase
            win_rate_by_phase: Historical win rates by phase
            
        Returns:
            Simulation results including final bankroll and growth rate
        """
        bankroll = initial_bankroll
        results = []
        
        for i in range(num_bets):
            # Sample phase
            phase = np.random.choice(
                list(phase_distribution.keys()),
                p=list(phase_distribution.values())
            )
            
            # Add some variance to win probability and odds
            win_prob = np.clip(avg_win_prob + np.random.normal(0, 0.05), 0.3, 0.7)
            odds = max(1.5, avg_odds + np.random.normal(0, 0.2))
            
            # Calculate stake
            stake = self.calculate_stake(
                bankroll=bankroll,
                win_prob=win_prob,
                odds=odds,
                phase=phase,
                win_rate=win_rate_by_phase.get(phase, 0.52)
            )
            
            if stake > 0:
                # Simulate outcome
                won = np.random.random() < win_prob
                
                if won:
                    profit = stake * (odds - 1)
                    bankroll += profit
                else:
                    bankroll -= stake
                    
                results.append({
                    'bet_num': i + 1,
                    'phase': phase,
                    'stake': stake,
                    'won': won,
                    'bankroll': bankroll
                })
                
        # Calculate metrics
        total_staked = sum(r['stake'] for r in results)
        wins = sum(1 for r in results if r['won'])
        
        return {
            'initial_bankroll': initial_bankroll,
            'final_bankroll': bankroll,
            'total_return': (bankroll - initial_bankroll) / initial_bankroll,
            'num_bets': len(results),
            'win_rate': wins / len(results) if results else 0,
            'avg_stake': total_staked / len(results) if results else 0,
            'results': results
        }
        
    def get_phase_statistics(self) -> Dict:
        """Get current divisor configuration and statistics."""
        stats = {
            'mode': self.divisors.get('mode', 'static'),
            'phases': {}
        }
        
        for phase in self.static_divisors.keys():
            phase_stats = {
                'static_divisor': self.divisors.get('static_divisors', {}).get(phase, self.static_divisors[phase])
            }
            
            if self.divisors.get('mode') == 'dynamic':
                phase_stats['formula'] = self.divisors.get('dynamic_formulas', {}).get(phase, 'N/A')
                
                # Calculate divisor at different win rates
                phase_stats['divisor_curve'] = {}
                for wr in [0.45, 0.50, 0.52, 0.55, 0.60]:
                    phase_stats['divisor_curve'][f"{int(wr*100)}%"] = round(
                        self._evaluate_dynamic_divisor(phase, wr), 2
                    )
                    
            stats['phases'][phase] = phase_stats
            
        return stats


if __name__ == "__main__":
    # Example usage and testing
    optimizer = BankrollOptimizer()
    
    # Test basic Kelly calculation
    print("=== Basic Kelly Calculation ===")
    kelly = optimizer.calculate_kelly_fraction(
        win_prob=0.55,
        odds=2.0,
        phase='ovulatory'
    )
    print(f"Kelly fraction: {kelly:.4f}")
    
    # Test stake calculation
    print("\n=== Stake Calculation ===")
    stake = optimizer.calculate_stake(
        bankroll=1000,
        win_prob=0.55,
        odds=2.0,
        phase='ovulatory'
    )
    print(f"Recommended stake: ${stake:.2f}")
    
    # Test dynamic divisors
    print("\n=== Dynamic Divisor Testing ===")
    for phase in ['menstrual', 'follicular', 'ovulatory', 'luteal']:
        print(f"\n{phase.capitalize()} phase:")
        for win_rate in [0.45, 0.52, 0.58]:
            divisor = optimizer._evaluate_dynamic_divisor(phase, win_rate)
            print(f"  Win rate {win_rate:.0%}: divisor = {divisor:.2f}")
            
    # Show configuration
    print("\n=== Current Configuration ===")
    stats = optimizer.get_phase_statistics()
    print(json.dumps(stats, indent=2))
