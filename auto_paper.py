#!/usr/bin/env python3
"""
Enhanced Auto Paper Script for PhaseGrid
Generates slips with unique IDs and integrates with PrizePicks API
"""

import os
import sys
import uuid
import datetime
import json
import logging
import time
from typing import List, Dict, Optional
from functools import wraps

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odds_provider.prizepicks import PrizePicksClient
from slips_generator import generate_slips


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def exponential_backoff_retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for exponential backoff with jitter"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (HttpError, Exception) as e:
                    last_exception = e
                    
                    # Don't retry on 4xx errors (except 429)
                    if isinstance(e, HttpError) and 400 <= e.resp.status < 500 and e.resp.status != 429:
                        raise
                    
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = delay * 0.1 * (0.5 - time.time() % 1)  # Add 10% jitter
                    actual_delay = delay + jitter
                    
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {actual_delay:.2f}s: {str(e)}")
                    time.sleep(actual_delay)
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class EnhancedAutoPaper:
    """Enhanced auto paper generator with production features"""
    
    def __init__(self, sheet_id: str, dry_run: bool = True):
        self.sheet_id = sheet_id
        self.dry_run = dry_run
        self.sheet_service = None
        self.prizepicks_client = PrizePicksClient()
        self.batch_id = str(uuid.uuid4())
        
    def initialize_sheets(self):
        """Initialize Google Sheets service with retry logic"""
        try:
            google_sa_json = os.environ.get('GOOGLE_SA_JSON')
            if not google_sa_json:
                raise ValueError("Missing GOOGLE_SA_JSON environment variable")
            
            # Parse credentials
            if os.path.exists(google_sa_json):
                credentials = service_account.Credentials.from_service_account_file(
                    google_sa_json,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                service_account_info = json.loads(google_sa_json)
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            
            self.sheet_service = build('sheets', 'v4', credentials=credentials)
            logger.info("✅ Google Sheets service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            raise
    
    def generate_slip_id(self, slip_data: Dict) -> str:
        """Generate unique slip ID"""
        # Create deterministic ID based on slip content
        components = [
            slip_data.get('player', ''),
            slip_data.get('prop_type', ''),
            str(slip_data.get('line', '')),
            slip_data.get('game_id', ''),
            datetime.datetime.now().strftime('%Y%m%d')
        ]
        
        # Use first 8 chars of UUID5 for shorter IDs
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, 'phasegrid.com')
        slip_uuid = uuid.uuid5(namespace, '|'.join(components))
        
        return f"PG_{slip_uuid.hex[:8].upper()}"
    
    @exponential_backoff_retry(max_retries=3)
    def check_existing_slip(self, slip_id: str) -> Optional[int]:
        """Check if slip already exists in sheet, return row number if found"""
        try:
            # Read slip_id column (assuming it's column A)
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range='paper_slips!A:A'
            ).execute()
            
            values = result.get('values', [])
            for idx, row in enumerate(values):
                if row and row[0] == slip_id:
                    return idx + 1  # Sheets are 1-indexed
                    
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing slip: {e}")
            raise
    
    def fetch_live_lines(self, league: str = "NBA") -> List[Dict]:
        """Fetch live lines from PrizePicks"""
        try:
            logger.info(f"📡 Fetching live {league} lines from PrizePicks...")
            _, slips = self.prizepicks_client.fetch_current_board(league=league)
            logger.info(f"✅ Fetched {len(slips)} live lines")
            return slips
        except Exception as e:
            logger.error(f"Failed to fetch live lines: {e}")
            return []
    
    def merge_with_projections(self, live_lines: List[Dict]) -> List[Dict]:
        """Merge live lines with model projections"""
        try:
            # Generate projections from model
            today = datetime.date.today().isoformat()
            model_slips = generate_slips(start_date=today, end_date=today)
            
            # Create lookup map for live lines
            lines_map = {}
            for line in live_lines:
                key = f"{line['player']}|{line['prop_type']}"
                lines_map[key] = line
            
            # Merge data
            merged_slips = []
            for slip in model_slips:
                key = f"{slip.get('player', '')}|{slip.get('prop_type', '')}"
                
                # If we have live line data, use it
                if key in lines_map:
                    live_data = lines_map[key]
                    slip.update({
                        'line': live_data['line'],
                        'over_odds': live_data['over_odds'],
                        'under_odds': live_data['under_odds'],
                        'game_id': live_data['game_id'],
                        'projection_id': live_data.get('projection_id'),
                        'source': 'prizepicks_live'
                    })
                
                # Add metadata
                slip['slip_id'] = self.generate_slip_id(slip)
                slip['batch_id'] = self.batch_id
                slip['dry_run'] = self.dry_run
                slip['created_at'] = datetime.datetime.now().isoformat()
                slip['date'] = today  # Add date field
                
                # Calculate edge and make pick
                if 'projection' in slip and 'line' in slip:
                    edge = float(slip.get('projection', 0)) - float(slip.get('line', 0))
                    slip['edge'] = round(edge, 2)
                    slip['edge_pct'] = round((edge / slip['line'] * 100), 2) if slip['line'] else 0
                    
                    # Make pick based on edge threshold
                    if abs(edge) >= 0.5:  # Configurable threshold
                        slip['pick'] = 'OVER' if edge > 0 else 'UNDER'
                        slip['confidence'] = min(abs(slip['edge_pct']) / 10, 1.0)  # 0-1 scale
                    else:
                        slip['pick'] = 'PASS'
                        slip['confidence'] = 0
                
                merged_slips.append(slip)
            
            return merged_slips
            
        except Exception as e:
            logger.error(f"Error merging projections: {e}")
            return []
    
    @exponential_backoff_retry(max_retries=3)
    def push_to_sheets(self, slips: List[Dict]) -> Dict:
        """Push slips to Google Sheets with deduplication"""
        if not slips:
            logger.warning("No slips to push")
            return {"updated": 0, "skipped": 0}
        
        try:
            # Define column order
            columns = [
                'slip_id', 'batch_id', 'date', 'player', 'team', 'prop_type',
                'line', 'projection', 'edge', 'edge_pct', 'pick', 'confidence',
                'over_odds', 'under_odds', 'game_id', 'start_time',
                'dry_run', 'created_at', 'source', 'projection_id',
                'graded', 'result', 'graded_at', 'actual_value'
            ]
            
            # Check for existing slips
            new_slips = []
            skipped_count = 0
            
            for slip in slips:
                slip_id = slip.get('slip_id')
                existing_row = self.check_existing_slip(slip_id)
                
                if existing_row:
                    logger.info(f"Slip {slip_id} already exists at row {existing_row}, skipping")
                    skipped_count += 1
                else:
                    # Ensure slip has all columns
                    for col in columns:
                        if col not in slip:
                            slip[col] = ''
                    
                    new_slips.append(slip)
            
            if not new_slips:
                logger.info(f"All {len(slips)} slips already exist in sheet")
                return {"updated": 0, "skipped": skipped_count}
            
            # Convert to rows
            rows = []
            for slip in new_slips:
                row = [str(slip.get(col, '')) for col in columns]
                rows.append(row)
            
            # Push to sheet
            body = {'values': rows}
            
            result = self.sheet_service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='paper_slips!A1',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updated_cells = result.get('updates', {}).get('updatedCells', 0)
            updated_rows = len(new_slips)
            
            logger.info(f"✅ Pushed {updated_rows} new slips, skipped {skipped_count} existing")
            
            return {
                "updated": updated_rows,
                "skipped": skipped_count,
                "cells": updated_cells
            }
            
        except Exception as e:
            logger.error(f"Failed to push to sheets: {e}")
            raise
    
    def run(self, fetch_live: bool = True, league: str = "NBA") -> Dict:
        """Main execution flow"""
        try:
            logger.info("=" * 50)
            logger.info(f"🚀 PHASEGRID AUTO PAPER - Batch: {self.batch_id}")
            logger.info(f"📅 Date: {datetime.date.today()}")
            logger.info(f"🏀 League: {league}")
            logger.info(f"🔴 Dry Run: {self.dry_run}")
            logger.info("=" * 50)
            
            # Initialize services
            self.initialize_sheets()
            
            # Fetch live lines if requested
            live_lines = []
            if fetch_live:
                live_lines = self.fetch_live_lines(league)
            
            # Generate and merge slips
            slips = self.merge_with_projections(live_lines)
            logger.info(f"📋 Generated {len(slips)} total slips")
            
            # Push to sheets
            result = self.push_to_sheets(slips)
            
            # Summary
            logger.info("=" * 50)
            logger.info("📊 SUMMARY:")
            logger.info(f"  - Total slips: {len(slips)}")
            logger.info(f"  - New slips added: {result['updated']}")
            logger.info(f"  - Duplicate slips skipped: {result['skipped']}")
            logger.info(f"  - Batch ID: {self.batch_id}")
            logger.info("=" * 50)
            
            return {
                "batch_id": self.batch_id,
                "total_slips": len(slips),
                "new_slips": result['updated'],
                "skipped_slips": result['skipped'],
                "slips": slips
            }
            
        except Exception as e:
            logger.error(f"💥 Auto paper failed: {e}")
            raise


