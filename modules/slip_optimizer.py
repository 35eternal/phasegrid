"""
Enhanced slip optimizer with POWER and FLEX ticket support.
Uses beam search for efficient slip generation with positive EV constraint.
"""

import json
import itertools
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime
import pandas as pd
import numpy as np


class SlipOptimizer:
    """Generates optimal betting slips for both POWER and FLEX tickets."""
    
    def __init__(self, payout_config_path: Optional[Path] = None):
        """
        Initialize with payout configuration.
        
        Args:
            payout_config_path: Path to payout_tables.json (default: config/payout_tables.json)
        """
        if payout_config_path is None:
            payout_config_path = Path("config/payout_tables.json")
        
        self.payout_tables = self._load_payout_tables(payout_config_path)
        self.max_per_prop = 3  # Maximum times a prop can appear across all slips
        self.beam_width = 50  # Default beam width for search
    
    def _load_payout_tables(self, config_path: Path) -> Dict:
        """Load payout multipliers for POWER and FLEX tickets."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default payout structure
            print(f"Warning: {config_path} not found. Using default payouts.")
            return {
                "power": {
                    "3": 10.0,
                    "4": 20.0,
                    "5": 40.0,
                    "6": 100.0
                },
                "flex": {
                    "3_of_3": 5.0,
                    "3_of_4": 2.5,
                    "4_of_4": 10.0,
                    "4_of_5": 4.0,
                    "5_of_5": 20.0,
                    "5_of_6": 10.0,
                    "6_of_6": 40.0
                }
            }
    
    def calculate_power_ev(self, props: List[Dict]) -> float:
        """
        Calculate expected value for a POWER play ticket.
        
        Args:
            props: List of prop dictionaries with 'implied_prob' field
        
        Returns:
            Expected value as a decimal (e.g., 0.05 = 5%)
        """
        n_props = len(props)
        if n_props < 3 or n_props > 6:
            return -1.0  # Invalid POWER play size
        
        # Get payout multiplier
        payout = self.payout_tables["power"].get(str(n_props), 0)
        
        # Calculate probability of all props hitting
        combined_prob = np.prod([p["implied_prob"] for p in props])
        
        # EV = (payout * win_prob) - 1
        ev = (payout * combined_prob) - 1.0
        
        return ev
    
    def calculate_flex_ev(self, props: List[Dict]) -> float:
        """
        Calculate expected value for a FLEX play ticket.
        Uses tiered payouts based on number of hits.
        
        Args:
            props: List of prop dictionaries with 'implied_prob' field
        
        Returns:
            Expected value as a decimal
        """
        n_props = len(props)
        if n_props < 3 or n_props > 6:
            return -1.0  # Invalid FLEX play size
        
        total_ev = 0.0
        probs = [p["implied_prob"] for p in props]
        
        # Calculate probability of each outcome tier
        for n_hits in range(n_props, 1, -1):  # From all hits down to minimum
            # Get payout for this tier
            tier_key = f"{n_hits}_of_{n_props}"
            payout = self.payout_tables["flex"].get(tier_key, 0)
            
            if payout > 0:
                # Calculate probability of exactly n_hits
                hit_prob = 0.0
                for hit_indices in itertools.combinations(range(n_props), n_hits):
                    prob = 1.0
                    for i in range(n_props):
                        if i in hit_indices:
                            prob *= probs[i]
                        else:
                            prob *= (1 - probs[i])
                    hit_prob += prob
                
                # Add to total EV
                total_ev += payout * hit_prob
        
        # Subtract initial bet
        return total_ev - 1.0
    
    def generate_slips(self, props_df: pd.DataFrame, ticket_type: str = "power", 
                       target_slips: int = 10, beam_width: Optional[int] = None) -> List[Dict]:
        """
        Generate optimal betting slips using beam search.
        
        Args:
            props_df: DataFrame with columns: prop_id, player, type, line, implied_prob, phase
            ticket_type: "power" or "flex"
            target_slips: Target number of slips to generate
            beam_width: Beam width for search (default: self.beam_width)
        
        Returns:
            List of slip dictionaries with positive EV
        """
        if beam_width is None:
            beam_width = self.beam_width
        
        # Convert props to list of dicts for easier manipulation
        props = props_df.to_dict('records')
        
        # Track prop usage across all slips
        prop_usage = {p['prop_id']: 0 for p in props}
        
        # Calculate EV function based on ticket type
        calc_ev = self.calculate_power_ev if ticket_type == "power" else self.calculate_flex_ev
        
        slips = []
        
        # Generate slips until target reached or no more valid combinations
        while len(slips) < target_slips:
            # Filter available props (usage < max_per_prop)
            available_props = [p for p in props if prop_usage[p['prop_id']] < self.max_per_prop]
            
            if len(available_props) < 3:
                break  # Not enough props left
            
            # Use beam search to find best slip
            best_slip = self._beam_search_slip(available_props, calc_ev, beam_width)
            
            if best_slip is None or best_slip['ev'] <= 0:
                break  # No positive EV slips remaining
            
            # Update prop usage
            for prop in best_slip['props']:
                prop_usage[prop['prop_id']] += 1
            
            # Create slip dictionary
            slip = {
                'slip_id': f"{ticket_type.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(slips)+1:03d}",
                'ticket_type': ticket_type.upper(),
                'props': [prop.copy() for prop in best_slip['props']],  # Ensure list not tuple
                'ev': round(best_slip['ev'], 4),
                'n_props': len(best_slip['props'])
            }
            
            slips.append(slip)
        
        return slips
    
    def _beam_search_slip(self, available_props: List[Dict], calc_ev, beam_width: int) -> Optional[Dict]:
        """
        Use beam search to find the best slip combination.
        
        Returns:
            Dictionary with 'props' and 'ev' keys, or None if no positive EV found
        """
        # Start with empty beam
        beam = [{'props': [], 'ev': 0}]
        
        # Build slips incrementally
        for size in range(1, 7):  # Max 6 props per slip
            new_beam = []
            
            for state in beam:
                current_props = state['props']
                current_ids = {p['prop_id'] for p in current_props}
                
                # Get candidates that aren't already in slip
                candidates = [p for p in available_props if p['prop_id'] not in current_ids]
                
                # Try adding each candidate
                for prop in candidates:
                    new_props = current_props + [prop]
                    
                    # Calculate EV only for valid sizes
                    if size >= 3:
                        ev = calc_ev(new_props)
                        new_beam.append({'props': new_props, 'ev': ev})
                    else:
                        # For sizes < 3, just build combinations
                        new_beam.append({'props': new_props, 'ev': 0})
            
            # Keep top beam_width states by EV
            if size >= 3:
                new_beam.sort(key=lambda x: x['ev'], reverse=True)
            beam = new_beam[:beam_width]
            
            if not beam:
                break
        
        # Return best slip with positive EV
        valid_slips = [s for s in beam if s['ev'] > 0 and len(s['props']) >= 3]
        if valid_slips:
            return max(valid_slips, key=lambda x: x['ev'])
        
        return None
    
    def optimize_portfolio(self, props_df: pd.DataFrame, power_target: int = 5, 
                          flex_target: int = 5) -> Dict[str, List[Dict]]:
        """
        Generate optimized portfolio with both POWER and FLEX slips.
        
        Args:
            props_df: DataFrame with prop information
            power_target: Target number of POWER slips
            flex_target: Target number of FLEX slips
        
        Returns:
            Dictionary with 'power' and 'flex' keys containing slip lists
        """
        # Generate POWER slips first (typically higher EV)
        power_slips = self.generate_slips(props_df, "power", power_target)
        
        # Generate FLEX slips
        flex_slips = self.generate_slips(props_df, "flex", flex_target)
        
        return {
            'power': power_slips,
            'flex': flex_slips
        }


# Example usage
if __name__ == "__main__":
    # Create sample props data
    sample_props = pd.DataFrame({
        'prop_id': [f'P{i:03d}' for i in range(1, 21)],
        'player': [f'Player_{i}' for i in range(1, 21)],
        'type': ['points'] * 10 + ['rebounds'] * 10,
        'line': np.random.uniform(15, 30, 20),
        'implied_prob': np.random.uniform(0.45, 0.65, 20),
        'phase': np.random.choice(['follicular', 'ovulatory', 'luteal', 'menstrual'], 20)
    })
    
    # Initialize optimizer
    optimizer = SlipOptimizer()
    
    # Generate portfolio
    portfolio = optimizer.optimize_portfolio(sample_props, power_target=3, flex_target=3)
    
    print("Generated Portfolio:")
    print(f"POWER slips: {len(portfolio['power'])}")
    print(f"FLEX slips: {len(portfolio['flex'])}")
    
    # Show sample slip
    if portfolio['power']:
        slip = portfolio['power'][0]
        print(f"\nSample POWER slip: {slip['slip_id']}")
        print(f"EV: {slip['ev']:.2%}")
        print(f"Props: {slip['n_props']}")