#!/usr/bin/env python3
"""
WHAT THIS FILE DOES:
This is our robot teacher that grades betting slips every night.
It checks if people's guesses about basketball games were right or wrong.
"""

# STEP 1: Import all the tools we need (like getting your pencils and erasers ready)
import os                          # Helps us read environment variables (secret passwords)
import sys                         # Helps us work with the system
import json                        # Helps us read data in JSON format
import logging                     # Helps us write down what's happening (like a diary)
from datetime import datetime, timedelta  # Helps us work with dates and time
from typing import List, Dict, Optional, Tuple  # Helps us define what kind of data we're using
import requests                    # Helps us talk to other websites
from dotenv import load_dotenv     # Helps us load secret passwords from .env file
from twilio.rest import Client     # Helps us send text messages

# STEP 2: Tell Python where to find our other helper files
# This is like telling someone "the bathroom is down the hall"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# STEP 3: Import our own helper functions
from utils.gsheet import get_sheet_service, append_to_sheet  # For talking to Google Sheets
from utils.alerts import send_alert                          # For sending emergency alerts

# STEP 4: Load all our secret passwords from the .env file
# This is like opening a locked box with all our passwords inside
load_dotenv()

# STEP 5: Set up our diary (logging) so we can see what's happening
logging.basicConfig(
    level=logging.INFO,  # We want to see all important messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # How to write each diary entry
)
logger = logging.getLogger(__name__)  # This is our diary writer

# STEP 6: Define important values we'll use everywhere
SHEET_ID = os.getenv('GSHEET_ID')  # The ID of our Google Sheet (like a home address)
SHEET_NAME = 'paper_slips'          # The name of the tab in our sheet
RESULTS_API_URL = os.getenv('RESULTS_API_URL', 'https://api.example.com/results')  # Where to get game results


