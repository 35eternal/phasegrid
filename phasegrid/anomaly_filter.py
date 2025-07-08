"""
Anomaly filter for PrizePicks Demons and Goblins.

Demons: Higher projections (harder to hit, higher payouts)
Goblins: Lower projections (easier to hit, lower payouts)

This module filters out these alternate lines to keep only standard projections.
"""
import logging
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnomalyFilter:
    """Filter out PrizePicks Demons and Goblins (alternate projection lines)."""
    
    def __init__(self, tolerance_percentage: float = 15.0):
        """
        Initialize the anomaly filter.
        
        Args:
            tolerance_percentage: Percentage difference to identify demons/goblins
                                (default 15% - if lines differ by >15%, they're likely alternates)
        """
        self.tolerance_percentage = tolerance_percentage
        
    def filter_anomalies(self, slips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out Demon and Goblin projections, keeping only standard lines.
        
        Args:
            slips: List of slip dictionaries from PrizePicks
            
        Returns:
            List of filtered slips with only standard projections
        """
        if not slips:
            return slips
            
        # Group slips by player + prop_type
        grouped_slips = defaultdict(list)
        for slip in slips:
            key = (slip['player'], slip['prop_type'])
            grouped_slips[key].append(slip)
        
        filtered_slips = []
        demons_filtered = 0
        goblins_filtered = 0
        
        for (player, prop_type), group in grouped_slips.items():
            if len(group) == 1:
                # Only one projection, it's standard
                filtered_slips.append(group[0])
            else:
                # Multiple projections for same player/prop - likely includes demons/goblins
                # Sort by line value
                sorted_group = sorted(group, key=lambda x: x['line'])
                
                if len(sorted_group) == 2:
                    # Two projections - keep the one that's not extreme
                    # Check if they differ significantly
                    line_diff_pct = abs(sorted_group[1]['line'] - sorted_group[0]['line']) / sorted_group[0]['line'] * 100
                    
                    if line_diff_pct > self.tolerance_percentage:
                        # Significant difference, likely demon/goblin
                        # In a 2-projection scenario, we'd need more context to decide
                        # For now, keep the lower one (more conservative)
                        filtered_slips.append(sorted_group[0])
                        logger.info(f"Filtered potential demon: {player} {prop_type} "
                                  f"({sorted_group[1]['line']} vs {sorted_group[0]['line']})")
                        demons_filtered += 1
                    else:
                        # Not significantly different, keep both
                        filtered_slips.extend(sorted_group)
                        
                elif len(sorted_group) >= 3:
                    # Three or more projections - middle one is likely standard
                    middle_idx = len(sorted_group) // 2
                    standard_slip = sorted_group[middle_idx]
                    filtered_slips.append(standard_slip)
                    
                    # Log what we filtered
                    logger.info(f"Filtered demons/goblins for {player} {prop_type}: "
                              f"keeping {standard_slip['line']}, "
                              f"removing {[s['line'] for i, s in enumerate(sorted_group) if i != middle_idx]}")
                    
                    # Count filtered items
                    goblins_filtered += middle_idx  # Lower lines
                    demons_filtered += len(sorted_group) - middle_idx - 1  # Higher lines
        
        logger.info(f"Anomaly filter results: {len(slips)} input slips, "
                   f"{len(filtered_slips)} output slips "
                   f"({demons_filtered} demons filtered, {goblins_filtered} goblins filtered)")
        
        return filtered_slips
    
    def identify_anomaly_type(self, slips_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify which slips are demons, goblins, or standard.
        
        Args:
            slips_group: List of slips for the same player/prop_type
            
        Returns:
            Dictionary mapping slip IDs to their types
        """
        if len(slips_group) < 2:
            return {slips_group[0]['slip_id']: 'standard'}
            
        sorted_slips = sorted(slips_group, key=lambda x: x['line'])
        
        # Calculate line differences
        result = {}
        
        if len(sorted_slips) == 2:
            line_diff_pct = abs(sorted_slips[1]['line'] - sorted_slips[0]['line']) / sorted_slips[0]['line'] * 100
            if line_diff_pct > self.tolerance_percentage:
                result[sorted_slips[0]['slip_id']] = 'goblin'
                result[sorted_slips[1]['slip_id']] = 'demon'
            else:
                result[sorted_slips[0]['slip_id']] = 'standard'
                result[sorted_slips[1]['slip_id']] = 'standard'
        else:
            # For 3+ slips, lowest is goblin, highest is demon, middle is standard
            for i, slip in enumerate(sorted_slips):
                if i == 0:
                    result[slip['slip_id']] = 'goblin'
                elif i == len(sorted_slips) - 1:
                    result[slip['slip_id']] = 'demon'
                else:
                    result[slip['slip_id']] = 'standard'
                    
        return result
