"""
Slip optimization module with detailed logging.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SlipOptimizer:
    """Enhanced optimizer with detailed filtering logs."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.confidence_threshold = config.get('confidence_threshold', 0.75)
        self.enable_logging = config.get('enable_detailed_logging', False)
        self.last_run_stats = {}
    
    def optimize(self, props: List[Dict[str, Any]], date: str) -> List[Dict[str, Any]]:
        """Optimize props to generate slips with detailed logging."""
        self.last_run_stats = {
            'total_props': len(props),
            'filtered_by_confidence': 0,
            'filtered_by_edge': 0,
            'filtered_by_duplicate': 0,
            'filtered_by_validity': 0,
            'generated_slips': 0
        }
        
        slips = []
        seen_combinations = set()
        
        for prop in props:
            # Filter by confidence
            if prop.get('confidence', 0) < self.confidence_threshold:
                self._log_filter('confidence', prop)
                self.last_run_stats['filtered_by_confidence'] += 1
                continue
            
            # Filter edge cases
            if self._is_edge_case(prop):
                self._log_filter('edge', prop)
                self.last_run_stats['filtered_by_edge'] += 1
                continue
            
            # Filter duplicates
            combo_key = f"{prop.get('prop_id')}:{prop.get('value')}"
            if combo_key in seen_combinations:
                self._log_filter('duplicate', prop)
                self.last_run_stats['filtered_by_duplicate'] += 1
                continue
            
            # Validate prop structure
            if not self._is_valid_prop(prop):
                self._log_filter('validity', prop)
                self.last_run_stats['filtered_by_validity'] += 1
                continue
            
            # Generate slip
            slip = self._create_slip(prop, date)
            slips.append(slip)
            seen_combinations.add(combo_key)
            self.last_run_stats['generated_slips'] += 1
        
        logger.info(f"Optimization stats: {self.last_run_stats}")
        return slips
    
    def _log_filter(self, reason: str, prop: Dict[str, Any]) -> None:
        """Log why a prop was filtered."""
        if self.enable_logging:
            logger.debug(
                f"Filtered prop {prop.get('prop_id')} - "
                f"reason: {reason}, confidence: {prop.get('confidence', 0)}"
            )
    
    def _is_edge_case(self, prop: Dict[str, Any]) -> bool:
        """Check if prop represents an edge case."""
        # Edge cases: extreme values, suspicious patterns
        value = prop.get('value', 0)
        if isinstance(value, (int, float)):
            if value < -1000000 or value > 1000000:
                return True
        
        # Check for test/demo props
        prop_id = prop.get('prop_id', '')
        if any(pattern in prop_id.lower() for pattern in ['test', 'demo', 'sample']):
            return True
        
        return False
    
    def _is_valid_prop(self, prop: Dict[str, Any]) -> bool:
        """Validate prop has required structure."""
        required_fields = ['prop_id', 'confidence', 'value', 'timestamp']
        return all(field in prop for field in required_fields)
    
    def _create_slip(self, prop: Dict[str, Any], date: str) -> Dict[str, Any]:
        """Create a slip from a validated prop."""
        return {
            'slip_id': f"SLIP-{prop['prop_id']}-{date}",
            'prop_id': prop['prop_id'],
            'value': prop['value'],
            'confidence': prop['confidence'],
            'date': date,
            'timestamp': prop['timestamp'],
            'source': prop.get('source', 'unknown'),
            'created_at': datetime.now().isoformat()
        }
    
    def get_last_run_stats(self) -> Dict[str, Any]:
        """Get statistics from the last optimization run."""
        return self.last_run_stats.copy()