"""
Slip processing module with guard-rail enforcement.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from .slip_optimizer import SlipOptimizer
from .errors import InsufficientSlipsError

logger = logging.getLogger(__name__)


class SlipProcessor:
    """Process props and generate slips with guard-rail enforcement."""
    
    def __init__(self, 
                 minimum_slips: int = 5,
                 bypass_guard_rail: bool = False):
        """
        Initialize slip processor.
        
        Args:
            minimum_slips: Minimum number of slips required per day
            bypass_guard_rail: Whether to bypass minimum slip requirement
        """
        self.minimum_slips = minimum_slips
        self.bypass_guard_rail = bypass_guard_rail
        self.optimizer = SlipOptimizer()
        logger.info(f"Initialized SlipProcessor (bypass_guard_rail={bypass_guard_rail})")
    
    def process(self,
                props: List[Dict[str, Any]],
                date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process props and generate slips with guard-rail enforcement.
        
        Args:
            props: List of property dictionaries to process
            date: Target date for slip generation
            
        Returns:
            List of generated slips
            
        Raises:
            InsufficientSlipsError: If slip count < minimum and guard-rail not bypassed
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        logger.info(f"Processing {len(props)} props for date {date}")
        
        # Generate slips with detailed logging
        slips = self.optimizer.optimize(props, date)
        slip_count = len(slips)
        
        logger.info(f"Generated {slip_count} slips after optimization")
        
        # Enforce guard-rail unless bypassed
        if slip_count < self.minimum_slips and not self.bypass_guard_rail:
            logger.error(
                f"Guard-rail violation: {slip_count} slips < {self.minimum_slips} minimum"
            )
            raise InsufficientSlipsError(slip_count, self.minimum_slips)
            
        if self.bypass_guard_rail and slip_count < self.minimum_slips:
            logger.warning(
                f"Guard-rail bypassed: {slip_count} slips < {self.minimum_slips} minimum"
            )
            
        return slips
    
    def validate_props(self, props: List[Dict[str, Any]]) -> List[str]:
        """
        Validate input props for required fields.
        
        Args:
            props: List of props to validate
            
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        required_fields = ['player_id', 'market', 'line', 'odds']
        
        for i, prop in enumerate(props):
            for field in required_fields:
                if field not in prop:
                    errors.append(f"Prop {i}: Missing required field '{field}'")
                    
        return errors
    
    def generate_slip_metadata(self, slip: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for a slip."""
        return {
            'generated_at': datetime.now().isoformat(),
            'processor_version': '1.0.0',
            'guard_rail_bypassed': self.bypass_guard_rail,
            **slip
        }
    
    def batch_process(self, 
                     props_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Process props for multiple dates."""
        results = {}
        
        for date, props in props_by_date.items():
            try:
                results[date] = self.process(props, date)
            except InsufficientSlipsError as e:
                logger.error(f"Failed to process {date}: {e}")
                if not self.bypass_guard_rail:
                    raise
                results[date] = []  # Empty list if bypassed
                
        return results
