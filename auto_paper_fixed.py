#!/usr/bin/env python3
"""
Enhanced Auto Paper Script for PhaseGrid
Now with multi-day dry-run support, confidence scoring, and guard-rails
"""

import os
import sys
import uuid
import datetime
import json
import logging
import time
import argparse
import csv
import sqlite3
from typing import List, Dict, Optional, Tuple
from functools import wraps
from datetime import datetime as dt, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odds_provider.prizepicks import PrizePicksClient
from slips_generator import generate_slips
from alert_system import AlertManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Production hardened imports
from auth.sheets_auth import get_sheets_service
from api_clients.results_api import get_results_api_client


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


class StateManager:
    """Manages state persistence for multi-day runs"""
    
    def __init__(self, state_dir: str = "data/run_states"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
    
    def get_state_file(self, start_date: str, end_date: str) -> str:
        """Get versioned state file path"""
        return os.path.join(self.state_dir, f"dry_run_{start_date}_to_{end_date}.json")
    
    def load_state(self, start_date: str, end_date: str) -> Dict:
        """Load run state if exists"""
        state_file = self.get_state_file(start_date, end_date)
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                return json.load(f)
        return {
            "start_date": start_date,
            "end_date": end_date,
            "completed_dates": [],
            "last_run": None,
            "total_slips_generated": 0,
            "errors": []
        }
    
    def save_state(self, state: Dict, start_date: str, end_date: str):
        """Save current run state"""
        state_file = self.get_state_file(start_date, end_date)
        state["last_updated"] = dt.now(timezone.utc).isoformat()
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)


