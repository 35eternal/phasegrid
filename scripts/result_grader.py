#!/usr/bin/env python3
"""
Nightly grader for PhaseGrid dry-run automation.
Fetches yesterday's paper slips, retrieves actual game results,
compares them, and sends notifications.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import requests
from dotenv import load_dotenv
from twilio.rest import Client

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gsheet import get_sheet_service, append_to_sheet
from utils.alerts import send_alert

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants - USING YOUR EXISTING SECRET NAMES
SHEET_ID = os.getenv('SHEET_ID')  # Changed from GSHEET_ID to match your existing secrets
SHEET_NAME = 'paper_slips'
RESULTS_API_URL = os.getenv('RESULTS_API_URL', 'https://api.example.com/results')


class ResultGrader:
    """Grades paper slips against actual game results."""
    
    def __init__(self):
        self.sheet_service = None
        self.twilio_client = None
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
    def initialize(self):
        """Initialize services and connections."""
        try:
            # Initialize Google Sheets
            logger.info("Connecting to Google Sheets...")
            self.sheet_service = get_sheet_service()
            logger.info("✅ Connected to Google Sheets!")
            
            # Initialize Twilio
            account_sid = os.getenv('TWILIO_SID')
            auth_token = os.getenv('TWILIO_AUTH')
            if account_sid and auth_token:
                logger.info("Setting up text messaging...")
                self.twilio_client = Client(account_sid, auth_token)
                logger.info("✅ Text messaging ready!")
            else:
                logger.warning("⚠️ Twilio credentials not found. SMS notifications disabled.")
                
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            send_alert(f"ResultGrader initialization failed: {e}", severity="critical")
            raise
            
    def fetch_yesterdays_slips(self) -> List[Dict]:
        """Fetch yesterday's paper slips from Google Sheet."""
        try:
            logger.info(f"📋 Looking for slips from {self.yesterday}...")
            
            # Read all rows from the sheet
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,
                range=f'{SHEET_NAME}!A:H'
            ).execute()
            
            rows = result.get('values', [])
            if not rows:
                logger.warning("📭 No data found in sheet")
                return []
                
            # Parse rows (assuming header in first row)
            headers = rows[0]
            slips = []
            
            for row in rows[1:]:
                slip = dict(zip(headers, row))
                # Filter for yesterday's slips
                if slip.get('date') == self.yesterday:
                    slips.append(slip)
                    
            logger.info(f"📊 Found {len(slips)} slips for {self.yesterday}")
            return slips
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch slips: {e}")
            send_alert(f"Failed to fetch slips from Google Sheet: {e}", severity="high")
            raise
            
    def fetch_game_results(self, date: str) -> Dict:
        """Fetch actual game results for a given date."""
        try:
            logger.info(f"🏀 Fetching game results for {date} (using stub data)...")
            
            # STUB IMPLEMENTATION - Replace with real API call later
            # Example for real implementation:
            # response = requests.get(f"{RESULTS_API_URL}?date={date}")
            # return response.json()
            
            # Stub data for testing
            stub_results = {
                "LAL_vs_BOS": {"winner": "LAL", "score": "110-105"},
                "GSW_vs_NYK": {"winner": "GSW", "score": "120-115"},
                "MIA_vs_CHI": {"winner": "MIA", "score": "108-102"},
                "PHX_vs_DEN": {"winner": "PHX", "score": "118-114"},
                "DAL_vs_MIL": {"winner": "DAL", "score": "105-100"},
            }
            
            logger.info("✅ Got game results!")
            return stub_results
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch game results: {e}")
            send_alert(f"Failed to fetch game results: {e}", severity="high")
            raise
            
    def grade_slip(self, slip: Dict, results: Dict) -> Tuple[str, str]:
        """
        Grade a single slip against actual results.
        Returns: (grade, details)
        """
        try:
            game_key = slip.get('game_id', '')
            picked_winner = slip.get('pick', '')
            spread = float(slip.get('spread', 0))
            
            if game_key not in results:
                return 'ERROR', f"Game {game_key} not found in results"
                
            game_result = results[game_key]
            actual_winner = game_result.get('winner', '')
            score = game_result.get('score', '')
            
            # Simple win/loss logic (extend for spread calculations later)
            if picked_winner == actual_winner:
                return 'WIN', f"✅ Correct: {picked_winner} won ({score})"
            else:
                return 'LOSS', f"❌ Wrong: picked {picked_winner}, but {actual_winner} won ({score})"
                
        except Exception as e:
            logger.error(f"Error grading slip: {e}")
            return 'ERROR', str(e)
            
    def update_slip_grades(self, slips: List[Dict], grades: List[Tuple[str, str]]):
        """Update the Google Sheet with grading results."""
        try:
            logger.info("✍️ Writing grades to spreadsheet...")
            
            # Prepare batch update
            updates = []
            
            # For this example, we'll write to columns I and J
            # In production, you'd want to find the exact row for each slip
            for i, (slip, (grade, details)) in enumerate(zip(slips, grades)):
                # Starting from row 2 (assuming row 1 is headers)
                row_num = i + 2
                updates.append({
                    'range': f'{SHEET_NAME}!I{row_num}:J{row_num}',
                    'values': [[grade, details]]
                })
                
            if updates:
                body = {
                    'valueInputOption': 'RAW',
                    'data': updates
                }
                self.sheet_service.spreadsheets().values().batchUpdate(
                    spreadsheetId=SHEET_ID,
                    body=body
                ).execute()
                logger.info(f"✅ Updated {len(updates)} slip grades")
                
        except Exception as e:
            logger.error(f"❌ Failed to update grades: {e}")
            send_alert(f"Failed to update slip grades: {e}", severity="high")
            raise
            
    def send_summary_sms(self, total_slips: int, grades: List[Tuple[str, str]]):
        """Send SMS summary of grading results."""
        if not self.twilio_client:
            logger.warning("📵 Twilio client not initialized, skipping SMS")
            return
            
        try:
            # Count results
            wins = sum(1 for grade, _ in grades if grade == 'WIN')
            losses = sum(1 for grade, _ in grades if grade == 'LOSS')
            errors = sum(1 for grade, _ in grades if grade == 'ERROR')
            
            # Create message
            message_body = (
                f"🤖 PhaseGrid Nightly Grader\n"
                f"📅 Date: {self.yesterday}\n"
                f"📊 Total: {total_slips}\n"
                f"✅ Wins: {wins}\n"
                f"❌ Losses: {losses}\n"
                f"⚠️ Errors: {errors}\n"
            )
            
            if errors > 0:
                message_body += f"\n🚨 {errors} slips had errors!"
                
            # Send SMS
            from_phone = os.getenv('TWILIO_FROM')
            to_phone = os.getenv('PHONE_TO')
            
            logger.info(f"📱 Sending SMS from {from_phone} to {to_phone}...")
            
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=from_phone,
                to=to_phone
            )
            
            logger.info(f"✅ SMS sent! ID: {message.sid}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send SMS: {e}")
            send_alert(f"Failed to send summary SMS: {e}", severity="medium")
            
    def run(self):
        """Main execution flow."""
        try:
            logger.info("=" * 50)
            logger.info("🚀 PHASEGRID NIGHTLY GRADER")
            logger.info(f"📅 Grading slips from: {self.yesterday}")
            logger.info("=" * 50)
            
            # Initialize services
            self.initialize()
            
            # Fetch yesterday's slips
            slips = self.fetch_yesterdays_slips()
            if not slips:
                logger.info("😴 No slips to grade from yesterday")
                self.send_summary_sms(0, [])
                return
                
            # Fetch game results
            results = self.fetch_game_results(self.yesterday)
            
            # Grade each slip
            logger.info("📝 Grading slips...")
            grades = []
            for slip in slips:
                grade, details = self.grade_slip(slip, results)
                grades.append((grade, details))
                slip_id = slip.get('id', 'unknown')
                logger.info(f"  Slip {slip_id}: {grade}")
                
            # Update sheet with grades
            self.update_slip_grades(slips, grades)
            
            # Send summary notification
            self.send_summary_sms(len(slips), grades)
            
            # Check for critical issues
            error_count = sum(1 for grade, _ in grades if grade == 'ERROR')
            if error_count > 0:
                send_alert(
                    f"⚠️ Nightly grader completed with {error_count} errors",
                    severity="high"
                )
                
            logger.info("=" * 50)
            logger.info("🎉 Nightly grader completed successfully!")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"💥 Nightly grader failed: {e}")
            send_alert(f"🚨 Nightly grader critical failure: {e}", severity="critical")
            raise


if __name__ == "__main__":
    grader = ResultGrader()
    grader.run()