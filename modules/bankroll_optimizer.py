"""
Phase-aware Kelly bankroll optimizer for WNBA betting.
Calculates optimal bet sizing based on expected value and menstrual phase.
"""

import json
from pathlib import Path
from typing import Dict, Optional


class BankrollOptimizer:
    """Manages phase-aware bankroll allocation using Kelly criterion."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize with phase Kelly divisors from config.
        
        Args:
            config_path: Path to phase_kelly_divisors.json (default: config/phase_kelly_divisors.json)
        """
        if config_path is None:
            config_path = Path("config/phase_kelly_divisors.json")
        
        self.phase_divisors = self._load_phase_divisors(config_path)
        self.min_bet = 0.0  # Will be loaded from settings
        self.max_bet_pct = 0.0  # Will be loaded from settings
    
    def _load_phase_divisors(self, config_path: Path) -> Dict[str, float]:
        """Load phase-specific Kelly divisors from JSON config."""
        try:
            with open(config_path, 'r') as f:
                raw_config = json.load(f)
            
            # Handle both simple numeric divisors and complex config objects
            divisors = {}
            for phase, config in raw_config.items():
                if isinstance(config, (int, float)):
                    # Simple numeric divisor
                    if config <= 0:
                        raise ValueError(f"Invalid divisor for phase {phase}: {config}")
                    divisors[phase] = float(config)
                elif isinstance(config, dict):
                    # Complex config with formula, use default divisor based on phase
                    # You can customize these defaults based on your strategy
                    default_divisors = {
                        "follicular": 4.0,
                        "ovulatory": 3.0,
                        "luteal": 5.0,
                        "menstrual": 6.0,
                        "unknown": 5.0
                    }
                    divisors[phase] = default_divisors.get(phase, 5.0)
                    print(f"Using default divisor {divisors[phase]} for phase {phase} (formula-based config detected)")
                else:
                    raise ValueError(f"Invalid config format for phase {phase}")
            
            return divisors
            
        except FileNotFoundError:
            # Default divisors if config not found
            print(f"Warning: {config_path} not found. Using default divisors.")
            return {
                "follicular": 4.0,
                "ovulatory": 3.0,
                "luteal": 5.0,
                "menstrual": 6.0,
                "unknown": 5.0
            }
    
    def set_constraints(self, min_bet: float, max_bet_pct: float):
        """
        Set betting constraints from settings.
        
        Args:
            min_bet: Minimum bet size in dollars
            max_bet_pct: Maximum bet as percentage of bankroll (0-1)
        """
        self.min_bet = max(0.0, min_bet)
        self.max_bet_pct = max(0.0, min(1.0, max_bet_pct))
    
    def size_bet(self, bankroll: float, ev: float, phase: str) -> float:
        """
        Calculate optimal bet size using phase-aware Kelly criterion.
        
        Args:
            bankroll: Current bankroll amount
            ev: Expected value of the bet (as decimal, e.g., 0.05 = 5%)
            phase: Menstrual phase ("follicular", "ovulatory", "luteal", "menstrual", "unknown")
        
        Returns:
            Recommended stake amount (rounded to 2 decimal places)
        """
        # Validate inputs
        if bankroll <= 0:
            return 0.0
        
        if ev <= 0:
            return 0.0  # Never bet on negative EV
        
        # Get phase divisor (default to 'unknown' if phase not recognized)
        divisor = self.phase_divisors.get(phase.lower(), self.phase_divisors.get("unknown", 5.0))
        
        # Calculate Kelly fraction: f = EV / divisor
        kelly_fraction = ev / divisor
        
        # Calculate raw stake
        raw_stake = bankroll * kelly_fraction
        
        # Apply max bet percentage constraint
        max_stake = bankroll * self.max_bet_pct
        stake = min(raw_stake, max_stake)
        
        # Apply minimum bet constraint
        if stake < self.min_bet:
            # If calculated stake is below minimum, don't bet
            return 0.0
        
        # Round to 2 decimal places
        return round(stake, 2)
    
    def calculate_kelly_fraction(self, ev: float, phase: str) -> float:
        """
        Calculate the Kelly fraction for a given EV and phase.
        Useful for debugging and analysis.
        
        Args:
            ev: Expected value of the bet
            phase: Menstrual phase
        
        Returns:
            Kelly fraction (before constraints)
        """
        divisor = self.phase_divisors.get(phase.lower(), self.phase_divisors.get("unknown", 5.0))
        return ev / divisor if ev > 0 else 0.0


# Example usage and testing
if __name__ == "__main__":
    # Initialize optimizer
    optimizer = BankrollOptimizer()
    
    # Set constraints (example values)
    optimizer.set_constraints(min_bet=5.0, max_bet_pct=0.10)
    
    # Test bet sizing
    test_cases = [
        (1000, 0.05, "follicular"),  # 5% EV in follicular phase
        (1000, 0.08, "ovulatory"),   # 8% EV in ovulatory phase
        (1000, 0.03, "luteal"),      # 3% EV in luteal phase
        (500, 0.02, "menstrual"),    # 2% EV in menstrual phase
        (2000, 0.15, "unknown"),     # 15% EV in unknown phase
    ]
    
    print("Phase-Aware Kelly Betting Examples:")
    print("-" * 60)
    for bankroll, ev, phase in test_cases:
        stake = optimizer.size_bet(bankroll, ev, phase)
        print(f"Bankroll: ${bankroll:,} | EV: {ev:.1%} | Phase: {phase:10} | Stake: ${stake}")