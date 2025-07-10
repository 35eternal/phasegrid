"""Get sheet information including sheet IDs."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_integration import get_sheets_service, SPREADSHEET_ID

def get_sheet_info():
    """Get information about all sheets in the spreadsheet."""
    service = get_sheets_service()
    if not service:
        print("Failed to get sheets service")
        return
    
    try:
        # Get spreadsheet metadata
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        
        print(f"Spreadsheet: {spreadsheet['properties']['title']}")
        print("\nSheets:")
        
        for sheet in spreadsheet['sheets']:
            props = sheet['properties']
            print(f"  - {props['title']} (ID: {props['sheetId']})")
            
    except Exception as e:
        print(f"Error getting sheet info: {e}")

if __name__ == "__main__":
    get_sheet_info()
