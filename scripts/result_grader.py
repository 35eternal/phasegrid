#!/usr/bin/env python3
"""
Enhanced Result Grader for PhaseGrid
Grades slips by slip_id with retry logic and production API integration
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from functools import wraps
import requests
from dotenv import load_dotenv
from twilio.rest import Client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InsufficientSlipsError(Exception):
    """Raised when there are not enough slips to grade"""
    pass



def exponential_backoff_retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for exponential backoff with jitter"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (HttpError, requests.RequestException, Exception) as e:
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


class EnhancedResultGrader:
    """Production-ready result grader with slip ID updates"""
    
    def __init__(self, date: Optional[str] = None):
        self.sheet_service = None
        self.twilio_client = None
        self.sheet_id = os.getenv('SHEET_ID')
        self.sheet_name = 'paper_slips'
        self.grade_date = date or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # API endpoints
        self.results_api_url = os.getenv('RESULTS_API_URL', 'https://api.example.com/results')
        self.results_api_key = os.getenv('RESULTS_API_KEY')
        
        # Retry configuration
        self.max_retries = int(os.getenv('RETRY_MAX', '3'))
        
    def initialize(self):
        """Initialize services and connections"""
        try:
            # Initialize Google Sheets
            logger.info("Connecting to Google Sheets...")
            self.sheet_service = self._get_sheet_service()
            logger.info("âœ… Connected to Google Sheets!")
            
            # Initialize Twilio with local 10DLC number
            self._initialize_twilio()
            
        except Exception as e:
            logger.error(f"âŒ Initialization failed: {e}")
            self._send_alert(f"ResultGrader initialization failed: {e}", severity="critical")
            raise
    
    def _get_sheet_service(self):
        """Create and return Google Sheets service"""
        try:
            creds_json = os.getenv('GOOGLE_SA_JSON')
            if not creds_json:
                raise ValueError("GOOGLE_SA_JSON environment variable not set")
            
            # Parse credentials
            if os.path.exists(creds_json):
                credentials = service_account.Credentials.from_service_account_file(
                    creds_json,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                creds_dict = json.loads(creds_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            
            return build('sheets', 'v4', credentials=credentials)
            
        except Exception as e:
            logger.error(f"Failed to create Google Sheets service: {e}")
            raise
    
    def _initialize_twilio(self):
        """Initialize Twilio with local 10DLC number"""
        try:
            account_sid = os.getenv('TWILIO_SID')
            auth_token = os.getenv('TWILIO_AUTH')
            
            if account_sid and auth_token:
                logger.info("Setting up Twilio messaging...")
                self.twilio_client = Client(account_sid, auth_token)
                
                # Verify the local 10DLC number
                from_number = os.getenv('TWILIO_FROM')
                if from_number and not from_number.startswith('+1'):
                    from_number = f'+1{from_number}'  # Ensure US format
                
                # Test the number by fetching its details
                try:
                    phone_number = self.twilio_client.incoming_phone_numbers.list(
                        phone_number=from_number
                    )[0]
                    logger.info(f"âœ… Verified Twilio 10DLC number: {phone_number.phone_number}")
                    logger.info(f"   - Friendly name: {phone_number.friendly_name}")
                    logger.info(f"   - SMS capable: {phone_number.capabilities.sms}")
                except Exception as e:
                    logger.warning(f"Could not verify Twilio number: {e}")
                    
            else:
                logger.warning("âš ï¸ Twilio credentials not found. SMS notifications disabled.")
                
        except Exception as e:
            logger.error(f"Twilio initialization error: {e}")
            self.twilio_client = None
    
    def _send_alert(self, message: str, severity: str = "info"):
        """Send alert to Discord webhook"""
        try:
            webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
            if not webhook_url or webhook_url == 'https://discord.com/api/webhooks/placeholder':
                logger.warning(f"Discord webhook not configured. Alert: {message}")
                return
            
            emoji = {
                "critical": "ðŸš¨",
                "high": "âš ï¸",
                "medium": "ðŸ“¢",
                "info": "â„¹ï¸"
            }.get(severity, "ðŸ“Œ")
            
            payload = {
                "content": f"{emoji} **PhaseGrid Alert** ({severity.upper()})\n{message}"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code != 204:
                logger.error(f"Failed to send Discord alert: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    @exponential_backoff_retry(max_retries=3)
    def fetch_slips_for_date(self, date: str) -> List[Dict]:
        """Fetch slips for a specific date from Google Sheet"""
        try:
            logger.info(f"ðŸ“‹ Fetching slips for date: {date}")
            
            # Get all data from sheet
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f'{self.sheet_name}!A:Z'  # Get all columns
            ).execute()
            
            rows = result.get('values', [])
            if not rows:
                logger.warning("ðŸ“­ No data found in sheet")
                return []
            
            # Parse header row
            headers = rows[0]
            slips = []
            
            # Find column indices
            slip_id_idx = headers.index('slip_id') if 'slip_id' in headers else -1
            date_idx = headers.index('date') if 'date' in headers else -1
            graded_idx = headers.index('graded') if 'graded' in headers else -1
            
            if slip_id_idx == -1:
                logger.warning("slip_id column not found - using old format")
                # Fallback for old format without slip_id
                slip_id_idx = headers.index('id') if 'id' in headers else 0
            
            # Process rows
            for row_idx, row in enumerate(rows[1:], start=2):  # Start from row 2 (1-indexed)
                # Pad row to match headers length
                while len(row) < len(headers):
                    row.append('')
                    
                slip = dict(zip(headers, row))
                slip['_row_number'] = row_idx  # Store row number for updates
                
                # Filter by date and ungraded status
                if (date_idx != -1 and slip.get('date') == date and 
                    (graded_idx == -1 or slip.get('graded') != 'TRUE')):
                    slips.append(slip)
                    
            logger.info(f"ðŸ“Š Found {len(slips)} ungraded slips for {date}")
            return slips
            
        except Exception as e:
            logger.error(f"âŒ Failed to fetch slips: {e}")
            self._send_alert(f"Failed to fetch slips from Google Sheet: {e}", severity="high")
            return []  # Return empty list instead of raising
    
    @exponential_backoff_retry(max_retries=3)
    def fetch_game_results(self, date: str) -> Dict:
        """Fetch actual game results from production API"""
        try:
            logger.info(f"ðŸ€ Fetching game results for {date}")
            
            # Production API call
            if self.results_api_key and self.results_api_url != 'https://api.example.com/results':
                headers = {
                    'Authorization': f'Bearer {self.results_api_key}',
                    'Accept': 'application/json'
                }
                
                params = {
                    'date': date,
                    'include_props': True  # Include player prop results
                }
                
                response = requests.get(
                    self.results_api_url,
                    headers=headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                results = response.json()
                logger.info(f"âœ… Fetched results for {len(results.get('games', []))} games")
                return self._normalize_results(results)
            
            else:
                # Fallback to stub data for testing
                logger.warning("âš ï¸ Using stub data - configure RESULTS_API_URL and RESULTS_API_KEY for production")
                return self._get_stub_results(date)
                
        except Exception as e:
            logger.error(f"âŒ Failed to fetch game results: {e}")
            self._send_alert(f"Failed to fetch game results: {e}", severity="high")
            return {}
    
    def _normalize_results(self, api_results: Dict) -> Dict:
        """Normalize API results to standard format"""
        normalized = {}
        
        # Process game results
        for game in api_results.get('games', []):
            game_id = game.get('game_id')
            normalized[game_id] = {
                'winner': game.get('winner'),
                'score': game.get('final_score'),
                'home_score': game.get('home_score'),
                'away_score': game.get('away_score')
            }
        
        # Process player props
        for prop in api_results.get('player_props', []):
            player_key = f"{prop['player']}_{prop['prop_type']}"
            normalized[player_key] = {
                'actual_value': prop.get('actual_value'),
                'prop_type': prop.get('prop_type'),
                'player': prop.get('player')
            }
        
        return normalized
    
    def _get_stub_results(self, date: str) -> Dict:
        """Get stub results for testing"""
        return {
            "LAL_vs_BOS": {"winner": "LAL", "score": "110-105"},
            "GSW_vs_NYK": {"winner": "GSW", "score": "120-115"},
            "LeBron James_Points": {"actual_value": 28.0, "prop_type": "Points"},
            "Stephen Curry_Three Pointers Made": {"actual_value": 5.0, "prop_type": "Three Pointers Made"}
        }
    
    def grade_slip(self, slip: Dict, results: Dict) -> Tuple[str, str, Dict]:
        """Grade a single slip against actual results"""
        try:
            slip_id = slip.get('slip_id', slip.get('id', 'unknown'))
            prop_type = slip.get('prop_type', '')
            player = slip.get('player', '')
            pick = slip.get('pick', '')
            line = float(slip.get('line', 0))
            
            # Look up result
            if prop_type and player:
                # Player prop bet
                result_key = f"{player}_{prop_type}"
                if result_key in results:
                    actual = results[result_key].get('actual_value', 0)
                    
                    if pick == 'OVER':
                        is_win = actual > line
                    elif pick == 'UNDER':
                        is_win = actual < line
                    else:
                        return 'PASS', 'No pick made', {}
                    
                    grade = 'WIN' if is_win else 'LOSS'
                    details = f"{player} {prop_type}: {actual} vs {line} ({pick})"
                    
                    return grade, details, {
                        'actual_value': actual,
                        'line': line,
                        'pick': pick
                    }
            
            # Game result
            game_id = slip.get('game_id', '')
            if game_id and game_id in results:
                game_result = results[game_id]
                # Add game grading logic here
                return 'PENDING', 'Game grading not implemented', {}
            
            return 'ERROR', f"No result found for slip {slip_id}", {}
            
        except Exception as e:
            logger.error(f"Error grading slip {slip.get('slip_id', 'unknown')}: {e}")
            return 'ERROR', str(e), {}
    
    @exponential_backoff_retry(max_retries=3)
    def update_slip_by_id(self, slip: Dict, grade: str, details: str, metadata: Dict):
        """Update a specific slip row by slip_id"""
        try:
            slip_id = slip.get('slip_id', slip.get('id'))
            row_number = slip.get('_row_number')
            
            if not row_number:
                logger.error(f"Missing row_number for slip {slip_id}")
                return
            
            # Get column indices from header
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=f'{self.sheet_name}!1:1'
            ).execute()
            
            headers = result.get('values', [[]])[0]
            
            # Find columns to update
            updates = []
            
            # Update graded column
            if 'graded' in headers:
                col = chr(65 + headers.index('graded'))  # Convert to column letter
                updates.append({
                    'range': f'{self.sheet_name}!{col}{row_number}',
                    'values': [['TRUE']]
                })
            
            # Update result column
            if 'result' in headers:
                col = chr(65 + headers.index('result'))
                updates.append({
                    'range': f'{self.sheet_name}!{col}{row_number}',
                    'values': [[grade]]
                })
            
            # Update graded_at column
            if 'graded_at' in headers:
                col = chr(65 + headers.index('graded_at'))
                updates.append({
                    'range': f'{self.sheet_name}!{col}{row_number}',
                    'values': [[datetime.now().isoformat()]]
                })
            
            # Update actual_value if available
            if 'actual_value' in headers and 'actual_value' in metadata:
                col = chr(65 + headers.index('actual_value'))
                updates.append({
                    'range': f'{self.sheet_name}!{col}{row_number}',
                    'values': [[str(metadata['actual_value'])]]
                })
            
            # Batch update
            if updates:
                body = {
                    'valueInputOption': 'USER_ENTERED',
                    'data': updates
                }
                
                result = self.sheet_service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body=body
                ).execute()
                
                logger.info(f"âœ… Updated slip {slip_id} (row {row_number}): {grade}")
            
        except Exception as e:
            logger.error(f"âŒ Failed to update slip {slip.get('slip_id', 'unknown')}: {e}")
            raise
    
    def send_summary_sms(self, total_slips: int, grades: List[Tuple[str, str, Dict]]):
        """Send SMS summary using verified 10DLC number"""
        if not self.twilio_client:
            logger.warning("ðŸ“µ Twilio client not initialized, skipping SMS")
            return
        
        try:
            # Count results
            results_summary = {
                'WIN': sum(1 for g, _, _ in grades if g == 'WIN'),
                'LOSS': sum(1 for g, _, _ in grades if g == 'LOSS'),
                'ERROR': sum(1 for g, _, _ in grades if g == 'ERROR'),
                'PENDING': sum(1 for g, _, _ in grades if g == 'PENDING')
            }
            
            win_rate = (results_summary['WIN'] / (results_summary['WIN'] + results_summary['LOSS']) * 100 
                       if results_summary['WIN'] + results_summary['LOSS'] > 0 else 0)
            
            # Create message
            message_body = (
                f"ðŸ¤– PhaseGrid Results\n"
                f"ðŸ“… {self.grade_date}\n"
                f"ðŸ“Š Total: {total_slips}\n"
                f"âœ… Wins: {results_summary['WIN']}\n"
                f"âŒ Losses: {results_summary['LOSS']}\n"
                f"ðŸ“ˆ Win Rate: {win_rate:.1f}%\n"
            )
            
            if results_summary['ERROR'] > 0:
                message_body += f"âš ï¸ Errors: {results_summary['ERROR']}\n"
            
            if results_summary['PENDING'] > 0:
                message_body += f"â³ Pending: {results_summary['PENDING']}\n"
            
            # Send SMS
            from_phone = os.getenv('TWILIO_FROM')
            to_phone = os.getenv('PHONE_TO')
            
            # Ensure proper phone number format
            if not from_phone.startswith('+'):
                from_phone = f'+1{from_phone}'
            if not to_phone.startswith('+'):
                to_phone = f'+1{to_phone}'
            
            logger.info(f"ðŸ“± Sending SMS from {from_phone} to {to_phone}")
            
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=from_phone,
                to=to_phone
            )
            
            logger.info(f"âœ… SMS sent! ID: {message.sid}")
            
        except Exception as e:
            logger.error(f"âŒ Failed to send SMS: {e}")
            self._send_alert(f"Failed to send summary SMS: {e}", severity="medium")
    
    def run(self):
        """Main execution flow"""
        try:
            logger.info("=" * 50)
            logger.info("ðŸš€ PHASEGRID RESULT GRADER")
            logger.info(f"ðŸ“… Grading slips from: {self.grade_date}")
            logger.info("=" * 50)
            
            # Initialize services
            self.initialize()
            
            # Fetch slips to grade
            slips = self.fetch_slips_for_date(self.grade_date)
            if not slips:
                logger.info("ðŸ˜´ No ungraded slips found")
                self.send_summary_sms(0, [])
                return
            
            # Fetch game results
            results = self.fetch_game_results(self.grade_date)
            
            # Grade each slip
            logger.info(f"ðŸ“ Grading {len(slips)} slips...")
            grades = []
            
            for slip in slips:
                slip_id = slip.get('slip_id', slip.get('id', 'unknown'))
                grade, details, metadata = self.grade_slip(slip, results)
                grades.append((grade, details, metadata))
                
                # Update slip in sheet
                self.update_slip_by_id(slip, grade, details, metadata)
                
                logger.info(f"  Slip {slip_id}: {grade} - {details}")
            
            # Send summary notification
            self.send_summary_sms(len(slips), grades)
            
            # Check for issues
            error_count = sum(1 for grade, _, _ in grades if grade == 'ERROR')
            if error_count > 0:
                self._send_alert(
                    f"âš ï¸ Result grader completed with {error_count} errors",
                    severity="high"
                )
            
            logger.info("=" * 50)
            logger.info("ðŸŽ‰ Result grader completed successfully!")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"ðŸ’¥ Result grader failed: {e}")
            self._send_alert(f"ðŸš¨ Result grader critical failure: {e}", severity="critical")
            # Don't raise - let it complete gracefully


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PhaseGrid Result Grader")
    parser.add_argument("--date", help="Date to grade (YYYY-MM-DD), defaults to yesterday")
    args = parser.parse_args()
    
    grader = EnhancedResultGrader(date=args.date)
    grader.run()


if __name__ == "__main__":
    main()