class ResultGrader:
    """
    This is our robot teacher class. It knows how to:
    1. Get yesterday's guesses from Google Sheets
    2. Find out who really won the games
    3. Grade each guess
    4. Send text messages about the results
    """
    
    def __init__(self):
        """
        This runs when we create a new robot teacher.
        It's like the robot waking up and getting ready for work.
        """
        self.sheet_service = None    # We'll use this to talk to Google Sheets
        self.twilio_client = None    # We'll use this to send text messages
        # Figure out what yesterday's date was (we grade yesterday's guesses)
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
    def initialize(self):
        """
        This is where our robot teacher gets all its tools ready.
        Like a teacher setting up their desk before class.
        """
        try:
            # First, connect to Google Sheets (like logging into Google)
            logger.info("Connecting to Google Sheets...")
            self.sheet_service = get_sheet_service()
            logger.info("✅ Connected to Google Sheets!")
            
            # Next, set up text messaging (like turning on your phone)
            account_sid = os.getenv('TWILIO_SID')     # Your Twilio username
            auth_token = os.getenv('TWILIO_AUTH')     # Your Twilio password
            
            if account_sid and auth_token:
                logger.info("Setting up text messaging...")
                self.twilio_client = Client(account_sid, auth_token)
                logger.info("✅ Text messaging ready!")
            else:
                logger.warning("⚠️ No Twilio passwords found. Can't send texts!")
                
        except Exception as e:
            # If something goes wrong, tell everyone!
            logger.error(f"❌ Robot teacher couldn't get ready: {e}")
            send_alert(f"ResultGrader initialization failed: {e}", severity="critical")
            raise  # Stop everything - we can't continue
            
    def fetch_yesterdays_slips(self) -> List[Dict]:
        """
        This function gets all of yesterday's guesses from our Google Sheet.
        It's like opening the notebook and finding yesterday's homework.
        
        Returns: A list of all the guesses from yesterday
        """
        try:
            logger.info(f"📋 Looking for guesses from {self.yesterday}...")
            
            # Ask Google Sheets for all the data
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,      # Which spreadsheet to look at
                range=f'{SHEET_NAME}!A:H'    # Look at columns A through H
            ).execute()
            
            # Get all the rows of data
            rows = result.get('values', [])
            if not rows:
                logger.warning("📭 The sheet is empty!")
                return []
                
            # The first row has the column names (like "date", "team", etc.)
            headers = rows[0]
            yesterday_slips = []  # We'll put yesterday's guesses here
            
            # Look at each row (starting from row 2, because row 1 is headers)
            for row in rows[1:]:
                # Turn the row into a dictionary (like a labeled box)
                slip = dict(zip(headers, row))
                
                # Is this guess from yesterday?
                if slip.get('date') == self.yesterday:
                    yesterday_slips.append(slip)  # Yes! Save it
                    
            logger.info(f"📊 Found {len(yesterday_slips)} guesses from yesterday")
            return yesterday_slips
            
        except Exception as e:
            # Something went wrong! Tell everyone!
            logger.error(f"❌ Couldn't get yesterday's guesses: {e}")
            send_alert(f"Failed to fetch slips from Google Sheet: {e}", severity="high")
            raise
            
    def fetch_game_results(self, date: str) -> Dict:
        """
        This function finds out who actually won the games.
        It's like checking the sports news to see the real scores.
        
        Args:
            date: Which day's games to check (format: YYYY-MM-DD)
            
        Returns: A dictionary with all the game results
        """
        try:
            logger.info(f"🏀 Checking who won the games on {date}...")
            
            # NOTE: This is pretend data for now!
            # In real life, you would call a real sports API like this:
            # response = requests.get(f"{RESULTS_API_URL}?date={date}")
            # return response.json()
            
            # For now, we're pretending these are the results:
            fake_results = {
                "LAL_vs_BOS": {
                    "winner": "LAL",           # Lakers won
                    "score": "110-105"         # Final score
                },
                "GSW_vs_NYK": {
                    "winner": "GSW",           # Warriors won  
                    "score": "120-115"
                },
                "MIA_vs_CHI": {
                    "winner": "MIA",           # Heat won
                    "score": "108-102"
                }
            }
            
            logger.info("✅ Got the game results!")
            return fake_results
            
        except Exception as e:
            logger.error(f"❌ Couldn't get game results: {e}")
            send_alert(f"Failed to fetch game results: {e}", severity="high")
            raise
            
    def grade_slip(self, slip: Dict, results: Dict) -> Tuple[str, str]:
        """
        This grades one guess - was it right or wrong?
        It's like marking one question on a test.
        
        Args:
            slip: One person's guess
            results: The actual game results
            
        Returns: 
            - Grade (WIN/LOSS/ERROR)
            - Explanation of why
        """
        try:
            # Get the important info from the guess
            game_key = slip.get('game_id', '')      # Which game they guessed on
            picked_winner = slip.get('pick', '')     # Who they thought would win
            spread = float(slip.get('spread', 0))   # By how many points
            
            # Can we find this game in the results?
            if game_key not in results:
                return 'ERROR', f"❓ Can't find game {game_key} in the results"
                
            # Get what actually happened
            game_result = results[game_key]
            actual_winner = game_result.get('winner', '')
            score = game_result.get('score', '')
            
            # Check if they guessed right!
            if picked_winner == actual_winner:
                return 'WIN', f"✅ Correct! Picked {picked_winner} and they won ({score})"
            else:
                return 'LOSS', f"❌ Wrong! Picked {picked_winner} but {actual_winner} won ({score})"
                
        except Exception as e:
            logger.error(f"💥 Error grading slip: {e}")
            return 'ERROR', f"Something went wrong: {str(e)}"
            
    def update_slip_grades(self, slips: List[Dict], grades: List[Tuple[str, str]]):
        """
        This writes the grades back to the Google Sheet.
        It's like writing "A+" or "F" on each paper.
        
        Args:
            slips: All the guesses we graded
            grades: The grades for each guess
        """
        try:
            logger.info("✍️ Writing grades to the spreadsheet...")
            
            # We'll put all our updates here
            updates = []
            
            # For each slip and its grade...
            for i, (slip, (grade, details)) in enumerate(zip(slips, grades)):
                # For this example, we'll pretend we know which row to update
                # In real life, you'd search for the right row based on the slip ID
                row_num = i + 2  # Starting from row 2 (row 1 is headers)
                
                # Add this update to our list
                updates.append({
                    'range': f'{SHEET_NAME}!I{row_num}:J{row_num}',  # Columns I and J
                    'values': [[grade, details]]  # The grade and explanation
                })
                
            # Send all the updates to Google Sheets at once
            if updates:
                body = {
                    'valueInputOption': 'RAW',  # Write exactly what we say
                    'data': updates             # All our updates
                }
                self.sheet_service.spreadsheets().values().batchUpdate(
                    spreadsheetId=SHEET_ID,
                    body=body
                ).execute()
                logger.info(f"✅ Updated {len(updates)} grades in the sheet!")
                
        except Exception as e:
            logger.error(f"❌ Couldn't write grades to sheet: {e}")
            send_alert(f"Failed to update slip grades: {e}", severity="high")
            raise
            
    def send_summary_sms(self, total_slips: int, grades: List[Tuple[str, str]]):
        """
        This sends a text message with the results.
        It's like the teacher texting parents about how the class did.
        
        Args:
            total_slips: How many guesses we graded
            grades: All the grades we gave
        """
        if not self.twilio_client:
            logger.warning("📵 Can't send texts - Twilio not set up")
            return
            
        try:
            # Count how many of each grade we gave
            wins = sum(1 for grade, _ in grades if grade == 'WIN')
            losses = sum(1 for grade, _ in grades if grade == 'LOSS')
            errors = sum(1 for grade, _ in grades if grade == 'ERROR')
            
            # Create the text message
            message_body = (
                f"🤖 PhaseGrid Nightly Grader Summary\n"
                f"📅 Date: {self.yesterday}\n"
                f"📊 Total Slips: {total_slips}\n"
                f"✅ Wins: {wins}\n"
                f"❌ Losses: {losses}\n"
                f"⚠️ Errors: {errors}\n"
            )
            
            # Add a warning if there were errors
            if errors > 0:
                message_body += f"\n🚨 WARNING: {errors} slips had grading errors!"
                
            # Get phone numbers from environment
            from_phone = os.getenv('TWILIO_FROM')  # Our phone number
            to_phone = os.getenv('PHONE_TO')        # Who to text
            
            logger.info(f"📱 Sending SMS from {from_phone} to {to_phone}...")
            
            # Send the text!
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=from_phone,
                to=to_phone
            )
            
            logger.info(f"✅ Text sent! Message ID: {message.sid}")
            
        except Exception as e:
            logger.error(f"❌ Couldn't send text message: {e}")
            send_alert(f"Failed to send summary SMS: {e}", severity="medium")
            
    def run(self):
        """
        This is the main function that runs everything in order.
        It's like the teacher's lesson plan for the day.
        """
        try:
            logger.info("🚀 Starting the nightly grader...")
            logger.info(f"📅 Grading slips from: {self.yesterday}")
            
            # Step 1: Get ready
            self.initialize()
            
            # Step 2: Get yesterday's guesses
            slips = self.fetch_yesterdays_slips()
            if not slips:
                logger.info("😴 No slips to grade from yesterday. Going back to sleep!")
                self.send_summary_sms(0, [])  # Still send a text saying "nothing to grade"
                return
                
            # Step 3: Get the real game results
            results = self.fetch_game_results(self.yesterday)
            
            # Step 4: Grade each guess
            logger.info("📝 Starting to grade slips...")
            grades = []
            for slip in slips:
                grade, details = self.grade_slip(slip, results)
                grades.append((grade, details))
                logger.info(f"Graded slip {slip.get('id', '???')}: {grade}")
                
            # Step 5: Write grades back to the sheet
            self.update_slip_grades(slips, grades)
            
            # Step 6: Send summary text message
            self.send_summary_sms(len(slips), grades)
            
            # Step 7: Check if anything went wrong
            error_count = sum(1 for grade, _ in grades if grade == 'ERROR')
            if error_count > 0:
                send_alert(
                    f"⚠️ Nightly grader finished but had {error_count} errors",
                    severity="high"
                )
                
            logger.info("🎉 Nightly grader finished successfully!")
            
        except Exception as e:
            # If anything goes wrong, scream for help!
            logger.error(f"💥 CRITICAL ERROR: Nightly grader crashed: {e}")
            send_alert(f"🚨 Nightly grader FAILED COMPLETELY: {e}", severity="critical")
            raise


# This part runs when someone executes this file directly
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("PHASEGRID NIGHTLY GRADER")
    logger.info("=" * 50)
    
    # Create our robot teacher and tell it to start working
    grader = ResultGrader()
    grader.run()