class EnhancedAutoPaper:
    """Enhanced auto paper generator with production features"""

    def __init__(self, sheet_id: str, dry_run: bool = True, timezone_override: str = None):
        self.sheet_id = sheet_id
        self.dry_run = dry_run
        self.sheet_service = None
        self.prizepicks_client = PrizePicksClient()
        self.batch_id = str(uuid.uuid4())
        self.alert_manager = AlertManager()
        self.state_manager = StateManager()
        
        # Timezone handling
        self.timezone = timezone.utc
        if timezone_override:
            import pytz
            self.timezone = pytz.timezone(timezone_override)
        
        # Database connection for metrics
        self.db_path = "data/paper_metrics.db"
        self._init_database()

    def _init_database(self):
        """Initialize database with new schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if columns exist before adding
        cursor.execute("PRAGMA table_info(paper_slips)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'confidence_score' not in existing_columns:
            cursor.execute("ALTER TABLE paper_slips ADD COLUMN confidence_score REAL")
            logger.info("Added confidence_score column to paper_slips table")
        
        if 'closing_line' not in existing_columns:
            cursor.execute("ALTER TABLE paper_slips ADD COLUMN closing_line TEXT")
            logger.info("Added closing_line column to paper_slips table")
            
        conn.commit()
        conn.close()

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
            logger.info("âœ… Google Sheets service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            raise

    def calculate_confidence_score(self, slip_data: Dict) -> float:
        """Calculate confidence score based on model variance and other factors"""
        base_confidence = slip_data.get('confidence', 0.5)
        
        # Factors that affect confidence
        factors = []
        
        # Edge factor
        if 'edge' in slip_data:
            edge = abs(slip_data['edge'])
            edge_factor = min(edge * 2, 1.0)  # Cap at 1.0
            factors.append(edge_factor)
        
        # Model agreement factor (if multiple models)
        if 'model_variance' in slip_data:
            variance_factor = 1.0 - min(slip_data['model_variance'], 0.5)
            factors.append(variance_factor)
        
        # Historical accuracy factor (if available)
        if 'historical_accuracy' in slip_data:
            factors.append(slip_data['historical_accuracy'])
        
        # Combine factors
        if factors:
            confidence_score = base_confidence * (sum(factors) / len(factors))
        else:
            confidence_score = base_confidence
            
        return round(confidence_score, 4)

    def get_closing_line(self, slip_data: Dict) -> str:
        """Get the final closing line for the prop"""
        # In a real implementation, this would fetch the actual closing line
        # For now, we'll use the line at generation time
        line = slip_data.get('line', 'N/A')
        prop_type = slip_data.get('prop_type', '')
        
        return f"{prop_type} {line}"

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

    def fetch_live_lines(self, league: str = "WNBA") -> List[Dict]:
        """Fetch live lines from PrizePicks"""
        try:
            logger.info(f"?? Fetching live {league} lines from PrizePicks...")
            projections = self.prizepicks_client.fetch_projections(league=league, include_live=False)  # Fixed to get all games
            
            # Convert to list format if needed
            if isinstance(projections, dict):
                projections = self.prizepicks_client.parse_projections_to_slips(projections)            
            # Convert to slip format
            slips = []
            for proj in projections:
                slip = {
                    'player': proj.get('player_name', ''),
                    'prop_type': proj.get('stat_type', ''),
                    'line': proj.get('line_score', 0),
                    'over_odds': proj.get('over_odds', -110),
                    'under_odds': proj.get('under_odds', -110),
                    'game_id': proj.get('game_id', ''),
                    'projection_id': proj.get('id', ''),
                    'start_time': proj.get('start_time', '')
                }
                slips.append(slip)
                
            logger.info(f"âœ… Fetched {len(slips)} live lines")
            return slips
        except Exception as e:
            logger.error(f"Failed to fetch live lines: {e}")
            return []

    def merge_with_projections(self, live_lines: List[Dict], date: str) -> List[Dict]:
        """Merge live lines with model projections"""
        try:
            # Generate projections from model
            model_slips = generate_slips(start_date=date, end_date=date)

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
                slip['date'] = date
                
                # Add new fields
                slip['confidence_score'] = self.calculate_confidence_score(slip)
                slip['closing_line'] = self.get_closing_line(slip)

                # Calculate edge and make pick
                if 'projection' in slip and 'line' in slip:
                    slip['edge'] = (slip['projection'] - slip['line']) / slip['line']
                    slip['pick'] = 'over' if slip['edge'] > 0 else 'under'
                    
                merged_slips.append(slip)

            return merged_slips

        except Exception as e:
            logger.error(f"Error merging projections: {e}")
            return []

    def save_slips_to_csv(self, slips: List[Dict], date: str):
        """Save slips to CSV with new fields"""
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = os.path.join(output_dir, f"paper_slips_{date.replace('-', '')}.csv")
        
        # Define all columns including new ones
        fieldnames = [
            'slip_id', 'type', 'legs', 'combined_odds', 'potential_multiplier',
            'total_stake', 'phase', 'confidence', 'potential_payout', 'dry_run',
            'date', 'game', 'player', 'prop_type', 'line', 'over_odds',
            'under_odds', 'projection', 'pick', 'decimal_odds', 'flex_payouts',
            'confidence_score', 'closing_line'  # New fields
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for slip in slips:
                # Ensure all fields exist
                row = {field: slip.get(field, '') for field in fieldnames}
                writer.writerow(row)
                
        logger.info(f"ðŸ’¾ Saved {len(slips)} slips to {filename}")
        return filename

    def save_to_database(self, slips: List[Dict]):
        """Save slips to database with new fields"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for slip in slips:
            # Insert with new fields
            cursor.execute("""
                INSERT OR REPLACE INTO paper_slips 
                (slip_id, date, player, prop_type, line, pick, confidence, 
                 confidence_score, closing_line, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                slip.get('slip_id'),
                slip.get('date'),
                slip.get('player'),
                slip.get('prop_type'),
                slip.get('line'),
                slip.get('pick'),
                slip.get('confidence'),
                slip.get('confidence_score'),
                slip.get('closing_line'),
                slip.get('created_at')
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"ðŸ’¾ Saved {len(slips)} slips to database")

    def emit_daily_metrics(self, date: str, slips: List[Dict]):
        """Emit daily metrics for monitoring"""
        metrics = {
            'date': date,
            'slip_count': len(slips),
            'average_confidence': sum(s.get('confidence_score', 0) for s in slips) / len(slips) if slips else 0,
            'high_confidence_count': sum(1 for s in slips if s.get('confidence_score', 0) > 0.7),
            'low_confidence_count': sum(1 for s in slips if s.get('confidence_score', 0) < 0.3),
            'timestamp': dt.now(timezone.utc).isoformat()
        }
        
        # Log metrics
        logger.info(f"ðŸ“Š Daily Metrics for {date}: {json.dumps(metrics, indent=2)}")
        
        # Save to metrics file
        metrics_file = f"logs/daily_metrics_{date.replace('-', '')}.json"
        os.makedirs("logs", exist_ok=True)
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
            
        return metrics

    def check_guard_rails(self, slips: List[Dict], date: str, min_slips: int = 5) -> bool:
        """Check if slip generation meets minimum requirements"""
        slip_count = len(slips)
        
        if slip_count < min_slips:
            # Trigger alert
            alert_message = (
                f"ðŸš¨ GUARD RAIL ALERT ðŸš¨\n"
                f"Date: {date}\n"
                f"Slips generated: {slip_count}\n"
                f"Minimum required: {min_slips}\n"
                f"Status: BELOW THRESHOLD"
            )
            
            logger.error(alert_message)
            
            # Send alerts via SMS and Discord
            self.alert_manager.send_critical_alert(alert_message)
            
            return False
        
        logger.info(f"âœ… Guard rail check passed: {slip_count} slips >= {min_slips} minimum")
        return True

    def run_single_day(self, date: str) -> Tuple[bool, int]:
        """Run paper generation for a single day"""
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"ðŸ—“ï¸  Processing date: {date}")
            logger.info(f"{'='*50}")
            
            # Ensure we're using UTC boundaries
            date_obj = dt.strptime(date, '%Y-%m-%d')
            date_obj = date_obj.replace(tzinfo=self.timezone)
            
            # Fetch live lines
            live_lines = self.fetch_live_lines()
            
            # Merge with projections
            slips = self.merge_with_projections(live_lines, date)
            
            if not slips:
                logger.warning(f"No slips generated for {date}")
                return False, 0
            
            # Save slips
            self.save_slips_to_csv(slips, date)
            self.save_to_database(slips)
            
            # Emit metrics
            self.emit_daily_metrics(date, slips)
            
            # Check guard rails
            guard_rail_passed = self.check_guard_rails(slips, date)
            
            return True, len(slips)
            
        except Exception as e:
            logger.error(f"Error processing date {date}: {e}")
            return False, 0

    def run_multi_day(self, start_date: str, end_date: str, resume: bool = True):
        """Run paper generation for multiple days"""
        # Load state if resuming
        state = self.state_manager.load_state(start_date, end_date) if resume else {
            "start_date": start_date,
            "end_date": end_date,
            "completed_dates": [],
            "last_run": None,
            "total_slips_generated": 0,
            "errors": []
        }
        
        # Generate date range
        start = dt.strptime(start_date, '%Y-%m-%d')
        end = dt.strptime(end_date, '%Y-%m-%d')
        
        current = start
        dates_to_process = []
        
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            if date_str not in state['completed_dates']:
                dates_to_process.append(date_str)
            current += timedelta(days=1)
        
        logger.info(f"ðŸ“… Multi-day run: {len(dates_to_process)} days to process")
        if state['completed_dates']:
            logger.info(f"âœ… Already completed: {len(state['completed_dates'])} days")
        
        # Process each date
        for date in dates_to_process:
            success, slip_count = self.run_single_day(date)
            
            if success:
                state['completed_dates'].append(date)
                state['total_slips_generated'] += slip_count
            else:
                state['errors'].append({
                    'date': date,
                    'error': 'Failed to generate slips',
                    'timestamp': dt.now(timezone.utc).isoformat()
                })
            
            # Save state after each day
            state['last_run'] = dt.now(timezone.utc).isoformat()
            self.state_manager.save_state(state, start_date, end_date)
            
            # Brief pause between days
            if date != dates_to_process[-1]:
                time.sleep(2)
        
        # Final summary
        logger.info(f"\n{'='*50}")
        logger.info(f"ðŸ Multi-day run complete!")
        logger.info(f"Total days processed: {len(state['completed_dates'])}")
        logger.info(f"Total slips generated: {state['total_slips_generated']}")
        if state['errors']:
            logger.warning(f"Errors encountered: {len(state['errors'])}")
        logger.info(f"{'='*50}")
        
        return state


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description='PhaseGrid Auto Paper Generator')
    parser.add_argument('--start-date', type=str, 
                       default=dt.now().strftime('%Y-%m-%d'),
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       default=dt.now().strftime('%Y-%m-%d'),
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--sheet-id', type=str,
                       default=os.getenv('GOOGLE_SHEET_ID'),
                       help='Google Sheet ID')
    parser.add_argument('--dry-run', action='store_true',
                       default=True,
                       help='Run in dry-run mode')
    parser.add_argument('--production', action='store_true',
                       help='Run in production mode (disables dry-run)')
    parser.add_argument('--timezone', type=str,
                       default=None,
                       help='Timezone override (e.g., America/New_York)')
    parser.add_argument('--min-slips', type=int,
                       default=5,
                       help='Minimum slips required per day')
    parser.add_argument('--bypass-guard-rail', action='store_true',
                       help='Bypass guard rail checks')
    parser.add_argument('--no-resume', action='store_true',
                       help='Do not resume from saved state')
    
    args = parser.parse_args()
    
    # Handle production mode
    if args.production:
        args.dry_run = False
    
    # Initialize paper generator
    generator = EnhancedAutoPaper(
        sheet_id=args.sheet_id,
        dry_run=args.dry_run,
        timezone_override=args.timezone
    )
    
    try:
        # Initialize services
        generator.initialize_sheets()
        
        # Check if multi-day run
        if args.start_date != args.end_date:
            # Multi-day run
            state = generator.run_multi_day(
                args.start_date,
                args.end_date,
                resume=not args.no_resume
            )
        else:
            # Single day run
            success, slip_count = generator.run_single_day(args.start_date)
            
            if not args.bypass_guard_rail and slip_count < args.min_slips:
                logger.error(f"Guard rail check failed: {slip_count} < {args.min_slips}")
                sys.exit(1)
        
        logger.info("âœ… Auto paper generation complete!")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
