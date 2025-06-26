"""
Enhanced SlipProcessor with guard-rail enforcement and detailed logging.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .errors import InsufficientSlipsError, ConfigurationError
from .slip_optimizer import SlipOptimizer

logger = logging.getLogger(__name__)


class SlipProcessor:
    """Processes and validates slip generation with guard-rail enforcement."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.bypass_guard_rail = self.config.get('bypass_guard_rail', False)
        self.minimum_slips = int(os.getenv('MINIMUM_SLIPS_PER_DAY', '5'))
        self.slip_confidence_threshold = float(
            os.getenv('SLIP_CONFIDENCE_THRESHOLD', '0.75')
        )
        
        # Initialize optimizer with enhanced logging
        self.optimizer = SlipOptimizer({
            'confidence_threshold': self.slip_confidence_threshold,
            'enable_detailed_logging': True
        })
        
        logger.info(
            f"SlipProcessor initialized with threshold={self.slip_confidence_threshold}, "
            f"minimum_slips={self.minimum_slips}, bypass={self.bypass_guard_rail}"
        )
    
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
        
        if slip_count < self.minimum_slips and self.bypass_guard_rail:
            logger.warning(
                f"Guard-rail bypassed: {slip_count} slips < {self.minimum_slips} minimum"
            )
        
        return slips
    
    def set_bypass_guard_rail(self, bypass: bool) -> None:
        """Enable or disable guard-rail bypass."""
        self.bypass_guard_rail = bypass
        logger.info(f"Guard-rail bypass set to: {bypass}")
    
    def adjust_confidence_threshold(self, new_threshold: float) -> None:
        """
        Adjust the confidence threshold for slip generation.
        
        Args:
            new_threshold: New confidence threshold between 0.0 and 1.0
        """
        if not 0.0 <= new_threshold <= 1.0:
            raise ConfigurationError(
                f"Invalid confidence threshold: {new_threshold}"
            )
        
        old_threshold = self.slip_confidence_threshold
        self.slip_confidence_threshold = new_threshold
        self.optimizer.config['confidence_threshold'] = new_threshold
        self.optimizer.confidence_threshold = new_threshold
        
        logger.info(
            f"Adjusted confidence threshold: {old_threshold} -> {new_threshold}"
        )
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get statistics from the last optimization run."""
        return self.optimizer.get_last_run_stats()