#!/usr/bin/env python3
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    )
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if args.days < 1:
        logger.error("❌ Days must be at least 1")
        sys.exit(1)
    
    if args.days > 30:
        response = input(f"⚠️  You're about to backfill {args.days} days. "
                        f"This might take a while and cost API calls. Continue? (y/n): ")
        if response.lower() != 'y':
            logger.info("Cancelled by user")
            sys.exit(0)
    
    # Run backfill
    try:
        backfill_slips(args.days, force=args.force)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Backfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
