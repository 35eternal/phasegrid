"""Setup paper_slips sheet with proper headers."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_integration import get_sheets_service, SPREADSHEET_ID

def setup_paper_slips():
    """Clear the sheet and add proper headers."""
    service = get_sheets_service()
    if not service:
        print("Failed to get sheets service")
        return False
    
    try:
        # First, clear the sheet
        clear_result = service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range='paper_slips!A:Z'
        ).execute()
        print("Cleared paper_slips sheet")
        
        # Add headers
        headers = [[
            'Date',           # A
            'Sport',          # B
            'Player',         # C
            'Market Type',    # D
            'Line',           # E
            'Pick',           # F
            'Odds',           # G
            'Risk Amount',    # H
            'Potential Payout', # I
            'Phase',          # J
            'Confidence',     # K
            'Slip UUID',      # L
            'Result',         # M
            'Profit/Loss',    # N
            'Notes'           # O
        ]]
        
        header_result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='paper_slips!A1:O1',
            valueInputOption='RAW',
            body={'values': headers}
        ).execute()
        print("Added headers to paper_slips sheet")
        
        # Format the header row
        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': 0,  # Assuming paper_slips is the first sheet
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.9,
                            'green': 0.9,
                            'blue': 0.9
                        },
                        'textFormat': {
                            'bold': True
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        }]
        
        format_result = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': requests}
        ).execute()
        print("Formatted header row")
        
        return True
        
    except Exception as e:
        print(f"Error setting up sheet: {e}")
        return False

if __name__ == "__main__":
    setup_paper_slips()
