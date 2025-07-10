"""Format paper_slips sheet for better visibility."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_integration import get_sheets_service, SPREADSHEET_ID

def format_paper_slips(sheet_id):
    """Format the paper_slips sheet."""
    service = get_sheets_service()
    if not service:
        print("Failed to get sheets service")
        return False
    
    try:
        requests = [
            # Format header row
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.2,
                                'green': 0.4,
                                'blue': 0.8
                            },
                            'textFormat': {
                                'foregroundColor': {
                                    'red': 1.0,
                                    'green': 1.0,
                                    'blue': 1.0
                                },
                                'bold': True
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                }
            },
            # Freeze header row
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': sheet_id,
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            },
            # Auto-resize columns
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 15
                    }
                }
            },
            # Add alternating row colors
            {
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [{
                            'sheetId': sheet_id,
                            'startRowIndex': 1,
                            'endRowIndex': 1000
                        }],
                        'booleanRule': {
                            'condition': {
                                'type': 'CUSTOM_FORMULA',
                                'values': [{
                                    'userEnteredValue': '=MOD(ROW(),2)=0'
                                }]
                            },
                            'format': {
                                'backgroundColor': {
                                    'red': 0.95,
                                    'green': 0.95,
                                    'blue': 0.95
                                }
                            }
                        }
                    }
                }
            }
        ]
        
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': requests}
        ).execute()
        
        print("Successfully formatted paper_slips sheet")
        return True
        
    except Exception as e:
        print(f"Error formatting sheet: {e}")
        return False

if __name__ == "__main__":
    # You'll need to replace this with the actual sheet ID from get_sheet_info.py
    sheet_id = 2026932525  # Default, update after running get_sheet_info.py
    format_paper_slips(sheet_id)
