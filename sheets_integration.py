"""Google Sheets integration module for pushing slips to paper_slips tab."""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import uuid

logger = logging.getLogger(__name__)

# Target spreadsheet ID from the project documentation
SPREADSHEET_ID = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
SHEET_NAME = "paper_slips"

class Slip:
    """Slip data structure for type hints."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def get_sheets_service():
    """Get authenticated Google Sheets service instance."""
    try:
        # First try CI environment variable
        google_sa_json = os.environ.get('GOOGLE_SA_JSON')
        
        if google_sa_json:
            logger.info("Using GOOGLE_SA_JSON from environment variable")
            # Decode base64 if needed
            try:
                import base64
                credentials_data = json.loads(base64.b64decode(google_sa_json))
            except:
                # If not base64, try direct JSON
                credentials_data = json.loads(google_sa_json)
        else:
            # Fall back to local file
            creds_path = os.path.join(os.path.dirname(__file__), 'credentials', 'service_account.json')
            if not os.path.exists(creds_path):
                # Try alternative path
                creds_path = 'service_account.json'
            
            if not os.path.exists(creds_path):
                logger.error("No credentials found. Set GOOGLE_SA_JSON env var or provide service_account.json")
                return None
                
            logger.info(f"Using credentials from file: {creds_path}")
            with open(creds_path, 'r') as f:
                credentials_data = json.load(f)
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            credentials_data,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Build service
        service = build('sheets', 'v4', credentials=credentials)
        logger.info("Successfully created Google Sheets service")
        return service
        
    except Exception as e:
        logger.error(f"Failed to create Google Sheets service: {e}")
        return None


def push_slips_to_sheets(slips: List[Any]) -> bool:
    """
    Push slips to Google Sheets paper_slips tab.
    Each bet within a slip gets its own row for detailed tracking.
    
    Args:
        slips: List of Slip objects to push to sheets
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not slips:
        logger.warning("No slips to push to Google Sheets")
        return True
    
    try:
        # Get authenticated service
        service = get_sheets_service()
        if not service:
            logger.error("Failed to get Google Sheets service")
            return False
        
        # Prepare data for sheets - one row per bet
        rows = []
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        for slip in slips:
            # Get slip attributes
            slip_type = getattr(slip, 'slip_type', '')
            slip_expected_value = getattr(slip, 'expected_value', 0)
            slip_total_odds = getattr(slip, 'total_odds', 0)
            slip_confidence = getattr(slip, 'confidence', 0)
            
            # Generate a unique slip ID to link bets together
            slip_uuid = str(uuid.uuid4())[:8]  # Short UUID for readability
            
            # Extract bets from the slip
            bets = getattr(slip, 'bets', ())
            
            # Create one row per bet
            for bet in bets:
                # Extract bet attributes
                player = getattr(bet, 'player', '')
                prop_type = getattr(bet, 'prop_type', '')
                line = getattr(bet, 'line', 0)
                over_under = getattr(bet, 'over_under', '')
                odds = getattr(bet, 'odds', -110)
                bet_confidence = getattr(bet, 'confidence', 0)
                game = getattr(bet, 'game', '')
                
                # Determine sport from player names or game info
                sport = 'NBA'  # Default
                if any(name in player for name in ["A'ja Wilson", "Breanna Stewart", "Diana Taurasi", "Sabrina Ionescu"]):
                    sport = 'WNBA'
                
                # Calculate individual bet risk and payout (assuming $10 standard bet)
                risk_amount = 10.0
                if odds < 0:  # American odds (negative)
                    potential_payout = risk_amount * (100 / abs(odds))
                else:  # American odds (positive)
                    potential_payout = risk_amount * (odds / 100)
                
                # Create row for this bet
                row = [
                    current_date,                    # A: date
                    sport,                           # B: sport
                    player,                          # C: player_name
                    prop_type,                       # D: market_type
                    str(line),                       # E: line
                    over_under.capitalize(),         # F: pick (Over/Under)
                    float(odds),                     # G: odds
                    float(risk_amount),              # H: risk_amount
                    float(risk_amount + potential_payout),  # I: potential_payout (total return)
                    '',                              # J: phase (empty for now)
                    float(bet_confidence),           # K: confidence_score
                    slip_uuid,                       # L: uuid (links bets in same slip)
                    '',                              # M: result (empty for new slips)
                    '',                              # N: profit_loss (empty for new slips)
                    f'{slip_type} slip | {game}'     # O: notes (slip type and game info)
                ]
                rows.append(row)
        
        if not rows:
            logger.warning("No bet rows to push to sheets")
            return True
            
        # Append rows to sheet
        body = {
            'values': rows
        }
        
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A2:O",
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        updates = result.get('updates', {})
        updated_rows = updates.get('updatedRows', 0)
        
        logger.info(f"[Sheets Integration] Successfully pushed {updated_rows} bet rows to Google Sheets")
        print(f"[Sheets Integration] Successfully pushed {updated_rows} bet rows to Google Sheets")
        
        return True
        
    except HttpError as e:
        logger.error(f"HTTP error pushing to sheets: {e}")
        print(f"[Sheets Integration] Failed to push slips: HTTP error {e}")
        return False
    except Exception as e:
        logger.error(f"Error pushing to sheets: {e}")
        print(f"[Sheets Integration] Failed to push slips: {e}")
        return False


def test_connection():
    """Test connection to Google Sheets."""
    try:
        service = get_sheets_service()
        if not service:
            return False
            
        # Try to get spreadsheet metadata
        result = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        title = result.get('properties', {}).get('title', 'Unknown')
        print(f"Successfully connected to spreadsheet: {title}")
        return True
        
    except Exception as e:
        print(f"Failed to connect to sheets: {e}")
        return False


if __name__ == "__main__":
    # Test the connection
    test_connection()
