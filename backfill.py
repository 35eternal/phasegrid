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
from typing import List, Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_paper import EnhancedAutoPaper
from scripts.result_grader import EnhancedResultGrader
=======
"""Backfill historical slips for PhaseGrid."""

import argparse
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slips_generator import generate_slips
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
>>>>>>> 0dbb3630d4f4e32159e9c021f803b927a71d2293

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

<<<<<<< HEAD

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
=======
class SheetManager:
    """Manages Google Sheets operations for backfill."""
    
    def __init__(self):
        """Initialize Google Sheets connection."""
        self.sheet_id = os.environ.get('SHEET_ID')
        google_sa_json = os.environ.get('GOOGLE_SA_JSON')
        
        if not self.sheet_id or not google_sa_json:
            raise ValueError("Missing SHEET_ID or GOOGLE_SA_JSON environment variables")
        
        # Parse credentials
        if os.path.exists(google_sa_json):
            self.credentials = service_account.Credentials.from_service_account_file(
                google_sa_json,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        else:
            service_account_info = json.loads(google_sa_json)
            self.credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        
        self.service = build('sheets', 'v4', credentials=self.credentials)
        self.sheet = self.service.spreadsheets()
    
    def get_existing_slip_ids(self, worksheet: str = 'paper_slips') -> set:
        """Get all existing slip IDs to avoid duplicates."""
        try:
            # Read the slip_id column (assuming it's column A)
            range_name = f'{worksheet}!A:A'
            result = self.sheet.values().get(
                spreadsheetId=self.sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Extract slip IDs (skip header)
            slip_ids = set()
            for row in values[1:]:  # Skip header row
                if row and row[0]:  # Check if cell is not empty
                    slip_ids.add(row[0])
            
            logger.info(f"Found {len(slip_ids)} existing slips in sheet")
            return slip_ids
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Worksheet '{worksheet}' not found, will create new slips")
                return set()
            else:
                logger.error(f"Error reading sheet: {e}")
                raise
    
    def append_slips(self, slips: List[Dict[str, Any]], worksheet: str = 'paper_slips') -> int:
        """Append new slips to the sheet."""
        if not slips:
            return 0
        
        try:
            # Get headers from first slip
            headers = list(slips[0].keys())
            
            # Convert slips to rows
            rows = []
            for slip in slips:
                row = [str(slip.get(header, '')) for header in headers]
                rows.append(row)
            
            # Append to sheet
            range_name = f'{worksheet}!A1'
            body = {
                'values': rows
            }
            
            result = self.sheet.values().append(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updated_cells = result.get('updates', {}).get('updatedCells', 0)
            logger.info(f"Added {len(slips)} slips ({updated_cells} cells updated)")
            
            return len(slips)
            
        except HttpError as e:
            logger.error(f"Error appending to sheet: {e}")
            raise

def backfill_slips(days: int, force: bool = False):
    """
    Generate and push slips for the past N days.
    
    Args:
        days: Number of days to backfill
        force: If True, regenerate even if slips exist
    """
    logger.info(f"🚀 Starting backfill for {days} days")
    
    # Initialize sheet manager
    sheet_manager = SheetManager()
    
    # Get existing slip IDs unless forcing regeneration
    existing_ids = set() if force else sheet_manager.get_existing_slip_ids()
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Statistics
    total_generated = 0
    total_added = 0
    total_skipped = 0
    slips_by_date = {}
    
    # Process each day
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        logger.info(f"\n📆 Processing {date_str}")
        
        try:
            # Generate slips for this date
            daily_slips = generate_slips(date_str, date_str)
            total_generated += len(daily_slips)
            
            # Filter out existing slips
            new_slips = []
            for slip in daily_slips:
                if slip['slip_id'] not in existing_ids:
                    new_slips.append(slip)
                    slip['backfilled'] = True  # Mark as backfilled
                    slip['backfill_date'] = datetime.now().isoformat()
                else:
                    total_skipped += 1
                    logger.debug(f"⏭️  Skipping existing slip: {slip['slip_id']}")
            
            # Store for batch processing
            if new_slips:
                slips_by_date[date_str] = new_slips
                logger.info(f"✅ Generated {len(new_slips)} new slips for {date_str}")
            else:
                logger.info(f"ℹ️  No new slips for {date_str} (all exist)")
            
        except Exception as e:
            logger.error(f"❌ Error processing {date_str}: {e}")
        
        current_date += timedelta(days=1)
    
    # Batch append all new slips
    logger.info("\n📤 Uploading slips to Google Sheets...")
    
    all_new_slips = []
    for date, slips in sorted(slips_by_date.items()):
        all_new_slips.extend(slips)
    
    if all_new_slips:
        try:
            added = sheet_manager.append_slips(all_new_slips)
            total_added = added
        except Exception as e:
            logger.error(f"Failed to upload slips: {e}")
            # Try uploading day by day as fallback
            for date, slips in sorted(slips_by_date.items()):
                try:
                    added = sheet_manager.append_slips(slips)
                    total_added += added
                except Exception as e:
                    logger.error(f"Failed to upload slips for {date}: {e}")
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("🏁 BACKFILL COMPLETE!")
    logger.info(f"📊 Summary:")
    logger.info(f"  • Days processed: {days}")
    logger.info(f"  • Total generated: {total_generated}")
    logger.info(f"  • New slips added: {total_added}")
    logger.info(f"  • Existing skipped: {total_skipped}")
    logger.info(f"  • Success rate: {(total_added/total_generated*100) if total_generated > 0 else 0:.1f}%")
    logger.info("="*50)
    
    # Send alert if configured
    try:
        from alert_manager import AlertManager
        alert_manager = AlertManager()
        alert_manager._send_discord_alert(
            f"📊 Backfill Complete!\n\n"
            f"• Days: {days}\n"
            f"• Added: {total_added} slips\n"
            f"• Skipped: {total_skipped} existing",
            color=0x00FF00
        )
    except:
        pass  # Alerts are optional

def main():
    """Main entry point for backfill script."""
    parser = argparse.ArgumentParser(
        description='Backfill historical slips for PhaseGrid',
        epilog='Example: python backfill.py --days 7'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        required=True,
        help='Number of days to backfill (e.g., 7 for last week)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration even if slips already exist'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
>>>>>>> 0dbb3630d4f4e32159e9c021f803b927a71d2293
    )
    
    args = parser.parse_args()
    
<<<<<<< HEAD
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
    from typing import Optional
    sys.exit(main())