"""Read paper_slips sheet content."""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_integration import get_sheets_service, SPREADSHEET_ID

def read_paper_slips():
    """Read and display current sheet content."""
    service = get_sheets_service()
    if not service:
        print("Failed to get sheets service")
        return
    
    try:
        # Read the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='paper_slips!A1:Z50'
        ).execute()
        
        values = result.get('values', [])
        print(f"Found {len(values)} rows")
        
        if not values:
            print("No data found in sheet")
            return
            
        # Show first 10 rows
        for i, row in enumerate(values[:10]):
            print(f"Row {i+1} ({len(row)} cols): {row[:5]}..." if len(row) > 5 else f"Row {i+1}: {row}")
            
    except Exception as e:
        print(f"Error reading sheet: {e}")

if __name__ == "__main__":
    read_paper_slips()
