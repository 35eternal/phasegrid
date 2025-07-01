"""
PhaseGrid CLI with guard-rail bypass option.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

from .slip_processor import SlipProcessor
from .slip_optimizer import SlipOptimizer
from .verify_sheets import SheetVerifier
from .errors import InsufficientSlipsError, PhaseGridError


def setup_logging(level: str = 'INFO'):
    """Configure logging for CLI."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description='PhaseGrid - Slip Generation and Processing System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Global arguments
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level'
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Process command
    process_parser = subparsers.add_parser(
        'process',
        help='Process props and generate slips'
    )
    process_parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Target date for slip generation (YYYY-MM-DD). Default: today'
    )
    process_parser.add_argument(
        '--bypass-guard-rail',
        action='store_true',
        help='Bypass the minimum slip count requirement (default: 5 slips/day)'
    )
    process_parser.add_argument(
        '--props-file',
        type=str,
        help='Path to props JSON file'
    )
    process_parser.add_argument(
        '--output',
        type=str,
        default='slips.json',
        help='Output file for generated slips'
    )

    # Verify command
    verify_parser = subparsers.add_parser(
        'verify',
        help='Verify sheets data integrity'
    )
    verify_parser.add_argument(
        '--sheet',
        type=str,
        required=True,
        help='Sheet name to verify'
    )
    verify_parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix validation errors'
    )

    # Optimize command
    optimize_parser = subparsers.add_parser(
        'optimize',
        help='Optimize slip generation parameters'
    )
    optimize_parser.add_argument(
        '--bankroll',
        type=float,
        default=1000.0,
        help='Total bankroll for optimization'
    )
    optimize_parser.add_argument(
        '--risk-level',
        type=str,
        choices=['conservative', 'moderate', 'aggressive'],
        default='moderate',
        help='Risk level for optimization'
    )

    return parser


def process_data(props: List[Dict[str, Any]], 
                 date: Optional[str] = None,
                 bypass_guard_rail: bool = False) -> List[Dict[str, Any]]:
    """Process props data and generate slips."""
    processor = SlipProcessor()
    if bypass_guard_rail:
        processor.bypass_guard_rail = True
    
    return processor.process(props, date)


def verify_sheets(sheet_name: str, fix: bool = False) -> bool:
    """Verify sheet data integrity."""
    verifier = SheetVerifier()
    errors = verifier.verify_sheet(sheet_name)
    
    if errors:
        print(f"Found {len(errors)} validation errors in {sheet_name}")
        for error in errors:
            print(f"  - {error}")
        
        if fix:
            print("Attempting to fix errors...")
            # Implementation for fixing errors
            pass
        return False
    
    print(f"Sheet {sheet_name} passed all validations!")
    return True


def optimize_slips(bankroll: float, risk_level: str) -> Dict[str, Any]:
    """Optimize slip generation parameters."""
    optimizer = SlipOptimizer()
    
    # Set parameters based on risk level
    if risk_level == 'conservative':
        max_bet_pct = 0.02
        min_edge = 0.10
    elif risk_level == 'aggressive':
        max_bet_pct = 0.10
        min_edge = 0.03
    else:  # moderate
        max_bet_pct = 0.05
        min_edge = 0.05
    
    params = {
        'bankroll': bankroll,
        'max_bet_pct': max_bet_pct,
        'min_edge': min_edge,
        'risk_level': risk_level
    }
    
    print(f"Optimization parameters for {risk_level} strategy:")
    print(f"  Bankroll: ${bankroll}")
    print(f"  Max bet percentage: {max_bet_pct * 100}%")
    print(f"  Minimum edge required: {min_edge * 100}%")
    
    return params


def process_command(args: argparse.Namespace):
    """Process the command based on parsed arguments."""
    if args.command == 'process':
        # Load props
        if args.props_file:
            import json
            with open(args.props_file, 'r') as f:
                props = json.load(f)
        else:
            props = []
        
        try:
            slips = process_data(props, args.date, args.bypass_guard_rail)
            print(f"Generated {len(slips)} slips")
            
            # Save output
            import json
            with open(args.output, 'w') as f:
                json.dump(slips, f, indent=2)
                
        except InsufficientSlipsError as e:
            print(f"Error: {e}")
            sys.exit(1)
            
    elif args.command == 'verify':
        success = verify_sheets(args.sheet, args.fix)
        sys.exit(0 if success else 1)
        
    elif args.command == 'optimize':
        params = optimize_slips(args.bankroll, args.risk_level)
        # Could save params to a config file here
        
    else:
        print("No command specified. Use --help for usage information.")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Process the command
    process_command(args)


if __name__ == '__main__':
    main()