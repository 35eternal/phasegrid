"""
PhaseGrid CLI with guard-rail bypass option.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Optional

from .slip_processor import SlipProcessor
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
        '--confidence-threshold',
        type=float,
        default=None,
        help=f'Override confidence threshold for slip generation. '
             f'Default: {os.getenv("SLIP_CONFIDENCE_THRESHOLD", "0.75")} '
             f'(range: 0.0-1.0, lower = more slips)'
    )
    process_parser.add_argument(
        '--input-file',
        type=str,
        default='props.json',
        help='Input file containing props to process'
    )
    process_parser.add_argument(
        '--output-file',
        type=str,
        default='slips.json',
        help='Output file for generated slips'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser(
        'stats',
        help='Display slip generation statistics'
    )
    stats_parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Date to display stats for (YYYY-MM-DD)'
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        'config',
        help='Display current configuration'
    )
    
    # Global options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    
    return parser


def process_command(args):
    """Handle the process command."""
    import json
    
    # Load configuration
    config = {
        'bypass_guard_rail': args.bypass_guard_rail
    }
    
    # Initialize processor
    processor = SlipProcessor(config)
    
    # Override confidence threshold if specified
    if args.confidence_threshold is not None:
        processor.adjust_confidence_threshold(args.confidence_threshold)
    
    # Load props from input file
    try:
        with open(args.input_file, 'r') as f:
            props = json.load(f)
    except FileNotFoundError:
        logging.error(f"Input file not found: {args.input_file}")
        return 1
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in input file: {e}")
        return 1
    
    # Process props
    try:
        slips = processor.process(props, args.date)
        logging.info(f"Successfully generated {len(slips)} slips")
        
        # Save slips to output file
        with open(args.output_file, 'w') as f:
            json.dump(slips, f, indent=2)
        
        # Display statistics
        stats = processor.get_optimization_stats()
        print(f"\nSlip Generation Summary:")
        print(f"  Total props processed: {stats['total_props']}")
        print(f"  Slips generated: {stats['generated_slips']}")
        print(f"  Filtered by confidence: {stats['filtered_by_confidence']}")
        print(f"  Filtered by edge cases: {stats['filtered_by_edge']}")
        print(f"  Filtered by duplicates: {stats['filtered_by_duplicate']}")
        print(f"  Filtered by validity: {stats['filtered_by_validity']}")
        print(f"\nSlips saved to: {args.output_file}")
        
        return 0
        
    except InsufficientSlipsError as e:
        logging.error(str(e))
        print(f"\nERROR: {e}")
        print("\nTo bypass this check, use the --bypass-guard-rail flag")
        print("Warning: Bypassing may result in incomplete data processing")
        return 1
    except PhaseGridError as e:
        logging.error(f"Processing error: {e}")
        return 1


def stats_command(args):
    """Handle the stats command."""
    # TODO: Implement statistics retrieval
    print(f"Statistics for date: {args.date or 'today'}")
    print("Feature not yet implemented")
    return 0


def config_command(args):
    """Handle the config command."""
    print("Current PhaseGrid Configuration:")
    print(f"  SLIP_CONFIDENCE_THRESHOLD: {os.getenv('SLIP_CONFIDENCE_THRESHOLD', '0.75')}")
    print(f"  MINIMUM_SLIPS_PER_DAY: {os.getenv('MINIMUM_SLIPS_PER_DAY', '5')}")
    print(f"  LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO')}")
    print(f"  ENABLE_DETAILED_SLIP_LOGGING: {os.getenv('ENABLE_DETAILED_SLIP_LOGGING', 'true')}")
    return 0


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Handle commands
    if args.command == 'process':
        return process_command(args)
    elif args.command == 'stats':
        return stats_command(args)
    elif args.command == 'config':
        return config_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())