def main():
    """CLI entry point - backward compatible wrapper"""
    # Get sheet ID from environment
    sheet_id = os.environ.get('SHEET_ID')
    if not sheet_id:
        logger.error("Missing SHEET_ID environment variable")
        return
    
    # Create and run auto paper (always in dry-run mode for backward compatibility)
    auto_paper = EnhancedAutoPaper(sheet_id=sheet_id, dry_run=True)
    
    try:
        # Parse command line args if needed
        import argparse
        parser = argparse.ArgumentParser(description="PhaseGrid Auto Paper Generator")
        parser.add_argument("--fetch-lines", action="store_true", help="Fetch live lines from PrizePicks")
        parser.add_argument("--league", default="NBA", help="Sport league (NBA, NFL, etc.)")
        parser.add_argument("--production", action="store_true", help="Run in production mode (not dry-run)")
        
        # Try to parse args, but don't fail if none provided
        try:
            args = parser.parse_args()
            fetch_live = args.fetch_lines
            league = args.league
            dry_run = not args.production
        except:
            # Default values for backward compatibility
            fetch_live = False
            league = "NBA"
            dry_run = True
        
        # Update dry_run setting
        auto_paper.dry_run = dry_run
        
        # Run
        result = auto_paper.run(fetch_live=fetch_live, league=league)
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise


if __name__ == "__main__":
    main()