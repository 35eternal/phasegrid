#!/usr/bin/env python3
"""
Historical Backfill Script for PhaseGrid
Backfills historical data for specified number of days
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_paper import EnhancedAutoPaper
from scripts.result_grader import EnhancedResultGrader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HistoricalBackfill:
    """Handles historical data backfilling"""
    
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
        self.results = {
            'total_days': 0,
            'successful_days': 0,
            'failed_days': 0,
            'total_slips': 0,
            'total_graded': 0,
            'errors': []
        }
    
    def backfill_day(self, date: str, generate_slips: bool = True, grade_slips: bool = True) -> Dict:
        """Backfill data for a specific day"""
        logger.info(f"\n{'=' * 50}")
        logger.info(f"📅 Backfilling date: {date}")
        logger.info(f"{'=' * 50}")
        
        day_results = {
            'date': date,
            'slips_generated': 0,
            'slips_graded': 0,
            'errors': []
        }
        
        try:
            # Step 1: Generate slips for the day
            if generate_slips:
                logger.info("📝 Generating slips...")
                auto_paper = EnhancedAutoPaper(
                    sheet_id=self.sheet_id,
                    dry_run=False  # Historical data is not dry-run
                )
                
                # Override the date in slips generator
                original_date = os.environ.get('OVERRIDE_DATE')
                os.environ['OVERRIDE_DATE'] = date
                
                try:
                    result = auto_paper.run(fetch_live=False)  # No live data for historical
                    day_results['slips_generated'] = result.get('new_slips', 0)
                    logger.info(f"✅ Generated {day_results['slips_generated']} slips")
                except Exception as e:
                    logger.error(f"Failed to generate slips: {e}")
                    day_results['errors'].append(f"Generation error: {str(e)}")
                finally:
                    # Restore original date
                    if original_date:
                        os.environ['OVERRIDE_DATE'] = original_date
                    else:
                        os.environ.pop('OVERRIDE_DATE', None)
            
            # Step 2: Grade slips for the day
            if grade_slips and day_results['slips_generated'] > 0:
                logger.info("📊 Grading slips...")
                grader = EnhancedResultGrader(date=date)
                
                try:
                    grader.run()
                    # Get grading stats (would need to modify grader to return these)
                    day_results['slips_graded'] = day_results['slips_generated']
                    logger.info(f"✅ Graded {day_results['slips_graded']} slips")
                except Exception as e:
                    logger.error(f"Failed to grade slips: {e}")
                    day_results['errors'].append(f"Grading error: {str(e)}")
            
            # Mark as successful if no errors
            if not day_results['errors']:
                logger.info(f"✅ Successfully backfilled {date}")
                return day_results
            else:
                logger.error(f"❌ Backfill completed with errors for {date}")
                return day_results
                
        except Exception as e:
            logger.error(f"💥 Critical error backfilling {date}: {e}")
            day_results['errors'].append(f"Critical error: {str(e)}")
            return day_results
    
    def backfill_range(self, days: int, end_date: Optional[str] = None, 
                      generate_slips: bool = True, grade_slips: bool = True) -> Dict:
        """Backfill data for a range of days"""
        # Calculate date range
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end = datetime.now().date() - timedelta(days=1)  # Default to yesterday
        
        start = end - timedelta(days=days-1)
        
        logger.info(f"\n{'#' * 60}")
        logger.info(f"🚀 HISTORICAL BACKFILL")
        logger.info(f"📅 Date range: {start} to {end} ({days} days)")
        logger.info(f"📝 Generate slips: {generate_slips}")
        logger.info(f"📊 Grade slips: {grade_slips}")
        logger.info(f"{'#' * 60}\n")
        
        # Process each day
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            
            try:
                day_results = self.backfill_day(
                    date_str, 
                    generate_slips=generate_slips,
                    grade_slips=grade_slips
                )
                
                # Update totals
                self.results['total_days'] += 1
                self.results['total_slips'] += day_results['slips_generated']
                self.results['total_graded'] += day_results['slips_graded']
                
                if day_results['errors']:
                    self.results['failed_days'] += 1
                    self.results['errors'].extend([
                        f"{date_str}: {err}" for err in day_results['errors']
                    ])
                else:
                    self.results['successful_days'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to process {date_str}: {e}")
                self.results['failed_days'] += 1
                self.results['errors'].append(f"{date_str}: {str(e)}")
            
            current_date += timedelta(days=1)
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    def _print_summary(self):
        """Print backfill summary"""
        logger.info(f"\n{'#' * 60}")
        logger.info("📊 BACKFILL SUMMARY")
        logger.info(f"{'#' * 60}")
        logger.info(f"📅 Total days processed: {self.results['total_days']}")
        logger.info(f"✅ Successful days: {self.results['successful_days']}")
        logger.info(f"❌ Failed days: {self.results['failed_days']}")
        logger.info(f"📝 Total slips generated: {self.results['total_slips']}")
        logger.info(f"📊 Total slips graded: {self.results['total_graded']}")
        
        if self.results['errors']:
            logger.info(f"\n⚠️ Errors encountered:")
            for error in self.results['errors'][:10]:  # Show first 10 errors
                logger.error(f"  - {error}")
            if len(self.results['errors']) > 10:
                logger.error(f"  ... and {len(self.results['errors']) - 10} more errors")
        
        logger.info(f"{'#' * 60}\n")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Backfill historical data for PhaseGrid",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backfill last 7 days
  python backfill.py --days 7
  
  # Backfill 30 days ending on specific date
  python backfill.py --days 30 --end-date 2024-12-31
  
  # Only generate slips without grading
  python backfill.py --days 14 --no-grade
  
  # Only grade existing slips without generating new ones
  python backfill.py --days 7 --no-generate
        """
    )
    
    parser.add_argument(
        '--days', '-d',
        type=int,
        required=True,
        help='Number of days to backfill'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for backfill (YYYY-MM-DD), defaults to yesterday'
    )
    
    parser.add_argument(
        '--no-generate',
        action='store_true',
        help='Skip slip generation (only grade existing slips)'
    )
    
    parser.add_argument(
        '--no-grade',
        action='store_true',
        help='Skip grading (only generate slips)'
    )
    
    parser.add_argument(
        '--sheet-id',
        type=str,
        help='Google Sheet ID (overrides SHEET_ID env var)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.no_generate and args.no_grade:
        parser.error("Cannot use both --no-generate and --no-grade")
    
    if args.days < 1:
        parser.error("Days must be at least 1")
    
    if args.days > 365:
        response = input(f"⚠️ You're about to backfill {args.days} days. Continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Backfill cancelled")
            return 0
    
    # Get sheet ID
    sheet_id = args.sheet_id or os.environ.get('SHEET_ID')
    if not sheet_id:
        logger.error("Missing SHEET_ID (use --sheet-id or set SHEET_ID env var)")
        return 1
    
    # Run backfill
    try:
        backfiller = HistoricalBackfill(sheet_id)
        results = backfiller.backfill_range(
            days=args.days,
            end_date=args.end_date,
            generate_slips=not args.no_generate,
            grade_slips=not args.no_grade
        )
        
        # Return non-zero exit code if there were failures
        return 1 if results['failed_days'] > 0 else 0
        
    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())